# Ticket Status

**Overall:** The capstone has been implemented and locally demonstrated. The public repository contains the earlier project version; the latest assignment updates still need to be committed and pushed.

| Requirement | Status | Evidence |
|---|---|---|
| Assignment specification and plan | Done | `spec.md`, `ticket.md`, `ticket_plan.md` |
| Seeded synthetic order dataset | Done | 50 orders; seed 2603; all required categories and statuses; 14 delayed orders (28%) |
| Required fictional knowledge base | Done | 12 topic documents in `data/knowledge_base/` |
| Two RAG chunking strategies | Done | Separate fixed and sentence Chroma collections |
| Retrieval calibration and document metrics | Done | Five in-scope and two out-of-scope queries; thresholds 0.534 fixed and 0.465 sentence; detailed P@3/R@3 in `reports/retrieval_evaluation.md` |
| LangGraph agent, order tool, memory, and safeguards | Done | Conditional order/policy routing, JSON memory, response validation, PII and injection guards, grounded abstention |
| Conversation transcripts | Done | `reports/memory_demo.md` shows a grounded follow-up and a separate fresh session |
| FastAPI and safe request traces | Done | `/health`, `/chat`, and `/ask`; smoke checks confirm trace IDs, timing, and masked phone/card values |
| RAG-triad evaluation | Done | 15 queries; latest deterministic MOCK_LLM rubric averages are 1.000 for context relevance, groundedness, and answer relevance |
| MCP client/server | Done | Separate local client called `check_order_status` for two sample records |
| SQLite resume, retries, and timeouts | Done | `reports/resilience_demo.md`; same-thread resume, retry recovery, node timeout, and global timeout demonstrated |
| README and ignore rules | Updated locally | README records current assignment choices and results; `.gitignore` excludes runtime files |
| Public GitHub submission | Earlier version published | https://github.com/Rashika729/nykaa-support-capstone; latest assignment updates are pending commit and push |

## Evaluation notes

The evaluations use small, manually labeled datasets and deterministic checks under MOCK_LLM. They are not human judgments or external LLM evaluations. Orders and policy rules are fictional and do not represent official or current Nykaa information.
