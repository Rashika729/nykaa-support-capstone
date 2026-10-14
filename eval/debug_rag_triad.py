import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nykaa_support.agent import ChatRequest, run_agent

query_path = PROJECT_ROOT / "eval" / "queries.jsonl"
with query_path.open(encoding="utf-8-sig") as query_file:
    queries = [json.loads(line) for line in query_file if line.strip()]

for item in queries[:15]:
    response = run_agent(
        ChatRequest(
            session_id=f"debug-{item['id']}",
            message=item["question"],
        )
    )
    answer = response.answer.replace("\n", " ")
    print(
        f"{item['id']} expected={item['expected_source']} "
        f"route={response.route} sources={response.sources}"
    )
    print(f"  answer={answer[:220]}")
