"""Index and search fictional policy documents with local MiniLM embeddings."""

from __future__ import annotations

import argparse
import os
import re
from functools import lru_cache
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "data" / "knowledge_base"
DB_DIR = ROOT / "data" / "chroma"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.39  # Recalibrate with eval/measure_retrieval.py before grading.


def read_documents() -> list[tuple[str, str]]:
    files = sorted(KB_DIR.glob("*.md"))
    if len(files) < 12:
        raise ValueError(f"Expected at least 12 policy documents; found {len(files)}.")
    return [(file.stem, file.read_text(encoding="utf-8-sig").strip()) for file in files]


def fixed_chunks(text: str, size: int = 55, overlap: int = 12) -> list[str]:
    """Split into fixed word windows, repeating overlap words between chunks."""
    if size <= overlap:
        raise ValueError("Chunk size must be larger than overlap.")
    words = text.split()
    step = size - overlap
    return [" ".join(words[start:start + size]) for start in range(0, len(words), step)]


def sentence_chunks(text: str, max_words: int = 65) -> list[str]:
    """Group complete sentences up to a word limit; split only oversized sentences."""
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        if part.strip()
    ]
    chunks = []
    current = []
    current_words = 0
    for sentence in sentences:
        count = len(sentence.split())
        if count > max_words:
            if current:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            chunks.extend(fixed_chunks(sentence, size=max_words, overlap=0))
        elif current and current_words + count > max_words:
            chunks.append(" ".join(current))
            current, current_words = [sentence], count
        else:
            current.append(sentence)
            current_words += count
    if current:
        chunks.append(" ".join(current))
    return chunks


def prepare(strategy: str) -> tuple[list[str], list[str], list[dict]]:
    if strategy not in {"fixed", "sentence"}:
        raise ValueError("strategy must be 'fixed' or 'sentence'")
    ids, texts, metadata = [], [], []
    for doc_id, text in read_documents():
        pieces = fixed_chunks(text) if strategy == "fixed" else sentence_chunks(text)
        for number, piece in enumerate(pieces):
            ids.append(f"{doc_id}-{number:03d}")
            texts.append(piece)
            metadata.append({"source": f"{doc_id}.md", "strategy": strategy})
    return ids, texts, metadata


@lru_cache(maxsize=1)
def embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def chroma_client():
    return chromadb.PersistentClient(path=str(DB_DIR))


def collection_name(strategy: str) -> str:
    names = {
        "fixed": "nykaa_kb_fixed_chunks",
        "sentence": "nykaa_kb_sentence_chunks",
    }
    if strategy not in names:
        raise ValueError("strategy must be 'fixed' or 'sentence'")
    return names[strategy]


def index_documents() -> None:
    model = embedding_model()
    client = chroma_client()
    for strategy in ("fixed", "sentence"):
        ids, texts, metadata = prepare(strategy)
        collection = client.get_or_create_collection(
            name=collection_name(strategy),
            metadata={"hnsw:space": "cosine"},
        )
        old_ids = collection.get()["ids"]
        if old_ids:
            collection.delete(ids=old_ids)
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        collection.upsert(ids=ids, documents=texts, metadatas=metadata, embeddings=vectors)
        print(f"{strategy}: indexed {len(texts)} chunks in {collection_name(strategy)}")


def retrieve(question: str, strategy: str = "fixed", k: int = 3) -> list[dict]:
    if not question.strip():
        return []
    collection = chroma_client().get_collection(name=collection_name(strategy))
    count = min(k, collection.count())
    if count == 0:
        return []
    vector = embedding_model().encode([question], normalize_embeddings=True)[0].tolist()
    result = collection.query(
        query_embeddings=[vector],
        n_results=count,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc_id, text, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        hits.append({
            "id": doc_id,
            "text": text,
            "source": metadata["source"],
            "similarity": 1.0 - distance,
        })
    return hits


def search(question: str, strategy: str) -> None:
    hits = retrieve(question, strategy=strategy, k=3)
    if not hits or hits[0]["similarity"] < SIMILARITY_THRESHOLD:
        print(
            "I do not know: no retrieved policy evidence reached the current "
            f"similarity threshold ({SIMILARITY_THRESHOLD:.3f})."
        )
        return
    for rank, hit in enumerate(hits, start=1):
        if hit["similarity"] < SIMILARITY_THRESHOLD:
            continue
        print(f"\n{rank}. {hit['source']} | similarity: {hit['similarity']:.3f}")
        print(hit["text"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Search fictional policy documents")
    parser.add_argument("action", choices=("index", "search"))
    parser.add_argument("--question", help="Question to search for")
    parser.add_argument("--strategy", choices=("fixed", "sentence"), default="fixed")
    args = parser.parse_args()
    if args.action == "index":
        index_documents()
    elif not args.question:
        parser.error("search needs --question")
    else:
        search(args.question, args.strategy)


if __name__ == "__main__":
    main()
