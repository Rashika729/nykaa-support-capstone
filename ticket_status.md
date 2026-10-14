# Ticket Status

**Overall:** The capstone is implemented, locally demonstrated, committed, and published as a public GitHub repository.

| Requirement | Status | Evidence |
|---|---|---|
| Specification, ticket, and plan | Done | `spec.md`, `ticket.md`, `ticket_plan.md` |
| Synthetic orders and knowledge base | Done | 48 unique sample orders and 12 fictional policy documents |
| Dual Chroma indexes and local MiniLM | Done | Fixed-size and paragraph indexes built locally |
| Retrieval evaluation | Done | 20 answerable questions; both strategies scored 1.000 top-1, hit@3, and MRR; selected threshold 0.39 |
| LangGraph agent and safeguards | Done | Routing, order lookup, escalation scoring, JSON memory, schemas, PII masking, and input guards implemented |
| RAG-triad evaluation | Done | 15/15 deterministic checks passed for context relevance, answer relevance, and faithfulness |
| FastAPI and safe traces | Done | `/health` and `/chat` smoke check passed; trace masking and session hashing checked |
| FastMCP tools | Done | Local client discovered and called order and policy tools |
| SQLite resume, retries, and timeouts | Done | Pause/resume, retry, per-node timeout, and global timeout demonstrations passed |
| Documentation and ignore rules | Done | README and `.gitignore` cover setup, evaluations, and local runtime files |
| Public GitHub submission | Done | https://github.com/Rashika729/nykaa-support-capstone; `main` pushed to `origin/main` |

## Evaluation notes

The retrieval and RAG-triad results are from small, manually labeled deterministic evaluations. They check selected reference facts and are not human or LLM judgments. All order and policy examples are fictional educational content, not official or current Nykaa information.

## Handoff

The local `main` branch was pushed to the public repository. The working tree was clean after that push.
