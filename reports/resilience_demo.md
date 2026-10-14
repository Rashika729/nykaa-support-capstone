# Resilience Demonstration

- SQLite checkpoint file: `data/checkpoints/resilience.sqlite`
- Interruption: approval node paused and saved state with a stable thread ID.
- Resume: the same graph and thread resumed with a demo approval.
- Retries: transient tool succeeded after 3 attempts; configured initial interval 0.02s, backoff factor 2.0, maximum interval 0.04s.
- Per-node timeout: async `slow_node` used a 0.05s run timeout.
- Global run timeout: `asyncio.wait_for` capped a separate graph run at 0.05s.
- All calls used local code and fictional data; no LLM API or credentials were used.
