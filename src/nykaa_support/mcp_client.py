"""Separate-process MCP client demo for two fictional sample orders."""

import asyncio
import json
from pathlib import Path

from fastmcp import Client

SERVER_SCRIPT = Path(__file__).with_name("mcp_server.py").resolve()


async def main() -> None:
    async with Client(SERVER_SCRIPT) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}
        print("Server tools:", ", ".join(sorted(names)))
        assert "check_order_status" in names, names

        for record_id in ("NK000001", "NK000050"):
            result = await client.call_tool(
                "check_order_status",
                {"record_id": record_id},
            )
            data = result.data
            assert data["found"] is True, data
            assert data["record_id"] == record_id, data

            print(f"\nStandard MCP response for {record_id}:")
            if hasattr(result, "model_dump"):
                print(json.dumps(result.model_dump(mode="json"), indent=2))
            else:
                print(json.dumps({"data": data}, indent=2, default=str))

        print("\nPASS: separate MCP client called the local server for two records.")


if __name__ == "__main__":
    asyncio.run(main())
