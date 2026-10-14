# Resilience Demonstration

- SQLite checkpoint file: `data/checkpoints/checkpoints.sqlite`
- Main support graph: paused after `input_guard`, `request_router`, and `order_lookup`, with `escalation_score` next.
- Main support graph resume: the same SQLite thread continued at `escalation_score`; `mock_llm_response` and `persist_memory` completed, and no pre-pause nodes reran.
- Approval-flow graph: separately paused before `wait_for_review` and resumed on the same thread; its completed-node counters did not increase.
- Retry: transient tool succeeded after 3 attempts. Configuration: initial interval 0.02 seconds, backoff factor 2, maximum interval 0.04 seconds, three maximum attempts, jitter enabled.
- Per-node timeout: simulated `slow_node` uses a 0.05-second run timeout.
- Global timeout: `asyncio.wait_for` caps a separate graph run at 0.05 seconds.
- All calls used local code and fictional data; no LLM API or credentials were used.
