"""Configure the F1 Racing Intelligence MCP server for Claude Desktop and VS Code Copilot.

Usage:
    python scripts/setup_mcp.py

What this does:
  1. Adds the MCP server entry to Claude Desktop's config file
  2. Confirms the .vscode/mcp.json is present for VS Code Copilot
"""

import json
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = REPO_ROOT / "mcp_server.py"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/f1_racing_db"


def find_python() -> str:
    """Return the Python executable — prefer the active venv."""
    venv_candidates = [
        REPO_ROOT / "venv" / "bin" / "python",          # Mac/Linux
        REPO_ROOT / "venv" / "Scripts" / "python.exe",  # Windows
    ]
    for p in venv_candidates:
        if p.exists():
            return str(p)
    return sys.executable


def claude_desktop_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        appdata = Path.home() / "AppData" / "Roaming"
        return appdata / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def setup_claude_desktop():
    config_path = claude_desktop_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            print(f"  Warning: existing config at {config_path} is not valid JSON — creating fresh.")

    config.setdefault("mcpServers", {})
    config["mcpServers"]["f1-racing"] = {
        "command": find_python(),
        "args": [str(MCP_SERVER)],
        "env": {"DATABASE_URL": DATABASE_URL},
    }

    config_path.write_text(json.dumps(config, indent=2))
    print(f"  ✓ Claude Desktop config updated: {config_path}")
    print("  → Restart Claude Desktop to activate the F1 tools.")


def check_vscode_config():
    vscode_mcp = REPO_ROOT / ".vscode" / "mcp.json"
    if vscode_mcp.exists():
        print(f"  ✓ VS Code Copilot config present: {vscode_mcp}")
        print("  → Open this repo in VS Code — F1 tools will appear automatically.")
    else:
        print("  ! .vscode/mcp.json not found — run from the repo root.")


def main():
    print("=== F1 Racing Intelligence — MCP Setup ===\n")
    print(f"Repo:       {REPO_ROOT}")
    print(f"Server:     {MCP_SERVER}")
    print(f"Python:     {find_python()}")
    print(f"DB URL:     {DATABASE_URL}")
    print()

    if not MCP_SERVER.exists():
        print("Error: mcp_server.py not found. Run this script from the repo root.")
        sys.exit(1)

    print("[1/2] Configuring Claude Desktop...")
    try:
        setup_claude_desktop()
    except Exception as e:
        print(f"  ! Could not write Claude Desktop config: {e}")

    print()
    print("[2/2] Checking VS Code Copilot config...")
    check_vscode_config()

    print()
    print("Done. Make sure Docker is running first:")
    print("  docker-compose up --build")
    print()
    print("Then restart Claude Desktop or reload VS Code.")


if __name__ == "__main__":
    main()
