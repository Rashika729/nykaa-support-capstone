# Ticket Status

**Overall:** Core capstone features and recorded local demonstrations are complete. Final repository review and public GitHub publication remain.

| Requirement | Status | Evidence |
|---|---|---|
| Specification, ticket, and implementation plan | Done | `spec.md`, `ticket.md`, `ticket_plan.md` |
| Project skeleton and synthetic orders | Done | 48 sample orders; 48 unique IDs were checked |
| Authored knowledge base | Done | 12 fictional policy documents |
| Two Chroma indexes and local MiniLM embeddings | Done | Fixed-size and paragraph indexes built |
| Retrieval evaluation and threshold | Done | 20 answerable questions; both strategies scored 1.000 top-1, hit@3, and MRR; threshold 0.39 |
| LangGraph agent and safeguards | Done | Routing, order lookup, escalation scoring, JSON memory, schemas, PII masking, and input guards implemented |
| RAG-triad evaluation | Done | 15/15 deterministic checks passed for context relevance, answer relevance, and faithfulness |
| FastAPI endpoints and safe traces | Done | Smoke check passed for `/health`, `/chat`, PII masking, and hashed session ID |
| FastMCP server and client | Done | Local order and policy tools discovered and called successfully |
| SQLite resume, retries, and timeouts | Done | Pause/resume, retry, per-node timeout, and global timeout demonstrations passed |
| `.gitignore` and project README | Done | Runtime artifacts excluded; setup and run commands documented |
| Final repository review | Not started | Review tracked files, generated artifacts, and documented commands |
| Public GitHub repository | Not started | Create or choose a public repository, then push the project |

## Notes

All orders and policy rules are fictional educational examples, not official or current Nykaa information. Retrieval and RAG-triad scores are from small, manually labeled deterministic evaluations; they are not human or LLM judgments.

## Remaining work

1. Review repository contents and confirm `.gitignore` excludes local-only files.
2. Run the documented checks and resolve any failures.
3. Create or select a public GitHub repository and push the finished project.
