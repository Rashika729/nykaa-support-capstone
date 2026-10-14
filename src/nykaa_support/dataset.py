"""Seeded synthetic orders for the Nykaa capstone; all records are fictional."""

import csv
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "orders.csv"

ORDER_COUNT = 50
BASE_SEED = 2603
CATEGORIES = ("Apparel", "Electronics", "Home", "Footwear", "Beauty")
CATEGORY_WEIGHTS = (20, 20, 20, 20, 20)
STATUSES = ("Placed", "Shipped", "Delivered", "Returned", "Refunded")
STATUS_WEIGHTS = (20, 25, 35, 10, 10)
MIN_ORDER_VALUE_INR = 299
MAX_ORDER_VALUE_INR = 24999
DELAY_PROBABILITY = 0.20

FIELDS = (
    "record_id", "category", "status", "order_value_inr",
    "days_since_created", "delayed_shipment",
    # Compatibility fields used by the current API and MCP examples.
    "order_id", "amount_inr", "tracking_id",
)


def draw(seed):
    rng = random.Random(seed)
    rows = []
    for number in range(1, ORDER_COUNT + 1):
        record_id = f"NK{number:06d}"
        category = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
        status = rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        value = rng.randint(MIN_ORDER_VALUE_INR, MAX_ORDER_VALUE_INR)
        age = rng.randint(0, 30)
        delayed = rng.random() < DELAY_PROBABILITY
        tracking = (
            f"TRK{number:08d}"
            if status in {"Shipped", "Delivered", "Returned", "Refunded"}
            else ""
        )
        rows.append({
            "record_id": record_id,
            "category": category,
            "status": status,
            "order_value_inr": value,
            "days_since_created": age,
            "delayed_shipment": delayed,
            "order_id": record_id,
            "amount_inr": value,
            "tracking_id": tracking,
        })
    return rows


def valid(rows):
    category_counts = Counter(row["category"] for row in rows)
    status_counts = Counter(row["status"] for row in rows)
    delayed = sum(row["delayed_shipment"] for row in rows)
    rate = delayed / len(rows)
    return (
        all(category_counts[value] >= 3 for value in CATEGORIES)
        and all(status_counts[value] >= 1 for value in STATUSES)
        and 0.10 <= rate <= 0.30
    )


def generate_orders():
    for seed in range(BASE_SEED, BASE_SEED + 10000):
        rows = draw(seed)
        if valid(rows):
            return seed, rows
    raise RuntimeError("No valid seeded dataset found in the configured range")


SELECTED_SEED, ORDERS = generate_orders()


def write_orders():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ORDERS)

    category_counts = Counter(row["category"] for row in ORDERS)
    status_counts = Counter(row["status"] for row in ORDERS)
    delayed = sum(row["delayed_shipment"] for row in ORDERS)
    print(f"Selected seed: {SELECTED_SEED} (base seed {BASE_SEED})")
    print(f"Wrote {len(ORDERS)} orders to {OUTPUT}")
    print("Category counts:", dict(sorted(category_counts.items())))
    print("Status counts:", dict(sorted(status_counts.items())))
    print(f"Delayed shipments: {delayed}/{len(ORDERS)} ({100 * delayed / len(ORDERS):.1f}%)")
    print(f"Order value range: INR {MIN_ORDER_VALUE_INR}–{MAX_ORDER_VALUE_INR}")
    return ORDERS


if __name__ == "__main__":
    write_orders()

def order_escalation_score(order):
    """Score delay risk and normalized age on a 0.0–1.0 scale."""
    delayed_signal = 1.0 if order["delayed_shipment"] else 0.0
    normalized_recency = int(order["days_since_created"]) / 30.0
    return round(0.70 * delayed_signal + 0.30 * normalized_recency, 4)


def nearest_rank_percentile(values, percentile):
    ordered = sorted(values)
    rank = max(1, int(len(ordered) * percentile + 0.999999))
    return ordered[rank - 1]


ORDER_ESCALATION_THRESHOLD = nearest_rank_percentile(
    [order_escalation_score(order) for order in ORDERS],
    0.80,
)


def check_order_status(record_id: str) -> dict:
    """Look up a synthetic order and return status, value, and escalation risk."""
    wanted_id = record_id.strip().upper()
    order = next(
        (item for item in ORDERS if item["record_id"] == wanted_id),
        None,
    )
    if order is None:
        return {"found": False, "record_id": wanted_id}

    score = order_escalation_score(order)
    return {
        "found": True,
        "record_id": order["record_id"],
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "days_since_created": order["days_since_created"],
        "delayed_shipment": order["delayed_shipment"],
        "escalation_score": score,
        "escalation_threshold": ORDER_ESCALATION_THRESHOLD,
        "escalation_required": score >= ORDER_ESCALATION_THRESHOLD,
    }
