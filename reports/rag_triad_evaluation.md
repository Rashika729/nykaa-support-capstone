# RAG-Triad Evaluation

Evaluated: 2026-10-14 17:05 UTC
Queries: 15 total; all 12 required KB topics plus 3 unsupported or official-policy cases.

## MOCK_LLM Judge Prompt

> You are the evaluation judge for a fictional e-commerce support demo.
> Score context relevance, groundedness, and answer relevance from 0 to 1.
> For answerable queries, check the expected source and expected facts against
> the retrieved source and agent answer. For unsupported queries, give full
> credit only when no source is cited and the agent clearly abstains or explains
> that official/current policy is out of scope. Do not use outside knowledge.
> Return one score for each metric.

The project has no LLM API calls. This deterministic local judge interprets the prompt using expected-source, expected-fact, and abstention checks.

## Scores by query

| ID | Route | Context relevance | Groundedness | Answer relevance | Cited source(s) |
|---|---|---:|---:|---:|---|
| q01 | knowledge | 1 | 1 | 1 | 01-return-window-by-category.md |
| q02 | knowledge | 1 | 1 | 1 | 02-cod-refund-timelines.md |
| q03 | knowledge | 1 | 1 | 1 | 03-delivery-slas.md |
| q04 | knowledge | 1 | 1 | 1 | 04-reverse-pickup-eligibility.md |
| q05 | knowledge | 1 | 1 | 1 | 05-warranty-by-category.md |
| q06 | knowledge | 1 | 1 | 1 | 06-order-cancellation.md |
| q07 | knowledge | 1 | 1 | 1 | 07-loyalty-points-redemption.md |
| q08 | knowledge | 1 | 1 | 1 | 08-payment-failure-retry.md |
| q09 | knowledge | 1 | 1 | 1 | 09-size-exchange.md |
| q10 | escalation | 1 | 1 | 1 | 10-damaged-item-claims.md |
| q11 | knowledge | 1 | 1 | 1 | 11-international-shipping-restrictions.md |
| q12 | knowledge | 1 | 1 | 1 | 12-customer-support-escalation-matrix.md |
| q13 | knowledge | 1 | 1 | 1 | None |
| q14 | knowledge | 1 | 1 | 1 | None |
| q15 | scope | 1 | 1 | 1 | None |

## Average scores

| Metric | Average across 15 queries |
|---|---:|
| Context relevance | 1.000 |
| Groundedness | 1.000 |
| Answer relevance | 1.000 |

## Demonstrated agent answers

