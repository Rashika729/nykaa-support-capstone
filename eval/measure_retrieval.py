"""Measure similarity calibration and document-level P@3/R@3 for both indexes."""

import json
from pathlib import Path

from nykaa_support.rag import prepare, retrieve

ROOT = Path(__file__).resolve().parents[1]
QUERY_FILE = ROOT / "eval" / "queries.jsonl"
REPORT_FILE = ROOT / "reports" / "retrieval_evaluation.md"
STRATEGIES = ("fixed", "sentence")
IN_SCOPE_CALIBRATION_IDS = {"q01", "q02", "q03", "q04", "q05"}
OUT_OF_SCOPE_CALIBRATION_IDS = {"q13", "q14"}
METRIC_QUERY_IDS = ("q01", "q02", "q03", "q04", "q05")


def load_queries():
    with QUERY_FILE.open(encoding="utf-8-sig") as file:
        return [json.loads(line) for line in file if line.strip()]


def top1_similarity(query, strategy):
    hits = retrieve(query["question"], strategy=strategy, k=1)
    return hits[0]["similarity"] if hits else 0.0


def evaluate_strategy(queries, strategy):
    by_id = {query["id"]: query for query in queries}
    lines = [f"## {strategy.title()} chunking", "", "### Top-1 similarity calibration", ""]
    in_scores = []
    out_scores = []

    for query_id in sorted(IN_SCOPE_CALIBRATION_IDS):
        query = by_id[query_id]
        score = top1_similarity(query, strategy)
        in_scores.append(score)
        lines.append(f"- {query_id} (in-scope): {score:.3f} — {query['question']}")

    for query_id in sorted(OUT_OF_SCOPE_CALIBRATION_IDS):
        query = by_id[query_id]
        score = top1_similarity(query, strategy)
        out_scores.append(score)
        lines.append(f"- {query_id} (out-of-scope): {score:.3f} — {query['question']}")

    edge_query = by_id["q15"]
    edge_score = top1_similarity(edge_query, strategy)
    lines.append(
        f"- q15 (official-policy edge case, not used to calibrate): "
        f"{edge_score:.3f} — {edge_query['question']}"
    )

    min_in = min(in_scores)
    max_out = max(out_scores)
    if min_in > max_out:
        threshold = (min_in + max_out) / 2
        lines.extend([
            "",
            f"Observed in-scope range: {min(in_scores):.3f}–{max(in_scores):.3f}.",
            f"Observed out-of-scope range: {min(out_scores):.3f}–{max(out_scores):.3f}.",
            f"Selected threshold: ({min_in:.3f} + {max_out:.3f}) / 2 = **{threshold:.3f}**.",
            "The observed calibration values have a separating gap.",
        ])
    else:
        threshold = None
        lines.extend([
            "",
            f"Observed in-scope minimum: {min_in:.3f}.",
            f"Observed out-of-scope maximum: {max_out:.3f}.",
            "**No separating gap was observed; do not claim this strategy has a calibrated threshold yet.**",
        ])

    chunk_count = len(prepare(strategy)[0])
    p_values = []
    r_values = []
    p1_values = []
    hit3_values = []
    lines.extend(["", "### Document-level Precision@3 and Recall@3", ""])
    for query_id in METRIC_QUERY_IDS:
        query = by_id[query_id]
        hits = retrieve(query["question"], strategy=strategy, k=chunk_count)
        retrieved_docs = []
        for hit in hits:
            parent = Path(hit["source"]).stem
            if parent not in retrieved_docs:
                retrieved_docs.append(parent)
                if len(retrieved_docs) == 3:
                    break
        if len(retrieved_docs) < 3:
            raise ValueError(
                f"Could not retrieve three distinct parent documents for {query_id}."
            )
        relevant = {query["expected_source"]}
        matched = len(set(retrieved_docs) & relevant)
        precision = matched / 3
        recall = matched / len(relevant)
        p_values.append(precision)
        r_values.append(recall)
        precision_at_1 = int(retrieved_docs[0] in relevant)
        hit_at_3 = int(matched > 0)
        p1_values.append(precision_at_1)
        hit3_values.append(hit_at_3)
        lines.append(
            f"- {query_id}: retrieved {retrieved_docs}; relevant {sorted(relevant)}; "
            f"P@3 = {matched}/3 = {precision:.3f}; "
            f"P@1 = {precision_at_1}/1 = {precision_at_1:.3f}; "
            f"Hit@3 = {hit_at_3}; "
            f"R@3 = {matched}/{len(relevant)} = {recall:.3f}."
        )

    avg_p = sum(p_values) / len(p_values)
    avg_r = sum(r_values) / len(r_values)
    avg_p1 = sum(p1_values) / len(p1_values)
    avg_hit3 = sum(hit3_values) / len(hit3_values)
    lines.extend([
        "",
        f"Average Precision@3: **{avg_p:.3f}**.",
        f"Average Recall@3: **{avg_r:.3f}**.",
        f"Average Precision@1: **{avg_p1:.3f}**.",
        f"Average Hit@3: **{avg_hit3:.3f}**.",
        f"Indexed chunks: {chunk_count}.",
        "",
    ])
    return {
        "strategy": strategy,
        "threshold": threshold,
        "min_in": min_in,
        "max_out": max_out,
        "avg_p": avg_p,
        "avg_p1": avg_p1,
        "avg_hit3": avg_hit3,
        "avg_r": avg_r,
        "chunks": chunk_count,
        "lines": lines,
    }


def main():
    queries = load_queries()
    if len(queries) != 15:
        raise ValueError(f"Expected exactly 15 evaluation queries; found {len(queries)}.")
    results = [evaluate_strategy(queries, strategy) for strategy in STRATEGIES]

    fixed, sentence = results
    if fixed["threshold"] is None and sentence["threshold"] is None:
        recommendation = (
            "Neither strategy separated the measured in-scope and out-of-scope values. "
            "Revise the corpus or calibration examples and measure again before choosing "
            "a deployment threshold."
        )
    else:
        eligible = [item for item in results if item["threshold"] is not None]
        winner = max(
            eligible,
            key=lambda item: (item["avg_p"] + item["avg_r"], -item["chunks"]),
        )
        other = sentence if winner is fixed else fixed
        recommendation = (
            f"Deploy {winner['strategy']} chunking: its five-query averages were "
            f"Precision@3 {winner['avg_p']:.3f} and Recall@3 {winner['avg_r']:.3f}, "
            f"compared with {other['avg_p']:.3f} and {other['avg_r']:.3f} for "
            f"{other['strategy']}. "
            f"{winner['strategy'].title()} also showed an in-scope minimum of "
            f"{winner['min_in']:.3f} above an out-of-scope maximum of "
            f"{winner['max_out']:.3f}, allowing a measured threshold of "
            f"{winner['threshold']:.3f}."
        )

    report = [
        "# Retrieval Calibration and Document-level Metrics",
        "",
        "Similarity is cosine similarity from normalized local MiniLM embeddings.",
        "Document-level P@3 uses the first three distinct parent documents in ranked chunk order; duplicate chunks are skipped.",
        "The evaluator scans ranked chunks until it finds three distinct documents. R@3 uses unique relevant parent documents retrieved.",
        "",
    ]
    for result in results:
        report.extend(result["lines"])
    report.extend(["## Recommendation", "", recommendation, ""])
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\nReport saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
