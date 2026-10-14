"""In-process MCP client smoke check; uses no network transport."""

import asyncio
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE_DIR))

from fastmcp import Client
from nykaa_support.mcp_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        assert "lookup_sample_order" in tool_names, tool_names
        assert "search_demo_policies" in tool_names, tool_names
        print("Available MCP tools:", ", ".join(sorted(tool_names)))

        order_result = await client.call_tool(
            "lookup_sample_order",
            {"order_id": "NK000001"},
        )
        order = order_result.data
        assert order["found"] is True, order
        assert order["order_id"] == "NK000001", order
        assert order["status"] == "processing", order
        assert "email" not in order and "phone" not in order, order
        print("Order lookup:", order)

        policy_result = await client.call_tool(
            "search_demo_policies",
            {"query": "Can I get a refund?"},
        )
        policies = policy_result.data
        sources = [item["source"] for item in policies]
        assert "07-refund-timing.md" in sources, sources
        print("Policy search sources:", ", ".join(sources))
        print("PASS: MCP tools were discovered and called locally.")


if __name__ == "__main__":
    asyncio.run(main())
