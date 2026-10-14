"""Six-node LangGraph support agent using deterministic local behavior."""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from nykaa_support.dataset import check_order_status

ROOT = Path(__file__).resolve().parents[2]
ORDERS_FILE = ROOT / "data" / "orders.csv"
DB_DIR = ROOT / "data" / "chroma"
MEMORY_DIR = ROOT / "data" / "memory"
CHECKPOINT_FILE = ROOT / "data" / "checkpoints" / "checkpoints.sqlite"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.465


class ChatRequest(BaseModel):
    """Validated user input."""

    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Validated response returned by the agent."""

    session_id: str
    answer: str
    route: Literal["knowledge", "order", "escalation", "blocked", "scope"]
    escalation_score: int = Field(ge=0, le=100)
    escalation_required: bool
    sources: list[str]
    tools_called: list[str]


class AgentState(TypedDict, total=False):
    session_id: str
    message: str
    safe_message: str
    injection_detected: bool
    scope_block: bool
    route: str
    order_id: str | None
    order_result: dict | None
    evidence: list[dict]
    sources: list[str]
    tools_called: list[str]
    history: list[dict]
    answer: str
    escalation_score: int
    escalation_required: bool
    response: dict


def mask_pii(text: str) -> str:
    """Mask email addresses, Indian mobile numbers, and card last-four values."""
    text = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED_EMAIL]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)",
        "[REDACTED_PHONE]",
        text,
    )
    return re.sub(
        r"(?i)\b(?:card(?:\s*(?:number|no\.?|ending|last\s*4|last\s*four))?|last\s*4(?:\s*of\s*(?:the\s*)?card)?)\s*(?:ending\s*(?:in\s*)?|is\s*|[:#-]\s*)?(\d{4})\b",
        "[REDACTED_CARD_LAST4]",
        text,
    )


def contains_injection(text: str) -> bool:
    patterns = (
        r"ignore (all )?(previous|earlier) instructions",
        r"reveal (the )?(system|developer) prompt",
        r"bypass (the )?guardrails",
        r"disregard (all )?(rules|instructions)",
    )
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def asks_for_official_policy(text: str) -> bool:
    normalized = text.lower()
    official_request = "official" in normalized or (
        "current" in normalized and "nykaa" in normalized
    )
    policy_topic = any(
        word in normalized for word in ("policy", "return", "refund", "delivery")
    )
    return official_request and policy_topic


def memory_file(session_id: str) -> Path:
    return MEMORY_DIR / f"{session_id}.json"


def load_memory(session_id: str) -> list[dict]:
    path = memory_file(session_id)
    if not path.exists():
        return []
    saved = json.loads(path.read_text(encoding="utf-8-sig"))
    return saved.get("turns", [])[-20:]


@lru_cache(maxsize=1)
def embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def retrieve_policy(question: str) -> list[dict]:
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(name="nykaa_kb_sentence_chunks")
    vector = embedding_model().encode(
        [question], normalize_embeddings=True
    )[0].tolist()
    result = collection.query(
        query_embeddings=[vector],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    evidence = []
    for text, details, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        score = 1.0 - distance
        if score >= SIMILARITY_THRESHOLD:
            evidence.append(
                {"text": text, "source": details["source"], "score": score}
            )
    return evidence


def input_guard(state: AgentState) -> dict:
    raw_message = state["message"]
    return {
        "safe_message": mask_pii(raw_message),
        "injection_detected": contains_injection(raw_message),
        "scope_block": asks_for_official_policy(raw_message),
        "history": load_memory(state["session_id"]),
        "tools_called": [],
        "order_id": None,
        "order_result": {},
        "evidence": [],
        "sources": [],
        "answer": "",
        "escalation_score": 0,
        "escalation_required": False,
        "response": {},
    }

def request_router(state: AgentState) -> dict:
    message = state["safe_message"]
    order_match = re.search(r"\bNK\d{6}\b", message, flags=re.IGNORECASE)
    lower = message.lower()

    if state.get("injection_detected"):
        route = "blocked"
    elif state.get("scope_block"):
        route = "scope"
    elif order_match:
        route = "order"
    elif any(term in lower for term in (
        "damaged", "missing item", "payment dispute", "fraud",
        "allergic", "injury", "unsafe", "complaint", "wrong item",
    )):
        route = "escalation"
    else:
        # Only a concrete sample order ID triggers order lookup.
        route = "knowledge"

    return {
        "route": route,
        "order_id": order_match.group(0).upper() if order_match else None,
    }


def deterministic_tools(state: AgentState) -> dict:
    route = state["route"]
    tools_called = list(state.get("tools_called", []))

    if route == "order":
        tools_called.append("order_lookup")
        order_id = state.get("order_id")
        if not order_id:
            return {
                "order_result": {"kind": "missing_id"},
                "tools_called": tools_called,
            }

        order = check_order_status(order_id)
        if not order.get("found"):
            result = {"kind": "not_found", "order_id": order_id}
        else:
            result = {"kind": "found", "order_id": order_id, **order}
        return {"order_result": result, "tools_called": tools_called}
    if route == "knowledge":
        tools_called.append("policy_search")
        history = state.get("history", [])
        previous_question = next(
            (
                turn.get("content", "")
                for turn in reversed(history)
                if turn.get("role") == "user"
            ),
            "",
        )
        retrieval_query = f"{previous_question} {state['safe_message']}".strip()
        evidence = retrieve_policy(retrieval_query)
        return {
            "evidence": evidence,
            "sources": [item["source"] for item in evidence],
            "tools_called": tools_called,
        }

    if route == "escalation":
        tools_called.append("human_escalation_router")
        tools_called.append("policy_search")
        history = state.get("history", [])
        previous_question = next(
            (
                turn.get("content", "")
                for turn in reversed(history)
                if turn.get("role") == "user"
            ),
            "",
        )
        retrieval_query = f"{previous_question} {state['safe_message']}".strip()
        evidence = retrieve_policy(retrieval_query)
        return {
            "evidence": evidence,
            "sources": [item["source"] for item in evidence],
            "tools_called": tools_called,
        }

    return {"tools_called": tools_called}


def escalation_score(state: AgentState) -> dict:
    message = state.get("safe_message", "").lower()
    urgent_terms = ("fraud", "payment dispute", "injury", "allergic", "unsafe")
    escalation_terms = (
        "damaged", "missing item", "complaint", "wrong item",
        "cancel",
    )

    order_result = state.get("order_result") or {}
    if order_result.get("kind") == "found":
        score = round(float(order_result["escalation_score"]) * 100)
        return {
            "escalation_score": score,
            "escalation_required": bool(order_result["escalation_required"]),
        }
    if any(term in message for term in urgent_terms):
        score = 95
    elif state.get("route") == "escalation" or any(
        term in message for term in escalation_terms
    ):
        score = 80
    elif state.get("order_result", {}).get("kind") == "not_found":
        score = 45
    elif state.get("route") == "knowledge" and not state.get("evidence"):
        score = 45
    else:
        score = 0

    return {"escalation_score": score, "escalation_required": score >= 70}


def mock_llm_response(state: AgentState) -> dict:
    """Deterministic MOCK_LLM: templates and retrieved evidence only."""
    route = state["route"]

    if route == "blocked":
        answer = "I can help with order or demo-policy questions, but not that request."
    elif route == "scope":
        answer = (
            "This project contains fictional demo rules, not official or current "
            "Nykaa policies. Please ask an authorized support operator."
        )
    elif state.get("order_result"):
        result = state["order_result"]
        if result["kind"] == "missing_id":
            answer = "Please provide the sample order ID, for example NK000001."
        elif result["kind"] == "not_found":
            answer = f"I could not find sample order {result['order_id']}."
        else:
            answer = (
                f"Sample order {result['order_id']} has status: {result['status']}."
            )
            if result.get("tracking_id"):
                answer += f" Demo tracking ID: {result['tracking_id']}."
            if state.get("escalation_required"):
                answer += " A human support operator should review your request."
    elif state.get("escalation_required") and state.get("evidence"):
        item = state["evidence"][0]
        answer = (
            f"{item['text']}\n\nSource: {item['source']}. "
            "These are fictional capstone rules. A human support operator "
            "should review this request."
        )
        if item["text"] not in answer:
            answer = "I could not verify an answer from the policy evidence."
    elif state.get("escalation_required"):
        answer = (
            "This issue needs human review. Please contact a support operator; "
            "the demo agent cannot decide the claim."
        )
    elif state.get("evidence"):
        item = state["evidence"][0]
        answer = (
            f"{item['text']}\n\nSource: {item['source']}. "
            "These are fictional capstone rules."
        )
        if item["text"] not in answer:
            answer = "I could not verify an answer from the policy evidence."
    else:
        answer = (
            "I could not find enough support in the demo policies to answer that. "
            "Please ask a human support operator."
        )

    return {"answer": answer}


def persist_memory(state: AgentState) -> dict:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    turns = list(state.get("history", []))
    turns.extend(
        [
            {"role": "user", "content": state["safe_message"]},
            {"role": "assistant", "content": state["answer"]},
        ]
    )
    turns = turns[-20:]

    path = memory_file(state["session_id"])
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {"session_id": state["session_id"], "turns": turns},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)

    response = ChatResponse(
        session_id=state["session_id"],
        answer=state["answer"],
        route=state["route"],
        escalation_score=state.get("escalation_score", 0),
        escalation_required=state.get("escalation_required", False),
        sources=state.get("sources", []),
        tools_called=state.get("tools_called", []),
    )
    return {"response": response.model_dump()}


def choose_tool_node(state: AgentState) -> str:
    """Choose the graph branch that matches the routed request."""
    if state.get("route") == "order":
        return "order_lookup"
    if state.get("route") in ("knowledge", "escalation"):
        return "policy_search"
    return "skip_tools"


def order_lookup_node(state: AgentState) -> dict:
    return deterministic_tools(state)


def policy_search_node(state: AgentState) -> dict:
    return deterministic_tools(state)


def skip_tools_node(state: AgentState) -> dict:
    return deterministic_tools(state)


builder = StateGraph(AgentState)
builder.add_node("input_guard", input_guard)
builder.add_node("request_router", request_router)
builder.add_node("order_lookup", order_lookup_node)
builder.add_node("policy_search", policy_search_node)
builder.add_node("skip_tools", skip_tools_node)
builder.add_node("escalation_score", escalation_score)
builder.add_node("mock_llm_response", mock_llm_response)
builder.add_node("persist_memory", persist_memory)

builder.add_edge(START, "input_guard")
builder.add_edge("input_guard", "request_router")
builder.add_conditional_edges(
    "request_router",
    choose_tool_node,
    {
        "order_lookup": "order_lookup",
        "policy_search": "policy_search",
        "skip_tools": "skip_tools",
    },
)
builder.add_edge("order_lookup", "escalation_score")
builder.add_edge("policy_search", "escalation_score")
builder.add_edge("skip_tools", "escalation_score")
builder.add_edge("escalation_score", "mock_llm_response")
builder.add_edge("mock_llm_response", "persist_memory")
builder.add_edge("persist_memory", END)

CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
_CHECKPOINT_CONNECTION = sqlite3.connect(
    str(CHECKPOINT_FILE),
    check_same_thread=False,
)
_SUPPORT_CHECKPOINTER = SqliteSaver(_CHECKPOINT_CONNECTION)
support_graph = builder.compile(checkpointer=_SUPPORT_CHECKPOINTER)


def run_agent(payload: ChatRequest | dict) -> ChatResponse:
    request = (
        payload if isinstance(payload, ChatRequest)
        else ChatRequest.model_validate(payload)
    )
    result = support_graph.invoke(
        {
            "session_id": request.session_id,
            "message": mask_pii(request.message),
        },
        config={"configurable": {"thread_id": request.session_id}},
    )
    return ChatResponse.model_validate(result["response"])


if __name__ == "__main__":
    demo = run_agent(
        {"session_id": "demo-session", "message": "Can I get a refund?"}
    )
    print(demo.model_dump_json(indent=2))
