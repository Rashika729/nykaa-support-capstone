"""Local MCP server exposing fictional sample-order status lookup."""

import re
import sys
from pathlib import Path

from fastmcp import FastMCP

SOURCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_DIR))

from nykaa_support.dataset import check_order_status as dataset_order_status

mcp = FastMCP("Nykaa Sample Order Support")


@mcp.tool
def check_order_status(record_id: str) -> dict:
    """Return status and escalation details for one fictional sample order ID."""
    normalized_id = record_id.strip().upper()
    if not re.fullmatch(r"NK\d{6}", normalized_id):
        return {
            "found": False,
            "record_id": normalized_id,
            "message": "Enter a sample record ID such as NK000001.",
        }
    return dataset_order_status(normalized_id)


if __name__ == "__main__":
    mcp.run()
