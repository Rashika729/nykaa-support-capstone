"""Index and search simulated policies with local MiniLM embeddings."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "data" / "knowledge_base"
DB_DIR = ROOT / "data" / "chroma"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.39


def read_documents() -> list[tuple[str, str]]:
    files = sorted(KB_DIR.glob("*.md"))
    if len(files) < 12:
        raise ValueError(f"Expected at least 12 policy documents; found {len(files)}.")
    return [(file.stem, file.read_text(encoding="utf-8-sig")) for file in files]


def fixed_chunks(text: str, size: int = 55, overlap: int = 12) -> list[str]:
    """Split text into same-sized word windows with overlap."""
    words = text.split()
    if not words:
        return []
    step = size - overlap
    return [
        " ".join(words[start : start + size])
        for start in range(0, len(words), step)
        if words[start : start + size]
    ]


def paragraph_chunks(text: str, size: int = 65) -> list[str]:
    """Keep nearby paragraphs together; split any very long paragraph."""
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks = []
    current = []
    current_size = 0

    for paragraph in paragraphs:
        words = paragraph.split()
        if current and current_size + len(words) > size:
            chunks.append("\n\n".join(current))
            current = []
            current_size = 0

        if len(words) > size:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_size = 0
            chunks.extend(fixed_chunks(paragraph, size=size, overlap=0))
        else:
            current.append(paragraph)
            current_size += len(words)

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def prepare(strategy: str) -> tuple[list[str], list[str], list[dict]]:
    ids = []
    texts = []
    metadata = []

    for doc_id, text in read_documents():
        pieces = fixed_chunks(text) if strategy == "fixed" else paragraph_chunks(text)
        for number, piece in enumerate(pieces):
            ids.append(f"{doc_id}-{number:03d}")
            texts.append(piece)
            metadata.append({"source": f"{doc_id}.md", "strategy": strategy})

    return ids, texts, metadata


def index_documents() -> None:
    print(f"Loading cached embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(DB_DIR))

    for strategy, collection_name in (
        ("fixed", "nykaa_kb_fixed_chunks"),
        ("paragraph", "nykaa_kb_paragraph_chunks"),
    ):
        ids, texts, metadata = prepare(strategy)
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadata,
            embeddings=vectors,
        )
        print(f"{strategy}: indexed {len(texts)} chunks in {collection_name}")


def search(question: str, strategy: str) -> None:
    if not question.strip():
        raise ValueError("Enter a question to search for.")

    normalized = question.lower()
    asks_for_official_policy = (
        "official" in normalized
        or ("current" in normalized and "nykaa" in normalized)
    ) and any(word in normalized for word in ("policy", "return", "refund", "delivery"))

    if asks_for_official_policy:
        print(
            "ABSTAIN: This knowledge base contains fictional demo rules, "
            "not official or current Nykaa policies. Please ask a human support operator."
        )
        return

    collection_name = (
        "nykaa_kb_fixed_chunks"
        if strategy == "fixed"
        else "nykaa_kb_paragraph_chunks"
    )
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(name=collection_name)
    vector = model.encode([question], normalize_embeddings=True)[0].tolist()
    results = collection.query(
        query_embeddings=[vector],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for document, details, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = 1.0 - distance
        if similarity >= SIMILARITY_THRESHOLD:
            hits.append((document, details, similarity))

    if not hits:
        print(
            f"ABSTAIN: No policy chunk reached the measured similarity "
            f"threshold of {SIMILARITY_THRESHOLD:.2f}."
        )
        return

    for rank, (document, details, similarity) in enumerate(hits, start=1):
        print(f"\n{rank}. {details['source']} | similarity: {similarity:.3f}")
        print(document)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the simulated policy documents")
    parser.add_argument("action", choices=("index", "search"))
    parser.add_argument("--question", help="Question to search for")
    parser.add_argument(
        "--strategy",
        choices=("fixed", "paragraph"),
        default="fixed",
        help="Which separately stored chunking strategy to search",
    )
    args = parser.parse_args()

    if args.action == "index":
        index_documents()
    else:
        if not args.question:
            parser.error("search needs --question")
        search(args.question, args.strategy)


if __name__ == "__main__":
    main()
