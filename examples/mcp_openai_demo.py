"""F1 Intelligence via OpenAI Agents SDK + MCP server.

This demo shows the same MCP server being consumed by OpenAI's agent
framework — no code changes to the server required.

Prerequisites:
    pip install openai-agents
    export OPENAI_API_KEY=your_key_here

Start the MCP server first:
    python mcp_server.py --sse          # runs on http://localhost:3001/sse

Then run this script:
    python examples/mcp_openai_demo.py
"""

import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServerSse


async def main() -> None:
    async with MCPServerSse(
        url="http://localhost:3001/sse",
        name="f1-racing",
    ) as f1_server:
        agent = Agent(
            name="F1 Race Analyst",
            instructions=(
                "You are an expert Formula 1 analyst. "
                "Use the available tools to answer questions with precise data."
            ),
            mcp_servers=[f1_server],
        )

        questions = [
            "Who are the top 5 all-time race winners in F1?",
            "What were the 2023 driver championship standings?",
            "Estimate Lewis Hamilton's win probability at Monza.",
        ]

        for question in questions:
            print(f"\n{'='*60}\nQ: {question}")
            result = await Runner.run(agent, question)
            print(f"A: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
