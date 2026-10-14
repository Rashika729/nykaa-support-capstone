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

## Verification tickets

| Ticket | Acceptance area | Verification |
|---|---|---|
| VT-01 | Seeded dataset | Run `src/nykaa_support/dataset.py`; inspect the seed, record counts, category/status counts, and delayed-shipment percentage. |
| VT-02 | Retrieval and chunking | Run the RAG indexer and `eval/measure_retrieval.py`; inspect both collections' calibration and document-level metrics in `reports/retrieval_evaluation.md`. |
| VT-03 | RAG-triad evaluation | Run `eval/evaluate_rag_triad.py`; inspect all 15 scores and averages in `reports/rag_triad_evaluation.md`. The scoring is a deterministic local rubric, not a model-generated judgment. |
| VT-04 | API and input safeguards | Run `tests/smoke_api.py`; inspect endpoint behavior, request validation and traces, PII masking, injection blocking, and memory redaction. |
| VT-05 | Conversation memory | Run `eval/demo_memory.py`; inspect same-session follow-up and fresh-session transcripts in `reports/memory_demo.md`. |
| VT-06 | MCP round trip | Start `mcp_server.py` in one terminal, then run `mcp_client.py` in another; verify both sample order lookups. |
| VT-07 | Checkpointing and resilience | Run `src/nykaa_support/resilience.py`; inspect support-graph resume, retry recovery, and timeout demonstrations in `reports/resilience_demo.md`. |

## Definition of done
Every acceptance criterion in `spec.md` has an implementation and reproducible evidence; documentation makes limitations explicit; the repository can be run locally from a clean setup.
