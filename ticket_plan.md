# Ticket Plan

Work through these phases in order. Keep each phase small enough for the learner to run and understand before moving on.

1. **Workspace audit and project skeleton** — inspect existing files, record available Python/package manager, agree on a minimal modular layout, add packaging and beginner setup instructions.
2. **Synthetic order dataset** — define schema, generate >=40 deterministic orders, add validation and a data dictionary.
3. **Policy knowledge base** — author >=12 clearly synthetic policy/FAQ documents; define source metadata and safe-answer behavior.
4. **RAG core** — implement and separately persist two chunking strategies in ChromaDB; use local MiniLM embeddings; evaluate candidate thresholds and report retrieval metrics.
5. **Agent foundation** — typed schemas and state, deterministic router, order lookup, policy answer, escalation scoring, >=4 LangGraph nodes.
6. **Memory and safety** — JSON-persisted conversation memory; schema validation; PII masking; injection filtering; groundedness and abstention checks.
7. **Evaluation and traces** — >=15 labeled evaluation cases across RAG-triad dimensions; reproducible summary; PII-safe JSONL observability.
8. **FastAPI** — chat and health/status endpoints, request/response validation, local run guide.
9. **MCP and resilience** — FastMCP server/client, SQLite checkpointing, interrupt/resume demonstration, exponential-backoff retries, node/global timeout demonstrations.
10. **Final verification and public-repo readiness** — run documented tests and demos, inspect generated data/reports, mark each criterion in `ticket_status.md`, and finish README with setup, architecture, examples, limitations, and submission checklist.

## Per-phase practice
For every phase: explain the concept; implement the smallest useful slice; run the relevant checks; describe the result and any remaining limitation before proceeding.
