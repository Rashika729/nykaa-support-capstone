# Project Ticket — Nykaa Domain Support Agent

## Goal
Build the complete capstone in this workspace as a single public-repository-ready project, meeting the four assignment parts in `spec.md` without requiring paid APIs or network model calls.

## User profile
The learner is a beginner. Explain each component in plain language, show how to run it, and build incrementally with concrete evidence. Do not hide unfinished requirements behind broad claims.

## Required outcomes
- >=40 validated synthetic orders and >=12 authored KB documents.
- Two separately indexed ChromaDB chunking strategies; local MiniLM embeddings; measured similarity threshold and retrieval metrics.
- LangGraph with >=4 nodes, order lookup, escalation score, JSON memory, schema validation, PII masking, injection and groundedness controls.
- FastAPI with >=2 endpoints; PII-safe JSONL traces; >=15 RAG-triad evaluation queries.
- FastMCP server/client; SQLite checkpointing with interruption/resume; exponential retries; per-node and global timeout demonstrations.
- Clear README, reproducible local setup, tests/demos, and accurate final acceptance status.

## Constraints
- `MOCK_LLM` only. Never use API keys or make network calls for model inference.
- Use synthetic records and clearly label the policy corpus as educational simulation, not official Nykaa policy.
- Deadline: October 18, 2026.

## Definition of done
Every acceptance criterion in `spec.md` has an implementation and reproducible evidence; documentation makes limitations explicit; the repository can be run locally from a clean setup.
