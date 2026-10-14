# Resilience Demonstration

- SQLite checkpoint file: `data/checkpoints/checkpoints.sqlite`
- Stable thread ID: `capstone-resilience-demo-v2`.
- Before interruption, `prepare_review` and `validate_review_context` each ran once; the graph paused at `wait_for_review`.
- Resume used the same thread ID. Execution counters stayed at one for both completed nodes, while `finish_review` ran once.
- Retry: transient tool succeeded after 3 attempts. Configuration: initial interval 0.02 seconds, backoff factor 2, maximum interval 0.04 seconds, three maximum attempts, jitter enabled.
- Per-node timeout: simulated `slow_node` uses a 0.05-second run timeout.
- Global timeout: `asyncio.wait_for` caps a separate graph run at 0.05 seconds.
- All calls used local code and fictional data; no LLM API or credentials were used.
