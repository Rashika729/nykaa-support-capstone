import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fastapi.testclient import TestClient
from nykaa_support.api import app

client = TestClient(app)

health = client.get("/health")
assert health.status_code == 200, health.text
assert health.json()["llm_mode"] == "MOCK_LLM"

session_id = "api-smoke-check"
email = "api-test@example.test"
phone = "9876543210"

reply = client.post(
    "/chat",
    json={
        "session_id": session_id,
        "message": (
            "What is the status of order NK000001? "
            f"My email is {email} and my phone is {phone}."
        ),
    },
)
assert reply.status_code == 200, reply.text
body = reply.json()
assert body["route"] == "order", body
assert "order_lookup" in body["tools_called"], body

trace_path = PROJECT_ROOT / "outputs" / "traces.jsonl"
trace_lines = [
    line for line in trace_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
trace = json.loads(trace_lines[-1])

assert trace["session_hash"] != session_id, trace
assert email not in json.dumps(trace), trace
assert phone not in json.dumps(trace), trace
assert "[REDACTED_EMAIL]" in trace["message"], trace
assert "[REDACTED_PHONE]" in trace["message"], trace

print("PASS: /health returned MOCK_LLM status")
print("PASS: /chat returned the sample order status")
print("PASS: the JSONL trace masked email and phone and hashed the session ID")
