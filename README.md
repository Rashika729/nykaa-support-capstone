# Nykaa Domain Support Agent

**Completed track: Nykaa (E-commerce & Retail).** I built this local capstone to bring together fictional order data, support policies, order lookups, and a FastAPI service in one project. The implementation uses LangGraph, ChromaDB, and FastMCP.

**Public submission:** [Rashika729/nykaa-support-capstone](https://github.com/Rashika729/nykaa-support-capstone)

## Scope and safety

All orders and policy documents are fictional; they are not official or current Nykaa policies. Agent responses use deterministic `MOCK_LLM` templates, with no LLM API calls or keys. On the first indexing run, the MiniLM model is downloaded from Hugging Face and saved to the local cache, so that run needs internet access. Later runs load the cached model locally. The project makes no LLM API calls.

## Part 1 — Dataset and RAG

Run `src/nykaa_support/dataset.py` to generate 50 synthetic orders. The base and selected seed is **2603**. Category weights are Apparel 20%, Electronics 20%, Home 20%, Footwear 20%, and Beauty 20%. Status weights are Placed 20%, Shipped 25%, Delivered 35%, Returned 10%, and Refunded 10%. I chose the INR 299–24,999 range to cover everyday purchases as well as higher-value electronics and home goods. The delay probability is 20%; the generated dataset has 14 delayed orders of 50 (28%).

Observed category counts: Apparel 8, Electronics 10, Home 13, Footwear 6, Beauty 13. Observed status counts: Placed 9, Shipped 11, Delivered 21, Returned 5, Refunded 4. Each order includes the required record ID, category, status, amount, age in days, and delay flag.

Twelve fictional policy documents cover all required assignment topics. RAG implements 55-word fixed chunks with 12-word overlap and sentence chunks grouped up to 65 words. They use separate Chroma collections and local `all-MiniLM-L6-v2` embeddings. The agent uses the sentence collection.

Calibration used five in-scope and two out-of-scope queries. Sentence top-1 scores were 0.575–0.826 in-scope and 0.232–0.354 out-of-scope; the measured midpoint threshold is **0.465**. Fixed-chunk scores were 0.583–0.826 in-scope and 0.236–0.485 out-of-scope; its midpoint threshold is **0.534**. An official/current-policy request is handled separately by a scope guard.

On the same five in-scope queries, fixed and sentence chunking both averaged document-level Precision@3 of **0.333** and Recall@3 of **1.000**. Both strategies also averaged Precision@1 of 1.000 and Hit@3 of 1.000. Precision@3 is 0.333 because each query has one labeled relevant source and the metric counts three distinct retrieved documents. I chose sentence chunking for the agent because it indexed 14 chunks instead of 25 and showed a wider measured gap between in-scope and unrelated queries. The per-query calculations for both strategies are in `reports/retrieval_evaluation.md`.

Order escalation is calculated as `0.70 × delayed_shipment + 0.30 × (days_since_created / 30)`, rounded to four decimals. I set the escalation threshold to **0.73**, the nearest-rank 80th percentile of scores in this generated dataset. `check_order_status(record_id)` returns the order status, INR value, score, and escalation decision.

## Part 2 — LangGraph agent

The graph has eight nodes and uses deterministic routing for order lookup, policy search, escalation, blocked requests, and official/current-policy scope requests. Pydantic request and response models validate structured data. JSON conversation memory is stored by session. The support graph also uses a SQLite checkpointer at `data/checkpoints/checkpoints.sqlite`, keyed by session ID; messages are masked before entering checkpointed state. `eval/demo_memory.py` writes a transcript showing a grounded follow-up in one session and an empty starting history in a separate fresh session.

Input guardrails mask email, Indian phone numbers, and card last-four values and block prompt-injection patterns. The output abstains when retrieval lacks sufficient evidence or a request asks for official/current policy.

## Part 3 — API and evaluation

FastAPI provides `GET /health` and `POST /chat` and `POST /ask`. Chat traces are JSON Lines in `outputs/traces.jsonl`; they include a trace ID, elapsed time, hashed session ID, and PII-masked message.

I evaluated 15 queries covering all 12 policy topics and three unsupported or official-policy cases. My deterministic local rubric, run in MOCK_LLM mode, averaged **1.000 context relevance, 1.000 groundedness, and 1.000 answer relevance**. These are rubric checks rather than human or external language-model judgments. The per-query scores and answer examples are in `reports/rag_triad_evaluation.md`.

## Part 4 — MCP and resilience

`mcp_server.py` exposes `check_order_status` over HTTP at `http://127.0.0.1:8000/mcp`. Start the server in one PowerShell window with `.\.venv\Scripts\python.exe .\src\nykaa_support\mcp_server.py`, then run `mcp_client.py` in another window to call it for two sample records.

`resilience.py` uses LangGraph’s SQLite saver at `data/checkpoints/checkpoints.sqlite`. It demonstrates pause/resume on the support-agent graph: `input_guard`, `request_router`, and `order_lookup` complete before the pause, and execution resumes at `escalation_score` without rerunning them. A separate approval-flow graph also demonstrates same-thread resume. The script demonstrates jittered exponential retries, a per-node timeout, and a global timeout. Results are recorded in `reports/resilience_demo.md`.

## Setup and demonstrations
Requires Python 3.11 or newer.

Run these commands from the project folder in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe .\src\nykaa_support\dataset.py
.\.venv\Scripts\python.exe .\src\nykaa_support\rag.py index
.\.venv\Scripts\python.exe .\eval\measure_retrieval.py
.\.venv\Scripts\python.exe .\eval\evaluate_rag_triad.py
.\.venv\Scripts\python.exe .\eval\demo_memory.py
.\.venv\Scripts\python.exe .\tests\smoke_api.py
# Start mcp_server.py in a second PowerShell window first; leave it running.
.\.venv\Scripts\python.exe .\src\nykaa_support\mcp_client.py
.\.venv\Scripts\python.exe .\src\nykaa_support\resilience.py
.\.venv\Scripts\python.exe -m uvicorn nykaa_support.api:app --reload

## Privacy limitations

Any customer names and delivery addresses in examples are fabricated. Names and delivery addresses are free text and are outside this demo's reliable masking scope. The input guardrail masks fixed-format phone numbers and payment-card last-four values.

See the [request sequence diagram](docs/sequence-diagram.md) for the main data flow.

## Project planning documents

- [Specification](spec.md)
- [Project ticket](ticket.md)
- [Ticket plan](ticket_plan.md)
- [Ticket status](ticket_status.md)
