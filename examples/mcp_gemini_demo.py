"""F1 Intelligence via Google Gemini ADK + MCP server.

This demo shows the same MCP server being consumed by Google's Agent
Development Kit — no code changes to the server required.

Prerequisites:
    pip install google-adk
    export GOOGLE_API_KEY=your_key_here

Start the MCP server first:
    python mcp_server.py --sse          # runs on http://localhost:3001/sse

Then run this script:
    python examples/mcp_gemini_demo.py
"""

import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google.genai.types import Content, Part


async def main() -> None:
    f1_tools = MCPToolset(
        connection_params=SseServerParams(url="http://localhost:3001/sse")
    )

    agent = LlmAgent(
        name="f1_analyst",
        model="gemini-2.0-flash",
        instruction=(
            "You are an expert Formula 1 analyst. "
            "Use the available tools to answer questions with precise data."
        ),
        tools=[f1_tools],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name="f1-mcp-demo",
    )

    session = await session_service.create_session(
        app_name="f1-mcp-demo", user_id="analyst"
    )

    questions = [
        "Who dominated the 2020s era in F1 constructors?",
        "Compare Lewis Hamilton and Max Verstappen head to head.",
        "What was the 2023 season summary statistics?",
    ]

    for question in questions:
        print(f"\n{'='*60}\nQ: {question}")
        message = Content(parts=[Part(text=question)])
        async for event in runner.run_async(
            user_id="analyst", session_id=session.id, new_message=message
        ):
            if event.is_final_response():
                print(f"A: {event.content.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
