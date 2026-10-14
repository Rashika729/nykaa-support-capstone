# Retrieval Calibration and Document-level Metrics

Similarity is cosine similarity from normalized local MiniLM embeddings.
Document-level P@3 uses the first three distinct parent documents in ranked chunk order; duplicate chunks are skipped.
The evaluator scans ranked chunks until it finds three distinct documents. R@3 uses unique relevant parent documents retrieved.

## Fixed chunking

### Top-1 similarity calibration

- q01 (in-scope): 0.583 — What is the return review window for a Beauty item in this demo?
- q02 (in-scope): 0.826 — If a COD return is approved, how long may the mock refund take?
- q03 (in-scope): 0.714 — What delivery estimate does the demo give for a remote destination?
- q04 (in-scope): 0.661 — What conditions are checked for a reverse pickup review?
- q05 (in-scope): 0.598 — What warranty review period is listed for Electronics in the simulation?
- q13 (out-of-scope): 0.485 — What is the current stock price of Nykaa?
- q14 (out-of-scope): 0.236 — What is the weather in Mumbai today?
- q15 (official-policy edge case, not used to calibrate): 0.644 — What is Nykaa's official current return policy?

Observed in-scope range: 0.583–0.826.
Observed out-of-scope range: 0.236–0.485.
Selected threshold: (0.583 + 0.485) / 2 = **0.534**.
The observed calibration values have a separating gap.

### Document-level Precision@3 and Recall@3

- q01: retrieved ['01-return-window-by-category', '04-reverse-pickup-eligibility', '10-damaged-item-claims']; relevant ['01-return-window-by-category']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q02: retrieved ['02-cod-refund-timelines', '01-return-window-by-category', '03-delivery-slas']; relevant ['02-cod-refund-timelines']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q03: retrieved ['03-delivery-slas', '10-damaged-item-claims', '11-international-shipping-restrictions']; relevant ['03-delivery-slas']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q04: retrieved ['04-reverse-pickup-eligibility', '05-warranty-by-category', '10-damaged-item-claims']; relevant ['04-reverse-pickup-eligibility']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q05: retrieved ['05-warranty-by-category', '01-return-window-by-category', '10-damaged-item-claims']; relevant ['05-warranty-by-category']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.

Average Precision@3: **0.333**.
Average Recall@3: **1.000**.
Average Precision@1: **1.000**.
Average Hit@3: **1.000**.
Indexed chunks: 25.

## Sentence chunking

### Top-1 similarity calibration

- q01 (in-scope): 0.575 — What is the return review window for a Beauty item in this demo?
- q02 (in-scope): 0.826 — If a COD return is approved, how long may the mock refund take?
- q03 (in-scope): 0.666 — What delivery estimate does the demo give for a remote destination?
- q04 (in-scope): 0.587 — What conditions are checked for a reverse pickup review?
- q05 (in-scope): 0.609 — What warranty review period is listed for Electronics in the simulation?
- q13 (out-of-scope): 0.354 — What is the current stock price of Nykaa?
- q14 (out-of-scope): 0.232 — What is the weather in Mumbai today?
- q15 (official-policy edge case, not used to calibrate): 0.555 — What is Nykaa's official current return policy?

Observed in-scope range: 0.575–0.826.
Observed out-of-scope range: 0.232–0.354.
Selected threshold: (0.575 + 0.354) / 2 = **0.465**.
The observed calibration values have a separating gap.

### Document-level Precision@3 and Recall@3

- q01: retrieved ['01-return-window-by-category', '04-reverse-pickup-eligibility', '10-damaged-item-claims']; relevant ['01-return-window-by-category']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q02: retrieved ['02-cod-refund-timelines', '01-return-window-by-category', '03-delivery-slas']; relevant ['02-cod-refund-timelines']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q03: retrieved ['03-delivery-slas', '10-damaged-item-claims', '11-international-shipping-restrictions']; relevant ['03-delivery-slas']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q04: retrieved ['04-reverse-pickup-eligibility', '12-customer-support-escalation-matrix', '06-order-cancellation']; relevant ['04-reverse-pickup-eligibility']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.
- q05: retrieved ['05-warranty-by-category', '01-return-window-by-category', '02-cod-refund-timelines']; relevant ['05-warranty-by-category']; P@3 = 1/3 = 0.333; P@1 = 1/1 = 1.000; Hit@3 = 1; R@3 = 1/1 = 1.000.

Average Precision@3: **0.333**.
Average Recall@3: **1.000**.
Average Precision@1: **1.000**.
Average Hit@3: **1.000**.
Indexed chunks: 14.

## Recommendation

Deploy sentence chunking: its five-query averages were Precision@3 0.333 and Recall@3 1.000, compared with 0.333 and 1.000 for fixed. Sentence also showed an in-scope minimum of 0.575 above an out-of-scope maximum of 0.354, allowing a measured threshold of 0.465.
