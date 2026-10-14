# RAG-Triad Evaluation

Evaluated: 2026-10-14 09:20 UTC
Questions: 15 labeled, answerable questions from `eval/queries.jsonl`.

## Results

| Metric | Passing | Score |
|---|---:|---:|
| Context relevance | 15/15 | 100.0% |
| Answer relevance | 15/15 | 100.0% |
| Faithfulness | 15/15 | 100.0% |

## How to read these scores

- **Context relevance:** the expected KB document appears in the agent's cited sources.
- **Answer relevance:** the answer includes every manually selected key fact for that question.
- **Faithfulness:** the expected source is cited and every checked fact appears in both the answer and that source document.
- These are deterministic checks for a MOCK_LLM demo, not human judgments or an LLM judge. They check selected facts rather than every possible claim.
- All policy documents contain fictional educational rules, not official or current Nykaa policy.

## Cases to review

- None.
