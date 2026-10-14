"""FastAPI endpoints with a masked JSONL trace for every HTTP request."""

import hashlib
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nykaa_support.agent import ChatRequest, ChatResponse, mask_pii, run_agent


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACE_FILE = PROJECT_ROOT / "outputs" / "traces.jsonl"
TRACE_LOCK = threading.Lock()


class RequestTraceMiddleware:
    """Record one PII-masked JSONL trace for each HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        trace_id = uuid.uuid4().hex
        body_parts: list[bytes] = []
        status_code = 500

        async def capture_receive() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                body_parts.append(message.get("body", b""))
            return message

        async def capture_send(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, capture_receive, capture_send)
        except Exception:
            status_code = 500
            raise
        finally:
            raw_request = b"".join(body_parts).decode(
                "utf-8", errors="replace"
            )
            message_text = raw_request
            session_hash = None

            try:
                payload = json.loads(raw_request)
                if isinstance(payload, dict):
                    message_text = str(payload.get("message", raw_request))
                    session_id = payload.get("session_id")
                    if isinstance(session_id, str):
                        session_hash = hashlib.sha256(
                            session_id.encode("utf-8")
                        ).hexdigest()[:16]
            except (json.JSONDecodeError, TypeError):
                pass

            trace = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": trace_id,
                "duration_ms": round(
                    (time.perf_counter() - started_at) * 1000, 2
                ),
                "method": scope.get("method", ""),
                "path": scope.get("path", ""),
                "status_code": status_code,
                "session_hash": session_hash,
                "message": mask_pii(message_text),
                "request": mask_pii(raw_request),
            }
            try:
                TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
                line = json.dumps(trace, ensure_ascii=False) + "\n"
                with TRACE_LOCK:
                    with TRACE_FILE.open("a", encoding="utf-8") as trace_file:
                        trace_file.write(line)
            except OSError:
                # A trace-write failure must not hide the API response.
                pass


app = FastAPI(
    title="Nykaa Domain Support Agent",
    description="Fictional capstone support-agent API using MOCK_LLM.",
    version="0.1.0",
)
app.add_middleware(RequestTraceMiddleware)


class HealthResponse(BaseModel):
    status: str
    llm_mode: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report whether the API process is responding."""
    return HealthResponse(status="ok", llm_mode="MOCK_LLM")


@app.post("/chat", response_model=ChatResponse)
@app.post("/ask", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Run one support-agent turn."""
    return run_agent(request)