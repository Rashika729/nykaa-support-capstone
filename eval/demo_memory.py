"""Write multi-turn and fresh-session memory demonstrations."""

import json
from datetime import datetime, timezone
from pathlib import Path

from nykaa_support.agent import load_memory, run_agent


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_FILE = PROJECT_ROOT / "reports" / "memory_demo.md"


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    multi_session = f"memory-multi-{stamp}"
    fresh_session = f"memory-fresh-{stamp}"

    assert load_memory(multi_session) == []
    first_question = "What is the return review window for a Beauty item?"
    first_answer = run_agent({
        "session_id": multi_session,
        "message": first_question,
    })
    saved_before_followup = load_memory(multi_session)
    assert len(saved_before_followup) == 2, saved_before_followup

    followup_question = "Does the Beauty item need to be unopened?"
    followup_answer = run_agent({
        "session_id": multi_session,
        "message": followup_question,
    })
    final_multi_history = load_memory(multi_session)
    assert len(final_multi_history) == 4, final_multi_history

    fresh_start = load_memory(fresh_session)
    assert fresh_start == [], fresh_start
    fresh_question = "What warranty review period is listed for Electronics?"
    fresh_answer = run_agent({
        "session_id": fresh_session,
        "message": fresh_question,
    })
    fresh_history = load_memory(fresh_session)
    assert len(fresh_history) == 2, fresh_history
    assert all(
        first_question not in turn["content"]
        for turn in fresh_history
    ), fresh_history

    lines = [
        "# Conversation Memory Demonstration",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Multi-turn session",
        "",
        f"- Session ID: `{multi_session}`",
        f"- Before its first turn, stored history was empty: yes.",
        f"- After turn one and before the follow-up, saved turn count: {len(saved_before_followup)}.",
        "- The follow-up ran using the same session ID and loaded the saved history.",
        f"- Final saved turn count: {len(final_multi_history)}.",
        "",
        f"**User:** {first_question}",
        "",
        f"**Agent:** {first_answer.answer}",
        "",
        f"**User:** {followup_question}",
        "",
        f"**Agent:** {followup_answer.answer}",
        "",
        "## Separate fresh session",
        "",
        f"- Session ID: `{fresh_session}`",
        f"- Stored history before its first turn: `{json.dumps(fresh_start)}`",
        f"- It did not contain the multi-turn session's first question: yes.",
        "",
        f"**User:** {fresh_question}",
        "",
        f"**Agent:** {fresh_answer.answer}",
        "",
        f"- Fresh session's own saved turn count after its first exchange: {len(fresh_history)}.",
        "",
    ]
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Report saved to {REPORT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
