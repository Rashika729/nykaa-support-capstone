# Nykaa Domain Support Agent

**Completed track: Nykaa (E-commerce & Retail).** This repository contains a local, fictional support-agent capstone using LangGraph, ChromaDB, FastAPI, and FastMCP.

**Public submission:** [Rashika729/nykaa-support-capstone](https://github.com/Rashika729/nykaa-support-capstone)

## Scope and safety

All orders and policy documents are fictional; they are not official or current Nykaa policies. Agent responses use deterministic `MOCK_LLM` templates, with no LLM API calls or keys. MiniLM embeddings run locally after the model is available in the Hugging Face cache.

## Part 1 — Dataset and RAG

Run `src/nykaa_support/dataset.py` to generate 50 synthetic orders. The base and selected seed is **2603**. Category weights are Apparel 20%, Electronics 20%, Home 20%, Footwear 20%, and Beauty 20%. Status weights are Placed 20%, Shipped 25%, Delivered 35%, Returned 10%, and Refunded 10%. The INR 299–24,999 amount range represents everyday items through higher-value electronics and home goods. The delay probability is 20%; the generated dataset has 14 delayed orders of 50 (28%).

Observed category counts: Apparel 8, Electronics 10, Home 13, Footwear 6, Beauty 13. Observed status counts: Placed 9, Shipped 11, Delivered 21, Returned 5, Refunded 4. Each order includes the required record ID, category, status, amount, age in days, and delay flag.

Twelve fictional policy documents cover all required assignment topics. RAG implements 55-word fixed chunks with 12-word overlap and sentence chunks grouped up to 65 words. They use separate Chroma collections and local `all-MiniLM-L6-v2` embeddings. The agent uses the sentence collection.

Calibration used five in-scope and two out-of-scope queries. Sentence top-1 scores were 0.575–0.826 in-scope and 0.232–0.354 out-of-scope; the measured midpoint threshold is **0.465**. Fixed-chunk scores were 0.583–0.826 in-scope and 0.236–0.485 out-of-scope; its midpoint threshold is **0.534**. An official/current-policy request is handled separately by a scope guard.

For the same five in-scope queries, both strategies averaged document-level Precision@3 **0.333** and Recall@3 **1.000**. The detailed per-query arithmetic is in `reports/retrieval_evaluation.md`. Sentence chunking is used because it kept those scores with 14 chunks versus 25 for fixed chunking and had a wider measured separation from unrelated queries.

Order escalation is calculated as `0.70 × delayed_shipment + 0.30 × (days_since_created / 30)`, rounded to four decimals. The escalation threshold is **0.73**, the nearest-rank 80th percentile of generated order scores. `check_order_status(record_id)` returns the order status, INR value, score, and escalation decision.

## Part 2 — LangGraph agent

The graph has eight nodes and a conditional route to order lookup, policy search, or no tool. Pydantic request and response models validate structured data. JSON conversation memory is stored by session. The support graph also uses a SQLite checkpointer at `data/checkpoints/checkpoints.sqlite`, keyed by session ID; messages are masked before entering checkpointed state. `eval/demo_memory.py` writes a transcript showing a grounded follow-up in one session and an empty starting history in a separate fresh session.

Input guardrails mask email, Indian phone numbers, and card last-four values and block prompt-injection patterns. The output abstains when retrieval lacks sufficient evidence or a request asks for official/current policy.

## Part 3 — API and evaluation

FastAPI provides `GET /health` and `POST /chat` and `POST /ask`. Chat traces are JSON Lines in `outputs/traces.jsonl`; they include a trace ID, elapsed time, hashed session ID, and PII-masked message.

The 15-query RAG-triad report covers all 12 policy topics plus three unsupported or official-policy cases. The latest local deterministic MOCK_LLM judge run averaged **1.000 context relevance, 1.000 groundedness, and 1.000 answer relevance**. These are rubric checks, not human or external LLM judgments. See `reports/rag_triad_evaluation.md`.

## Part 4 — MCP and resilience

`mcp_server.py` exposes `check_order_status` over HTTP at `http://127.0.0.1:8000/mcp`. Start the server in one PowerShell window with `.\.venv\Scripts\python.exe .\src\nykaa_support\mcp_server.py`, then run `mcp_client.py` in another window to call it for two sample records.

`resilience.py` uses LangGraph’s SQLite saver at `data/checkpoints/checkpoints.sqlite`. It demonstrates pause/resume on the support-agent graph: `input_guard`, `request_router`, and `order_lookup` complete before the pause, and execution resumes at `escalation_score` without rerunning them. A separate approval-flow graph also demonstrates same-thread resume. The script demonstrates jittered exponential retries, a per-node timeout, and a global timeout. Results are recorded in `reports/resilience_demo.md`.

## Setup and demonstrations

Run these commands from the project folder in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe .\src\nykaa_support\dataset.py
.\.venv\Scripts\python.exe .\src\nykaa_support\rag.py index
.\.venv\Scripts\python.exe .\eval\measure_retrieval.py
.\.venv\Scripts\python.exe .\eval\evaluate_rag_triad.py
.\.venv\Scripts\python.exe .\eval\demo_memory.py
.\.venv\Scripts\python.exe .\tests\smoke_api.py
.\.venv\Scripts\python.exe .\src\nykaa_support\mcp_client.py
.\.venv\Scripts\python.exe .\src\nykaa_support\resilience.py
.\.venv\Scripts\python.exe -m uvicorn nykaa_support.api:app --reload

## Privacy limitations

Any customer names and delivery addresses in examples are fabricated. Names and delivery addresses are free text and are outside this demo's reliable masking scope. The input guardrail masks fixed-format phone numbers and payment-card last-four values.
