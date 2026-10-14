"""Evaluate all 15 queries with a deterministic MOCK_LLM judge."""

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

MOCK_LLM_JUDGE_PROMPT = """\
You are the evaluation judge for a fictional e-commerce support demo.
Score context relevance, groundedness, and answer relevance from 0 to 1.
For answerable queries, check the expected source and expected facts against
the retrieved source and agent answer. For unsupported queries, give full
credit only when no source is cited and the agent clearly abstains or explains
that official/current policy is out of scope. Do not use outside knowledge.
Return one score for each metric.
"""


def normalize(text: str) -> str:
    text = text.casefold().replace("%", " percent ")
    text = text.replace("–", " to ").replace("—", " to ").replace("-", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fact_is_present(text: str, fact: str) -> bool:
    normalized_text = f" {normalize(text)} "
    normalized_fact = normalize(fact)
    if f" {normalized_fact} " in normalized_text:
        return True

    variants = {
        "cannot apply": ("cannot apply", "cannot be applied"),
        "not a guaranteed": ("not a guaranteed", "not guaranteed"),
        "12 month": ("12 month", "12 months"),
    }
    return any(
        f" {normalize(variant)} " in normalized_text
        for variant in variants.get(fact.casefold(), ())
    )


def is_clear_abstention(answer: str, route: str) -> bool:
    normalized = normalize(answer)
    if route == "scope":
        return "not official" in normalized or "fictional demo rules" in normalized
    return (
        "could not find enough support" in normalized
        or "could not verify" in normalized
        or "ask a human" in normalized
    )


def mock_judge(query: dict, response, source_text: str) -> dict:
    """Interpret MOCK_LLM_JUDGE_PROMPT using deterministic local checks."""
    expected_source = query.get("expected_source")
    sources = {Path(source).stem for source in response.sources}
    answerable = query["answerable"]

    if not answerable:
        abstained = not response.sources and is_clear_abstention(
            response.answer, response.route
        )
        return {
            "context_relevance": int(not response.sources),
            "groundedness": int(abstained),
            "answer_relevance": int(abstained),
        }

    source_retrieved = expected_source in sources
    facts = query.get("expected_facts", [])
    facts_in_source = all(fact_is_present(source_text, fact) for fact in facts)
    facts_in_answer = all(fact_is_present(response.answer, fact) for fact in facts)

    return {
        "context_relevance": int(source_retrieved),
        "groundedness": int(
            source_retrieved and facts_in_source and facts_in_answer
        ),
        "answer_relevance": int(facts_in_answer),
    }


def main() -> None:
    with QUERY_FILE.open(encoding="utf-8-sig") as query_file:
        queries = [json.loads(line) for line in query_file if line.strip()]

    if len(queries) != 15:
        raise ValueError(f"Expected 15 evaluation queries; found {len(queries)}.")

    results = []
    for query in queries:
        response = run_agent(ChatRequest(
            session_id=f"triad-v2-{query['id']}",
            message=query["question"],
        ))

        expected_source = query.get("expected_source")
        source_text = ""
        if expected_source:
            source_path = KB_DIR / f"{expected_source}.md"
            source_text = source_path.read_text(encoding="utf-8-sig")

        scores = mock_judge(query, response, source_text)
        results.append({
            "id": query["id"],
            "question": query["question"],
            "expected_source": expected_source,
            "route": response.route,
            "sources": response.sources,
            "answer": response.answer,
            **scores,
        })

    metric_names = (
        "context_relevance",
        "groundedness",
        "answer_relevance",
    )
    averages = {
        metric: sum(row[metric] for row in results) / len(results)
        for metric in metric_names
    }

    lines = [
        "# RAG-Triad Evaluation",
        "",
        f"Evaluated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Queries: {len(results)} total; all 12 required KB topics plus 3 unsupported or official-policy cases.",
        "",
        "## MOCK_LLM Judge Prompt",
        "",
        f"> {MOCK_LLM_JUDGE_PROMPT.strip().replace(chr(10), chr(10) + '> ')}",
        "",
        "The project has no LLM API calls. This deterministic local judge interprets the prompt using expected-source, expected-fact, and abstention checks.",
        "",
        "## Scores by query",
        "",
        "| ID | Route | Context relevance | Groundedness | Answer relevance | Cited source(s) |",
        "|---|---|---:|---:|---:|---|",
    ]

    for row in results:
        cited = ", ".join(row["sources"]) if row["sources"] else "None"
        lines.append(
            f"| {row['id']} | {row['route']} | {row['context_relevance']} "
            f"| {row['groundedness']} | {row['answer_relevance']} | {cited} |"
        )

    lines.extend([
        "",
        "## Average scores",
        "",
        "| Metric | Average across 15 queries |",
        "|---|---:|",
        f"| Context relevance | {averages['context_relevance']:.3f} |",
        f"| Groundedness | {averages['groundedness']:.3f} |",
        f"| Answer relevance | {averages['answer_relevance']:.3f} |",
        "",
        "## Demonstrated agent answers",
        "",
    ])

    for row in results:
        excerpt = re.sub(r"\s+", " ", row["answer"]).strip()
        lines.append(f"- **{row['id']} — {row['question']}**")
        lines.append(f"  - Scores: context {row['context_relevance']}, groundedness {row['groundedness']}, answer {row['answer_relevance']}.")
        lines.append(f"  - Answer: {excerpt}")

    lines.extend([
        "",
        "All policy documents contain fictional educational rules, not official or current Nykaa policy.",
        "",
    ])

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
