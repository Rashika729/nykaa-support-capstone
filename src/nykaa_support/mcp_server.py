"""Local MCP tools for fictional Nykaa capstone data."""

import csv
import re
import sys
from pathlib import Path

from fastmcp import FastMCP

SOURCE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE_DIR))

from nykaa_support.agent import retrieve_policy

ORDERS_FILE = PROJECT_ROOT / "data" / "orders.csv"

mcp = FastMCP("Nykaa Demo Support Tools")


@mcp.tool
def lookup_sample_order(order_id: str) -> dict:
    """Look up the status of one fictional sample order by its ID."""
    normalized_id = order_id.strip().upper()
    if not re.fullmatch(r"NK\d{6}", normalized_id):
        return {
            "found": False,
            "message": "Enter a sample order ID such as NK000001.",
        }

    with ORDERS_FILE.open(encoding="utf-8-sig", newline="") as order_file:
        row = next(
            (
                order
                for order in csv.DictReader(order_file)
                if order["order_id"] == normalized_id
            ),
            None,
        )

    if row is None:
        return {"found": False, "order_id": normalized_id}

    # Return only support-safe fields; never expose customer contact or payment data.
    return {
        "found": True,
        "order_id": normalized_id,
        "status": row["status"],
        "tracking_id": row["tracking_id"],
    }


@mcp.tool
def search_demo_policies(query: str) -> list[dict]:
    """Search fictional demo policy documents; these are not official Nykaa policies."""
    if not query.strip():
        return []

    hits = retrieve_policy(query)
    return [
        {
            "source": hit["source"],
            "text": hit["text"],
        }
        for hit in hits
    ]


if __name__ == "__main__":
    mcp.run()

