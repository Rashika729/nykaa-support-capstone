"""FastAPI endpoints for the Nykaa support agent demo."""

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

from nykaa_support.agent import (
    ChatRequest,
    ChatResponse,
    mask_pii,
    run_agent,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACE_FILE = PROJECT_ROOT / "outputs" / "traces.jsonl"

app = FastAPI(
    title="Nykaa Domain Support Agent",
    description="Fictional capstone support-agent API using MOCK_LLM.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Report whether the API process is responding."""
    return {"status": "ok", "llm_mode": "MOCK_LLM"}


@app.post("/chat", response_model=ChatResponse)
@app.post("/ask", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    started_at = time.perf_counter()
    trace_id = uuid.uuid4().hex
    """Run one support-agent turn and write a PII-safe trace."""
    try:
        response = run_agent(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The support agent could not process this request.",
        ) from exc

    session_hash = hashlib.sha256(
        request.session_id.encode("utf-8")
    ).hexdigest()[:16]

    trace = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "session_hash": session_hash,
        "message": mask_pii(request.message),
        "route": response.route,
        "escalation_score": response.escalation_score,
        "sources": response.sources,
        "tools_called": response.tools_called,
    }

    try:
        TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_FILE.open("a", encoding="utf-8") as trace_file:
            trace_file.write(json.dumps(trace, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="The support agent could not save its trace.",
        ) from exc

    return response
