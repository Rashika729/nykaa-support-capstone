"""Build and validate the capstone's fictional order dataset."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

STATUSES = ("processing", "shipped", "out_for_delivery", "delivered", "cancelled", "returned")
PAYMENT_METHODS = ("UPI", "card", "cash_on_delivery", "wallet")
PRODUCTS = (
    ("SKN-101", "Hydrating Face Cleanser", "skincare"),
    ("SKN-205", "Vitamin C Serum", "skincare"),
    ("MKE-110", "Matte Lip Color", "makeup"),
    ("HAI-301", "Nourishing Hair Mask", "haircare"),
    ("FRA-044", "Floral Eau de Parfum", "fragrance"),
    ("WEL-071", "Daily Wellness Gummies", "wellness"),
)


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_name: str
    email: str
    product_sku: str
    product_name: str
    category: str
    quantity: int
    amount_inr: int
    order_date: str
    status: str
    payment_method: str
    tracking_id: str


def build_orders(count: int = 48) -> list[Order]:
    """Return repeatable fictional records; names and emails are placeholders."""
    if count < 40:
        raise ValueError("The assignment requires at least 40 orders.")

    first_day = date(2026, 9, 1)
    orders = []

    for index in range(count):
        sku, product, category = PRODUCTS[index % len(PRODUCTS)]
        status = STATUSES[index % len(STATUSES)]
        tracking = (
            f"TRK{index + 1:08d}"
            if status in {"shipped", "out_for_delivery", "delivered"}
            else ""
        )
        orders.append(
            Order(
                order_id=f"NK{index + 1:06d}",
                customer_name=f"Sample Customer {index + 1:03d}",
                email=f"customer{index + 1:03d}@example.test",
                product_sku=sku,
                product_name=product,
                category=category,
                quantity=index % 3 + 1,
                amount_inr=(599 + 137 * index) * (index % 3 + 1),
                order_date=(first_day + timedelta(days=index % 30)).isoformat(),
                status=status,
                payment_method=PAYMENT_METHODS[index % len(PAYMENT_METHODS)],
                tracking_id=tracking,
            )
        )

    return orders


def validate_orders(orders: list[Order]) -> None:
    """Stop with an explanation if the generated records are inconsistent."""
    if len(orders) < 40:
        raise ValueError(f"Expected at least 40 orders; got {len(orders)}.")

    order_ids = [order.order_id for order in orders]
    if len(order_ids) != len(set(order_ids)):
        raise ValueError("Order IDs must be unique.")

    for order in orders:
        if order.status not in STATUSES:
            raise ValueError(f"Unknown status for {order.order_id}.")
        if order.quantity < 1 or order.amount_inr <= 0:
            raise ValueError(f"Invalid quantity or amount for {order.order_id}.")
        date.fromisoformat(order.order_date)


def write_orders(path: Path = Path("data/orders.csv")) -> None:
    orders = build_orders()
    validate_orders(orders)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(orders[0])))
        writer.writeheader()
        writer.writerows(asdict(order) for order in orders)

    print(f"Created {len(orders)} fictional orders at {path}")


if __name__ == "__main__":
    write_orders()
