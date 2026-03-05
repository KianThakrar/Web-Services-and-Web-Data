"""F1 Intelligence via Anthropic Claude API + MCP server.

Uses the Anthropic Python SDK with tool_use to connect directly
to the MCP server over HTTP SSE.

Prerequisites:
    pip install anthropic httpx-sse
    export ANTHROPIC_API_KEY=your_key_here

Start the MCP server first:
    python mcp_server.py --sse          # runs on http://localhost:3001/sse

Then run this script:
    python examples/mcp_claude_demo.py
"""

import asyncio
import json

import anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main() -> None:
    client = anthropic.Anthropic()

    # Connect to MCP server and fetch available tools
    async with sse_client("http://localhost:3001/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()

            # Convert MCP tool schemas to Anthropic tool format
            tools = [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": t.inputSchema,
                }
                for t in tools_result.tools
            ]

            print(f"Connected — {len(tools)} tools available: {[t['name'] for t in tools]}\n")

            messages = [
                {
                    "role": "user",
                    "content": (
                        "Using the F1 tools available to you: "
                        "1) Find the top 3 all-time race winners, "
                        "2) Get the 2023 driver standings, "
                        "3) Estimate Verstappen's win probability at Monza."
                    ),
                }
            ]

            # Agentic loop — let Claude call tools until it has a final answer
            while True:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            print("Claude:", block.text)
                    break

                # Execute any tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  → Calling tool: {block.name}({json.dumps(block.input)})")
                        result = await session.call_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result.content[0].text if result.content else "{}"),
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    asyncio.run(main())
