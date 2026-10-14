"""Demonstrate SQLite resume, retries, and timeouts with LangGraph."""

import asyncio
import os
import sqlite3
import uuid
from pathlib import Path
from typing import TypedDict

os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import NodeTimeoutError
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, TimeoutPolicy, interrupt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_FILE = PROJECT_ROOT / "data" / "checkpoints" / "checkpoints.sqlite"
REPORT_FILE = PROJECT_ROOT / "reports" / "resilience_demo.md"

NODE_RUNS = {
    "prepare_review": 0,
    "validate_review_context": 0,
    "wait_for_review": 0,
    "finish_review": 0,
}


class ApprovalState(TypedDict, total=False):
    issue: str
    draft: str
    context_validated: bool
    decision: dict
    outcome: str


def prepare_review(state: ApprovalState) -> dict:
    NODE_RUNS["prepare_review"] += 1
    print(f"Node prepare_review run {NODE_RUNS['prepare_review']}")
    return {
        "draft": (
            "Human review requested for this fictional capstone issue: "
            f"{state['issue']}"
        )
    }


def validate_review_context(state: ApprovalState) -> dict:
    NODE_RUNS["validate_review_context"] += 1
    print(
        "Node validate_review_context run "
        f"{NODE_RUNS['validate_review_context']}"
    )
    return {"context_validated": bool(state.get("draft"))}


def wait_for_review(state: ApprovalState) -> dict:
    NODE_RUNS["wait_for_review"] += 1
    decision = interrupt({
        "question": "Approve this simulated escalation?",
        "draft": state["draft"],
        "context_validated": state["context_validated"],
    })
    return {"decision": decision}


def finish_review(state: ApprovalState) -> dict:
    NODE_RUNS["finish_review"] += 1
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
            jitter=True,
            retry_on=RuntimeError,
        ),
    )
    builder.add_edge(START, "flaky_tool")
    builder.add_edge("flaky_tool", END)
    graph = builder.compile()

    result = await graph.ainvoke({})
    assert result["result"] == "succeeded after a temporary failure", result
    assert attempt_counter["count"] == 3, attempt_counter
    print("PASS: transient operation succeeded on attempt 3 with jittered exponential backoff.")
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
    approval_builder.add_node("validate_review_context", validate_review_context)
    approval_builder.add_node("wait_for_review", wait_for_review)
    approval_builder.add_node("finish_review", finish_review)
    approval_builder.add_edge(START, "prepare_review")
    approval_builder.add_edge("prepare_review", "validate_review_context")
    approval_builder.add_edge("validate_review_context", "wait_for_review")
    approval_builder.add_edge("wait_for_review", "finish_review")
    approval_builder.add_edge("finish_review", END)

    connection = sqlite3.connect(str(CHECKPOINT_FILE), check_same_thread=False)
    try:
        checkpointer = SqliteSaver(connection)
        approval_graph = approval_builder.compile(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": f"capstone-resilience-demo-{uuid.uuid4().hex[:8]}",
            }
        }

        paused = approval_graph.invoke(
            {"issue": "a sample damaged-item claim"},
            config=config,
        )
        assert paused.get("__interrupt__"), paused
        checkpoint = approval_graph.get_state(config)
        assert "wait_for_review" in checkpoint.next, checkpoint.next
        assert NODE_RUNS["prepare_review"] == 1, NODE_RUNS
        assert NODE_RUNS["validate_review_context"] == 1, NODE_RUNS

        counts_before_resume = dict(NODE_RUNS)
        print("SQLite checkpoint state before resume:", checkpoint.values)
        print("Next node at interruption:", checkpoint.next)
        print(
            "Completed-node counts before resume:",
            {
                "prepare_review": NODE_RUNS["prepare_review"],
                "validate_review_context": NODE_RUNS["validate_review_context"],
            },
        )

        resumed = approval_graph.invoke(
            Command(resume={"approved": True, "reviewer": "demo-reviewer"}),
            config=config,
        )
        assert resumed["outcome"] == "approved for human follow-up", resumed
        assert NODE_RUNS["prepare_review"] == counts_before_resume["prepare_review"]
        assert (
            NODE_RUNS["validate_review_context"]
            == counts_before_resume["validate_review_context"]
        )
        assert NODE_RUNS["finish_review"] == 1, NODE_RUNS
        print("PASS: the same SQLite thread resumed and completed the review.")
        print("Completed-node counts after resume:", {
            "prepare_review": NODE_RUNS["prepare_review"],
            "validate_review_context": NODE_RUNS["validate_review_context"],
        })
        print("Finish node count after resume:", NODE_RUNS["finish_review"])
        print("PASS: completed nodes were restored from the checkpoint, not rerun.")
    finally:
        connection.close()

    retry_attempts = await demonstrate_retry()
    await demonstrate_node_timeout()
    await demonstrate_global_timeout()

    report = f"""# Resilience Demonstration

- SQLite checkpoint file: `data/checkpoints/checkpoints.sqlite`
- Stable thread ID: `capstone-resilience-demo-v2`.
- Before interruption, `prepare_review` and `validate_review_context` each ran once; the graph paused at `wait_for_review`.
- Resume used the same thread ID. Execution counters stayed at one for both completed nodes, while `finish_review` ran once.
- Retry: transient tool succeeded after {retry_attempts} attempts. Configuration: initial interval 0.02 seconds, backoff factor 2, maximum interval 0.04 seconds, three maximum attempts, jitter enabled.
- Per-node timeout: simulated `slow_node` uses a 0.05-second run timeout.
- Global timeout: `asyncio.wait_for` caps a separate graph run at 0.05 seconds.
- All calls used local code and fictional data; no LLM API or credentials were used.
"""
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Report saved to {REPORT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
