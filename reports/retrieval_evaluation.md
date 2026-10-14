# Retrieval Evaluation

## Setup

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: persistent local ChromaDB at `data/chroma/`
- Chunking strategies: fixed word windows (55 words, 12-word overlap) and paragraph grouping (65-word target)
- Model loading: cached model files, offline mode
- Evaluation command: `.\.venv\Scripts\python.exe eval\measure_retrieval.py`

## Results

The labeled set has 20 answerable policy questions and 5 unsupported questions.

| Strategy | Chunks indexed | Top-1 accuracy | Hit@3 | MRR | Selected threshold | Precision | Recall | F1 | Unsupported rejection |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed windows | 22 | 1.000 | 1.000 | 1.000 | 0.39 | 0.952 | 1.000 | 0.976 | 0.800 |
| Paragraph grouping | 12 | 1.000 | 1.000 | 1.000 | 0.39 | 0.952 | 1.000 | 0.976 | 0.800 |

The threshold was selected by sweeping values from 0.00 to 1.00 in 0.01 steps and choosing the value with the best F1 score, then precision.

## Manual checks

- “How do I request a refund?” retrieved `07-refund-timing.md` at similarity 0.561.
- “Tell me the official current Nykaa return policy.” was rejected by the scope guard with an abstention message.

## Limits

This is a small, hand-written synthetic evaluation set. Both strategies scored identically on these questions; that does not prove that they perform equally on real customer questions. One of five unsupported queries scored above the similarity threshold, so the threshold alone is not a reliable safety check. The retrieval code includes a specific guard for official or current Nykaa policy requests. Broader guardrails and the separate RAG-triad evaluation remain to be implemented.
