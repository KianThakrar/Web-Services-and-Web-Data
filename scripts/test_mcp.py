"""Verify that the MCP server loads, registers all tools, and can query the database.

Usage:
    python -m scripts.test_mcp
"""

import asyncio
import sys

# Import the MCP server instance (this also validates all imports)
from mcp_server import mcp


async def _run() -> bool:
    """Return True if all checks pass."""
    ok = True

    # 1. List registered tools
    tools = mcp._tool_manager.list_tools()
    print(f"✓ MCP server loaded — {len(tools)} tools registered:\n")
    for t in tools:
        print(f"  {t.name:<35} {t.description.splitlines()[0][:60]}")

    expected = {
        "search_drivers", "get_driver_details", "list_races",
        "get_race_results", "get_race_ai_summary",
        "get_driver_standings", "get_constructor_standings_tool",
        "get_season_summary_tool", "get_all_time_top_winners",
        "get_driver_win_probability",
        "get_circuit_weather", "get_driver_wet_vs_dry", "get_race_weather",
    }
    registered = {t.name for t in tools}
    missing = expected - registered
    if missing:
        print(f"\n✗ Missing tools: {missing}")
        ok = False
    else:
        print(f"\n✓ All {len(expected)} expected tools are registered.")

    # 2. Call a sample of tools to verify DB connectivity
    print("\n--- Calling tools (DB connectivity check) ---\n")
    checks = [
        ("search_drivers", {"name": "Verstappen"}),
        ("list_races", {"season": 2024}),
        ("get_circuit_weather", {"circuit_name": "Silverstone Circuit"}),
        ("get_race_weather", {"race_id": 84}),
    ]
    for name, args in checks:
        try:
            result = await mcp._tool_manager.call_tool(name, args)
            if isinstance(result, dict) and "error" in result:
                print(f"  ✗ {name}  →  error: {result['error']}")
                ok = False
            else:
                summary = f"{len(result)} items" if isinstance(result, list) else "ok"
                print(f"  ✓ {name}({args})  →  {summary}")
        except Exception as e:
            print(f"  ✗ {name}  →  exception: {e}")
            ok = False

    return ok


def main() -> None:
    print("=" * 60)
    print("  F1 Racing Intelligence — MCP Server Verification")
    print("=" * 60, "\n")
    passed = asyncio.run(_run())
    print()
    if passed:
        print("✅  All MCP checks passed.")
    else:
        print("❌  Some checks failed — see errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