- **q01 — What is the return review window for a Beauty item in this demo?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Return window by product category For this fictional simulation, Beauty returns may be reviewed within 3 days if the item is unopened, while Apparel and Footwear may be reviewed within 7 days and Electronics and Home within 10 days. These windows are classroom examples and are not official Nykaa policy. A human operator must check the order, item condition, and final eligibility. Source: 01-return-window-by-category.md. These are fictional capstone rules.
- **q02 — If a COD return is approved, how long may the mock refund take?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Cash on delivery refund timelines The simulation cannot transfer money or verify a bank account. If a human operator approves a sample COD return, the mock record may show a pending refund with an estimated 5 to 7 business days. The agent must not promise a real refund date; payment questions require human confirmation. Source: 02-cod-refund-timelines.md. These are fictional capstone rules.
- **q03 — What delivery estimate does the demo give for a remote destination?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Delivery service estimates The fictional demo estimate is 2 to 4 business days for a metro destination and 4 to 7 business days for a remote destination. The sample order record is the source for current status; the estimate is not a guaranteed delivery date. These values are invented for the capstone and do not state an actual Nykaa service level. Source: 03-delivery-slas.md. These are fictional capstone rules.
- **q04 — What conditions are checked for a reverse pickup review?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Reverse pickup eligibility In this simulation, a reverse pickup may be reviewed for an order marked Delivered when the request is within the applicable category return window. A serviceable pickup area and item-condition review are also required, so the agent cannot confirm eligibility by itself. A human operator decides the next step; this is not an official Nykaa policy. Source: 04-reverse-pickup-eligibility.md. These are fictional capstone rules.
- **q05 — What warranty review period is listed for Electronics in the simulation?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Warranty terms by category For this fictional dataset, Electronics items may be reviewed for a 12 month manufacturer warranty and Home items for a 6 month warranty. Apparel and Footwear have no manufacturer warranty in this demo, and Beauty items are handled through the return review instead. A human operator must review warranty claims against the applicable terms. Source: 05-warranty-by-category.md. These are fictional capstone rules.
- **q06 — Can a Placed sample order be reviewed for cancellation?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Order cancellation A sample order marked Placed may be submitted for cancellation review in this simulation. Orders marked Shipped or Delivered cannot be cancelled automatically, and the agent cannot change an order record. A human operator must confirm any cancellation; these are fictional training rules. Source: 06-order-cancellation.md. These are fictional capstone rules. A human support operator should review this request.
- **q07 — How are sample loyalty points valued and capped?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Loyalty points redemption The demo uses fictional points where one point represents one rupee of sample discount value, up to 10 percent of an eligible order. The simulation has no live loyalty account and cannot apply or promise a discount. A human operator must verify any real points balance and promotion terms. Source: 07-loyalty-points-redemption.md. These are fictional capstone rules.
- **q08 — What should I do if my payment is still pending?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Payment failure and retry If a sample payment is pending, the demo advises checking the order record before attempting another payment. A failed payment may be reviewed once after the payment provider response is confirmed; repeated attempts can create duplicate authorizations. Never share a password, PIN, one-time code, or full card number in chat, and send payment disputes to a human. Source: 08-payment-failure-retry.md. These are fictional capstone rules.
- **q09 — Can I request a footwear size exchange after delivery?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Size exchange In this simulation, an Apparel or Footwear size exchange may be reviewed within 7 days of delivery if the item is unused and its tags are attached. An exchange depends on stock and a human condition check, so the agent cannot promise availability or approval. Beauty, Electronics, and Home items are outside this fictional size-exchange rule. Source: 09-size-exchange.md. These are fictional capstone rules.
- **q10 — What does the demo say to do about a damaged item?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Damaged item claims For the demo, a damage claim reported within 48 hours of delivery is routed for human review. The customer should retain the item and packaging while support reviews the claim; the agent must not decide eligibility. Do not send payment credentials or unnecessary personal details in chat; this is not an official Nykaa process. Source: 10-damaged-item-claims.md. These are fictional capstone rules. A human support operator should review this request.
- **q11 — Does this capstone support international delivery?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # International shipping restrictions The fictional capstone dataset supports deliveries within India only and does not calculate international shipping or customs. The agent cannot change a delivery address and should refer international requests to a human operator. This limitation is specific to the simulation and does not describe current Nykaa shipping coverage. Source: 11-international-shipping-restrictions.md. These are fictional capstone rules.
- **q12 — Which issues need immediate human escalation?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: # Customer support escalation matrix Safety concerns, suspected fraud, payment disputes, and injury or allergy reports require immediate human review. Order changes, return eligibility, damage claims, and missing-item claims also require a human decision, with urgency based on the reported harm and time sensitivity. Source: 12-customer-support-escalation-matrix.md. These are fictional capstone rules.
- **q13 — What is the current stock price of Nykaa?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: I could not find enough support in the demo policies to answer that. Please ask a human support operator.
- **q14 — What is the weather in Mumbai today?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: I could not find enough support in the demo policies to answer that. Please ask a human support operator.
- **q15 — What is Nykaa's official current return policy?**
  - Scores: context 1, groundedness 1, answer 1.
  - Answer: This project contains fictional demo rules, not official or current Nykaa policies. Please ask an authorized support operator.

All policy documents contain fictional educational rules, not official or current Nykaa policy.
