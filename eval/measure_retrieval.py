"""Measure retrieval quality and calibrate a threshold with supported and unsupported questions."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
QUERY_FILE = ROOT / "eval" / "queries.jsonl"
DB_DIR = ROOT / "data" / "chroma"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_queries() -> list[dict]:
    with QUERY_FILE.open(encoding="utf-8-sig") as file:
        queries = [json.loads(line) for line in file if line.strip()]

    if len(queries) < 15:
        raise ValueError(f"Expected at least 15 queries; found {len(queries)}.")
    return queries


def evaluate_strategy(model: SentenceTransformer, strategy: str, queries: list[dict]) -> None:
    collection_name = (
        "nykaa_kb_fixed_chunks"
        if strategy == "fixed"
        else "nykaa_kb_paragraph_chunks"
    )
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(name=collection_name)
    records = []

    for query in queries:
        vector = model.encode(
            [query["question"]], normalize_embeddings=True
        )[0].tolist()
        result = collection.query(
            query_embeddings=[vector],
            n_results=3,
            include=["metadatas", "distances"],
        )

        sources = [Path(item["source"]).stem for item in result["metadatas"][0]]
        scores = [1.0 - distance for distance in result["distances"][0]]
        expected = query.get("expected_source")
        supported = expected is not None
        reciprocal_rank = (
            next(
                (1.0 / (rank + 1) for rank, source in enumerate(sources) if source == expected),
                0.0,
            )
            if supported
            else 0.0
        )
        records.append(
            {
                "supported": supported,
                "top1_correct": supported and sources[0] == expected,
                "hit_at_3": supported and expected in sources,
                "reciprocal_rank": reciprocal_rank,
                "top1_score": scores[0],
            }
        )

    supported_rows = [row for row in records if row["supported"]]
    unsupported_rows = [row for row in records if not row["supported"]]
    positive_count = len(supported_rows)

    top1 = sum(row["top1_correct"] for row in supported_rows) / positive_count
    hit_at_3 = sum(row["hit_at_3"] for row in supported_rows) / positive_count
    mrr = sum(row["reciprocal_rank"] for row in supported_rows) / positive_count

    threshold_results = []
    for step in range(101):
        threshold = step / 100
        selected_rows = [
            row for row in records if row["top1_score"] >= threshold
        ]
        true_positive = sum(
            row["supported"] and row["top1_correct"] for row in selected_rows
        )
        precision = true_positive / len(selected_rows) if selected_rows else 0.0
        recall = true_positive / positive_count
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        rejected = sum(
            row["top1_score"] < threshold for row in unsupported_rows
        )
        rejection_rate = rejected / len(unsupported_rows) if unsupported_rows else 0.0
        threshold_results.append(
            (f1, precision, threshold, recall, rejection_rate)
        )

    best = max(threshold_results, key=lambda row: (row[0], row[1], row[2]))
    print(f"\n{strategy.upper()} chunking")
    print(f"Answerable questions: {positive_count}")
    print(f"Top-1 accuracy:       {top1:.3f}")
    print(f"Hit@3:                {hit_at_3:.3f}")
    print(f"MRR:                  {mrr:.3f}")
    print(f"Unsupported questions: {len(unsupported_rows)}")
    print(
        f"Selected threshold:   {best[2]:.2f} "
        f"(precision={best[1]:.3f}, recall={best[3]:.3f}, "
        f"F1={best[0]:.3f}, unsupported rejection={best[4]:.3f})"
    )


def main() -> None:
    queries = load_queries()
    print(f"Loading cached model for {len(queries)} labeled questions...")
    model = SentenceTransformer(MODEL_NAME)
    evaluate_strategy(model, "fixed", queries)
    evaluate_strategy(model, "paragraph", queries)


if __name__ == "__main__":
    main()
