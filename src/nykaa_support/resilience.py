"""Demonstrate SQLite resume, retries, and timeouts with LangGraph."""

import asyncio
import os
import sqlite3
from pathlib import Path
from typing import TypedDict

os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import NodeTimeoutError
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, TimeoutPolicy, interrupt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_FILE = PROJECT_ROOT / "data" / "checkpoints" / "resilience.sqlite"
REPORT_FILE = PROJECT_ROOT / "reports" / "resilience_demo.md"


class ApprovalState(TypedDict, total=False):
    issue: str
    draft: str
    decision: dict
    outcome: str


def prepare_review(state: ApprovalState) -> dict:
    return {
        "draft": (
            "Human review requested for this fictional capstone issue: "
            f"{state['issue']}"
        )
    }


def wait_for_review(state: ApprovalState) -> dict:
    # LangGraph checkpoints here and pauses until Command(resume=...) is given.
    decision = interrupt({
        "question": "Approve this simulated escalation?",
        "draft": state["draft"],
    })
    return {"decision": decision}


def finish_review(state: ApprovalState) -> dict:
    approved = state.get("decision", {}).get("approved") is True
    outcome = "approved for human follow-up" if approved else "not approved"
    return {"outcome": outcome}


class RetryState(TypedDict, total=False):
    result: str


async def demonstrate_retry() -> int:
    attempt_counter = {"count": 0}

    async def flaky_tool(state: RetryState) -> dict:
        attempt_counter["count"] += 1
        attempt = attempt_counter["count"]
        print(f"Transient tool attempt {attempt}")
        if attempt < 3:
            raise RuntimeError("Simulated temporary tool failure")
        return {"result": "succeeded after a temporary failure"}

    builder = StateGraph(RetryState)
    builder.add_node(
        "flaky_tool",
        flaky_tool,
        retry_policy=RetryPolicy(
            initial_interval=0.02,
            backoff_factor=2.0,
            max_interval=0.04,
            max_attempts=3,
            jitter=False,
            retry_on=RuntimeError,
        ),
    )
    builder.add_edge(START, "flaky_tool")
    builder.add_edge("flaky_tool", END)
    graph = builder.compile()

    result = await graph.ainvoke({})
    assert result["result"] == "succeeded after a temporary failure", result
    assert attempt_counter["count"] == 3, attempt_counter
    print("PASS: transient operation succeeded on attempt 3 with exponential backoff.")
    return attempt_counter["count"]


class TimeoutState(TypedDict, total=False):
    finished: bool


async def demonstrate_node_timeout() -> None:
    async def slow_node(state: TimeoutState) -> dict:
        await asyncio.sleep(0.5)
        return {"finished": True}

    builder = StateGraph(TimeoutState)
    builder.add_node(
        "slow_node",
        slow_node,
        timeout=TimeoutPolicy(run_timeout=0.05),
        retry_policy=RetryPolicy(max_attempts=1),
    )
    builder.add_edge(START, "slow_node")
    builder.add_edge("slow_node", END)
    graph = builder.compile()

    try:
        await graph.ainvoke({})
    except NodeTimeoutError as error:
        assert error.node == "slow_node", error
        print(
            "PASS: per-node timeout fired for "
            f"{error.node} after about {error.elapsed:.2f}s."
        )
    else:
        raise AssertionError("Expected the per-node timeout to fire.")


async def demonstrate_global_timeout() -> None:
    async def slow_node(state: TimeoutState) -> dict:
        await asyncio.sleep(0.5)
        return {"finished": True}

    builder = StateGraph(TimeoutState)
    builder.add_node("slow_node", slow_node)
    builder.add_edge(START, "slow_node")
    builder.add_edge("slow_node", END)
    graph = builder.compile()

    try:
        await asyncio.wait_for(graph.ainvoke({}), timeout=0.05)
    except TimeoutError:
        print("PASS: application-level global run timeout fired at 0.05s.")
    else:
        raise AssertionError("Expected the global run timeout to fire.")


async def main() -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    approval_builder = StateGraph(ApprovalState)
    approval_builder.add_node("prepare_review", prepare_review)
    approval_builder.add_node("wait_for_review", wait_for_review)
    approval_builder.add_node("finish_review", finish_review)
    approval_builder.add_edge(START, "prepare_review")
    approval_builder.add_edge("prepare_review", "wait_for_review")
    approval_builder.add_edge("wait_for_review", "finish_review")
    approval_builder.add_edge("finish_review", END)

    connection = sqlite3.connect(
        str(CHECKPOINT_FILE),
        check_same_thread=False,
    )
    try:
        checkpointer = SqliteSaver(connection)
        approval_graph = approval_builder.compile(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": "capstone-resilience-demo",
            }
        }

        paused = approval_graph.invoke(
            {"issue": "a sample damaged-item claim"},
            config=config,
        )
        assert paused.get("__interrupt__"), paused
        checkpoint = approval_graph.get_state(config)
        assert "wait_for_review" in checkpoint.next, checkpoint.next
        print("PASS: SQLite checkpoint saved; graph paused for review.")

        resumed = approval_graph.invoke(
            Command(resume={"approved": True, "reviewer": "demo-reviewer"}),
            config=config,
        )
        assert resumed["outcome"] == "approved for human follow-up", resumed
        print("PASS: graph resumed from SQLite and completed the review.")
    finally:
        connection.close()

    retry_attempts = await demonstrate_retry()
    await demonstrate_node_timeout()
    await demonstrate_global_timeout()

    report = f"""# Resilience Demonstration

- SQLite checkpoint file: `data/checkpoints/resilience.sqlite`
- Interruption: approval node paused and saved state with a stable thread ID.
- Resume: the same graph and thread resumed with a demo approval.
- Retries: transient tool succeeded after {retry_attempts} attempts; configured initial interval 0.02s, backoff factor 2.0, maximum interval 0.04s.
- Per-node timeout: async `slow_node` used a 0.05s run timeout.
- Global run timeout: `asyncio.wait_for` capped a separate graph run at 0.05s.
- All calls used local code and fictional data; no LLM API or credentials were used.
"""
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Report saved to {REPORT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
