# Synthetic order dataset

`orders.csv` contains 50 fictional sample orders. Run
`src/nykaa_support/dataset.py` to recreate the dataset deterministically using
seed 2603. The root `README.md` lists the generation weights, value range, and
observed counts.

| Column | Meaning |
|---|---|
| `record_id` | Unique sample order identifier used by the support tool |
| `category` | Product category |
| `status` | Sample order status |
| `order_value_inr` | Fictional order value in rupees |
| `days_since_created` | Order age, from 0 to 30 days |
| `delayed_shipment` | Whether the sample order is marked delayed |
| `order_id` | Alias of `record_id` |
| `amount_inr` | Alias of `order_value_inr` |
| `tracking_id` | Fabricated sample tracking code |

All records and tracking codes are fabricated; the dataset contains no customer
contact details. These examples are for the capstone demonstration and do not
represent real Nykaa orders or transactions.
