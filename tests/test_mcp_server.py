"""Regression tests for MCP server transport startup configuration."""

import pytest

import mcp_server


def test_main_runs_stdio_by_default(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        mcp_server.mcp,
        "run",
        lambda transport="stdio": calls.append(transport),
    )

    mcp_server.main([])

    assert calls == ["stdio"]


def test_main_runs_local_sse_with_configured_host_and_port(monkeypatch) -> None:
    calls: list[tuple[str, int]] = []
    original_host = mcp_server.mcp.settings.host
    original_port = mcp_server.mcp.settings.port

    monkeypatch.setattr(
        mcp_server,
        "run_sse",
        lambda host, port: calls.append((host, port)),
    )

    try:
        mcp_server.main(["--sse", "--port", "3011"])
        assert calls == [("127.0.0.1", 3011)]
        assert mcp_server.mcp.settings.host == "127.0.0.1"
        assert mcp_server.mcp.settings.port == 3011
    finally:
        mcp_server.mcp.settings.host = original_host
        mcp_server.mcp.settings.port = original_port


def test_main_rejects_non_local_sse_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(mcp_server.settings, "mcp_api_key", "")

    with pytest.raises(SystemExit):
        mcp_server.main(["--sse", "--host", "0.0.0.0"])
