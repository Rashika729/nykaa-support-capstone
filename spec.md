# Nykaa Domain Support Agent — Project Specification

## Purpose
Build a beginner-friendly, production-minded support agent for a simulated Nykaa e-commerce store. It answers policy questions from a locally authored knowledge base and checks seeded order records. This project is an educational simulation; orders and policies are synthetic and are not official Nykaa data or policy.

## Constraints and delivery
- Deliver one public GitHub repository with dataset, RAG, LangGraph agent, resilience/MCP layer, and FastAPI backend.
- All model behavior uses deterministic `MOCK_LLM`; no API keys or network calls for LLM inference.
- Build in small, explained increments. Keep the repository runnable on a local machine.
- Deadline: October 18, 2026.

## Scope and acceptance criteria

### Part 1 — Dataset design and RAG core (30 marks)
- Seed and validate at least 40 synthetic orders, with a documented schema and reproducible generation.
- Author at least 12 policy/FAQ knowledge-base documents.
- Implement two chunking strategies and index them separately in ChromaDB.
- Use local MiniLM embeddings; no remote embedding service.
- Measure a similarity threshold on validation queries; report retrieval metrics and explain the method.
- Answer policy queries from retrieved evidence and abstain when evidence is insufficient.

### Part 2 — LangGraph agent, tools, memory and guardrails (30 marks)
- Use a LangGraph workflow with at least four meaningful nodes.
- Provide deterministic order lookup and an escalation score/routing decision.
- Persist conversation memory as JSON and validate structured inputs/outputs against schemas.
- Mask PII in logs and user-facing diagnostic surfaces.
- Detect prompt injection and enforce groundedness; unsafe or unsupported requests must fail safely.

### Part 3 — Evaluation, observability and FastAPI deployment (20 marks)
- Provide at least two FastAPI endpoints (including support chat and health/status).
- Emit JSONL traces with PII removed or masked.
- Evaluate at least 15 queries using RAG-triad dimensions (context relevance, answer relevance, groundedness), with a reproducible report.
- Document local run and API usage.

### Part 4 — Resilience and interoperability (20 marks)
- Provide a FastMCP server and client exposing reusable tools.
- Persist LangGraph checkpoints in SQLite and demonstrate interruption and resume.
- Implement exponential-backoff retries for transient failures.
- Demonstrate per-node timeout handling and a global workflow timeout.

## Quality requirements
- Tests and demonstrations must be reproducible, local-first, and clearly label simulated behavior.
- Configuration and data paths must be documented; secrets must not be required.
- Do not claim acceptance criteria are complete until evidence exists.

## Proposed repository layout
```text
README.md
spec.md
ticket.md
ticket_plan.md
ticket_status.md
pyproject.toml
src/nykaa_support/{api,agent,models,config,rag,data,guardrails,memory,observability,resilience,mcp}.py
data/orders.csv
data/knowledge_base/
eval/queries.jsonl
reports/
tests/
```

## Beginner learning path
1. Project skeleton, environment setup, and synthetic data.
2. Knowledge documents, chunking, embeddings, retrieval, and threshold measurement.
3. Typed agent state, tools, LangGraph nodes, memory, and guardrails.
4. Evaluation and traces.
5. API, MCP, checkpointing, retry/timeout demonstrations, final documentation.
