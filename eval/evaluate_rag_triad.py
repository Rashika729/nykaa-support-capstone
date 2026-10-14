"""Deterministic, local RAG-triad evaluation for 15 labeled questions."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nykaa_support.agent import ChatRequest, run_agent

QUERY_FILE = PROJECT_ROOT / "eval" / "queries.jsonl"
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"
REPORT_FILE = PROJECT_ROOT / "reports" / "rag_triad_evaluation.md"

# Key facts were selected from the authored fictional KB documents.
REFERENCE_FACTS = {
    "q01": ["status processing"],
    "q02": ["order ID"],
    "q03": ["does not promise a delivery date"],
    "q04": ["current status"],
    "q05": ["cancellation review"],
    "q06": ["cancellation review"],
    "q07": ["cannot be cancelled automatically"],
    "q08": ["cannot be cancelled automatically"],
    "q09": ["cannot edit a delivery address"],
    "q10": ["Do not collect a full address"],
    "q11": ["7 calendar days after delivery"],
    "q12": ["human review"],
    "q13": ["cannot issue or promise refunds"],
    "q14": ["cannot issue or promise refunds"],
    "q15": ["human review"],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def source_stems(sources: list[str]) -> set[str]:
    return {Path(source).stem for source in sources}


def main() -> None:
    with QUERY_FILE.open(encoding="utf-8-sig") as query_file:
        queries = [
            json.loads(line)
            for line in query_file
            if line.strip()
        ]

    selected = [
        item for item in queries
        if item["id"] in REFERENCE_FACTS
        and item.get("expected_source") is not None
    ]

    if len(selected) != 15:
        raise ValueError(
            f"Expected 15 labeled evaluation questions; found {len(selected)}."
        )

    results = []
    for item in selected:
        request = ChatRequest(
            session_id=f"triad-{item['id']}",
            message=item["question"],
        )
        response = run_agent(request)

        expected_source = item["expected_source"]
        cited_sources = source_stems(response.sources)
        expected_source_cited = expected_source in cited_sources

        facts = REFERENCE_FACTS[item["id"]]
        answer_text = normalize(response.answer)
        document_path = KB_DIR / f"{expected_source}.md"
        document_text = normalize(
            document_path.read_text(encoding="utf-8-sig")
        )

        answer_has_facts = all(
            normalize(fact) in answer_text for fact in facts
        )
        source_supports_facts = all(
            normalize(fact) in document_text for fact in facts
        )

        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_source": expected_source,
            "context_relevant": expected_source_cited,
            "answer_relevant": answer_has_facts,
            "faithful": (
                expected_source_cited
                and answer_has_facts
                and source_supports_facts
            ),
        })

    total = len(results)
    metrics = {
        "Context relevance": sum(r["context_relevant"] for r in results),
        "Answer relevance": sum(r["answer_relevant"] for r in results),
        "Faithfulness": sum(r["faithful"] for r in results),
    }

    lines = [
        "# RAG-Triad Evaluation",
        "",
        f"Evaluated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Questions: {total} labeled, answerable questions from `eval/queries.jsonl`.",
        "",
        "## Results",
        "",
        "| Metric | Passing | Score |",
        "|---|---:|---:|",
    ]

    for name, passing in metrics.items():
        lines.append(f"| {name} | {passing}/{total} | {passing / total:.1%} |")

    lines.extend([
        "",
        "## How to read these scores",
        "",
        "- **Context relevance:** the expected KB document appears in the agent's cited sources.",
        "- **Answer relevance:** the answer includes every manually selected key fact for that question.",
        "- **Faithfulness:** the expected source is cited and every checked fact appears in both the answer and that source document.",
        "- These are deterministic checks for a MOCK_LLM demo, not human judgments or an LLM judge. They check selected facts rather than every possible claim.",
        "- All policy documents contain fictional educational rules, not official or current Nykaa policy.",
        "",
        "## Cases to review",
        "",
    ])

    failures = [
        result for result in results
        if not (
            result["context_relevant"]
            and result["answer_relevant"]
            and result["faithful"]
        )
    ]
    if failures:
        for result in failures:
            failed_checks = [
                name for name, key in (
                    ("context", "context_relevant"),
                    ("answer", "answer_relevant"),
                    ("faithfulness", "faithful"),
                )
                if not result[key]
            ]
            lines.append(
                f"- `{result['id']}` ({', '.join(failed_checks)}): "
                f"{result['question']}"
            )
    else:
        lines.append("- None.")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
