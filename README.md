# Nykaa Domain Support Agent

A local educational capstone demonstrating an e-commerce support agent with LangGraph, retrieval-augmented generation, FastAPI, and MCP.

## Scope and safety

All orders and policy documents are fictional. They do not represent official or current Nykaa policies. The agent uses a deterministic MOCK_LLM and requires no LLM API key. The local MiniLM embedding model must be downloaded once before offline retrieval can run.

## Project components

- `data/orders.csv`: 48 synthetic sample orders
- `data/knowledge_base/`: 12 fictional support documents
- `src/nykaa_support/rag.py`: fixed-size and paragraph chunking with separate ChromaDB indexes
- `src/nykaa_support/agent.py`: LangGraph agent, order lookup, policy search, escalation, memory, and guardrails
- `src/nykaa_support/api.py`: FastAPI `/health` and `/chat` endpoints with PII-safe traces
- `src/nykaa_support/mcp_server.py` and `mcp_client.py`: local FastMCP tools and client
- `src/nykaa_support/resilience.py`: SQLite checkpoint resume, retry, and timeout demonstrations
- `eval/` and `reports/`: evaluation scripts and recorded results

## Setup on Windows

Run these commands from the project folder:

    py -3.14 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -e .

The first embedding-model download requires internet. LLM calls are mocked and do not use the network.

## Run and verify

Build the two local indexes:

    .\.venv\Scripts\python.exe src\nykaa_support\rag.py index

Measure retrieval:

    .\.venv\Scripts\python.exe eval\measure_retrieval.py

Run the RAG-triad evaluation:

    .\.venv\Scripts\python.exe eval\evaluate_rag_triad.py

Run the API smoke check:

    .\.venv\Scripts\python.exe tests\smoke_api.py

Start the API:

    .\.venv\Scripts\python.exe -m uvicorn nykaa_support.api:app --reload

Then open http://127.0.0.1:8000/docs for the local API interface.

Run the MCP client and resilience demonstration:

    .\.venv\Scripts\python.exe src\nykaa_support\mcp_client.py
    .\.venv\Scripts\python.exe src\nykaa_support\resilience.py

## Recorded evaluation

The retrieval evaluation reported top-1 accuracy, hit@3, and MRR of 1.000 for both chunking strategies on 20 labeled answerable questions. The selected similarity threshold was 0.39; 4 of 5 unsupported questions were rejected.

The RAG-triad evaluation reported 15/15 passing checks for context relevance, answer relevance, and faithfulness. These deterministic checks measure selected reference facts; they are not human or LLM judgments. Reports are stored in `reports/`. Re-run the evaluations after changing the documents, data, retrieval, or response templates.

## Data and submission

Keep authored inputs such as the sample orders and knowledge-base documents in the repository. `.gitignore` excludes local environments and runtime artifacts such as indexes, checkpoints, memory, and traces.

The public GitHub repository has not been published yet. Review the project and reports before creating the public repository and pushing the submission.
