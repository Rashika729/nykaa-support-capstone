# Ticket Status

**Overall:** The capstone is implemented, demonstrated locally, committed, and pushed to the public repository.

| Requirement | Status | Evidence |
|---|---|---|
| Assignment specification and plan | Done | `spec.md`, `ticket.md`, `ticket_plan.md` |
| Seeded synthetic order dataset | Done | 50 orders; seed 2603; all required categories and statuses; 14 delayed orders (28%) |
| Required fictional knowledge base | Done | 12 topic documents in `data/knowledge_base/` |
| Two RAG chunking strategies | Done | Separate fixed and sentence Chroma collections |
| Retrieval calibration and document metrics | Done | Thresholds: 0.534 fixed and 0.465 sentence. For both strategies: P@3 0.333, R@3 1.000, P@1 1.000, and Hit@3 1.000; details in `reports/retrieval_evaluation.md`. |
| LangGraph agent, order tool, memory, and safeguards | Done | Conditional order/policy routing, JSON memory, response validation, PII and injection guards, grounded abstention |
| Conversation transcripts | Done | `reports/memory_demo.md` shows a grounded follow-up and a separate fresh session |
| FastAPI and safe request traces | Done | `/health`, `/chat`, and `/ask`; smoke checks confirm trace IDs, timing, and masked phone/card values |
| RAG-triad evaluation | Done | 15 queries; latest deterministic MOCK_LLM rubric averages are 1.000 for context relevance, groundedness, and answer relevance |
| MCP client/server | Done | Separate HTTP client called `check_order_status` at `http://127.0.0.1:8000/mcp` for two sample records |
| SQLite resume, retries, and timeouts | Done | `agent.py` checkpoints the support graph by session ID; `reports/resilience_demo.md` demonstrates same-thread resume, retry recovery, node timeout, and global timeout |
| README and ignore rules | Done | README records current assignment choices and results; `.gitignore` excludes runtime files |
| Sequence diagram | Done | docs/sequence-diagram.md documents the support request flow |
| Public GitHub submission | Done | https://github.com/Rashika729/nykaa-support-capstone; latest changes are pushed to `main` |

## Evaluation notes

The evaluations use small, manually labeled datasets and deterministic checks under MOCK_LLM. They are not human judgments or external LLM evaluations. Orders and policy rules are fictional and do not represent official or current Nykaa information.
