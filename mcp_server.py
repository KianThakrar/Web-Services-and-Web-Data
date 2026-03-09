"""MCP (Model Context Protocol) server for the F1 Racing Intelligence API.

Exposes F1 data as tools that can be used by MCP-compatible AI clients
(Claude Desktop, Claude Code, VS Code Copilot, etc.).

Usage:
    python mcp_server.py              # stdio transport — for Claude Desktop / Claude Code
    python mcp_server.py --sse        # SSE transport  — HTTP on port 3001, for any MCP client
    python scripts/setup_mcp.py       # auto-configure Claude Desktop + VS Code Copilot

Configuration:
    Set DATABASE_URL environment variable to point to your PostgreSQL instance.
    Defaults to the docker-compose database on port 5433.
"""

import secrets

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import SseServerTransport
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
import uvicorn

from app.config import settings
from app.database import SessionLocal
from app.models.driver import Driver
from app.models.constructor import Constructor
from app.models.race import Race
from app.models.race_result import RaceResult
from app.services.analytics_service import (
    get_constructor_standings,
    get_driver_standings as _get_driver_standings,
    get_season_summary,
    get_top_race_winners,
    get_win_probability,
)
from app.services.ai_service import get_race_summary
from app.services.weather_service import (
    get_circuit_weather_profile,
    get_driver_weather_performance,
    get_race_weather_impact,
)

mcp = FastMCP("F1 Racing Intelligence API")


def _is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def _extract_mcp_token(headers: Headers) -> str:
    auth_header = headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return headers.get("x-mcp-api-key", "").strip()


def _mcp_request_authorized(headers: Headers) -> bool:
    if not settings.mcp_api_key:
        return True
    presented = _extract_mcp_token(headers)
    return bool(presented) and secrets.compare_digest(presented, settings.mcp_api_key)


async def run_sse_async(host: str, port: int) -> None:
    """Run the SSE transport with optional API-key protection."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        if not _mcp_request_authorized(request.headers):
            return JSONResponse(
                status_code=401,
                content={"detail": "MCP API key required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp._mcp_server.run(
                streams[0],
                streams[1],
                mcp._mcp_server.create_initialization_options(),
            )

    async def handle_messages(scope, receive, send):
        if not _mcp_request_authorized(Headers(scope=scope)):
            response = JSONResponse(
                status_code=401,
                content={"detail": "MCP API key required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        await sse.handle_post_message(scope, receive, send)

    starlette_app = Starlette(
        debug=settings.debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=handle_messages),
        ],
    )

    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


def run_sse(host: str, port: int) -> None:
    """Synchronous wrapper for the authenticated SSE transport."""
    anyio.run(run_sse_async, host, port)


# ── Driver tools ─────────────────────────────────────────────────────────────

@mcp.tool()
def search_drivers(name: str = "", nationality: str = "") -> list[dict]:
    """Search for F1 drivers by name or nationality.

    Args:
        name: Partial or full driver name to search.
        nationality: Filter by nationality (e.g. 'British', 'Dutch').
    """
    db = SessionLocal()
    try:
        query = db.query(Driver)
        if name:
            query = query.filter(Driver.name.ilike(f"%{name}%"))
        if nationality:
            query = query.filter(Driver.nationality == nationality)
        drivers = query.order_by(Driver.last_name).limit(20).all()
        return [
            {"id": d.id, "name": d.name, "nationality": d.nationality,
             "number": d.number, "code": d.code}
            for d in drivers
        ]
    finally:
        db.close()


@mcp.tool()
def get_driver_details(driver_id: int) -> dict:
    """Get full details for a specific F1 driver.

    Args:
        driver_id: The numeric ID of the driver.
    """
    db = SessionLocal()
    try:
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            return {"error": f"Driver {driver_id} not found"}
        return {
            "id": driver.id, "name": driver.name, "nationality": driver.nationality,
            "date_of_birth": driver.date_of_birth, "number": driver.number,
            "code": driver.code, "driver_ref": driver.driver_ref,
        }
    finally:
        db.close()


# ── Race tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_races(season: int) -> list[dict]:
    """List all races in a given Formula 1 season.

    Args:
        season: The season year (e.g. 2024).
    """
    db = SessionLocal()
    try:
        races = db.query(Race).filter(Race.season == season).order_by(Race.round).all()
        return [
            {"id": r.id, "round": r.round, "name": r.name,
             "circuit": r.circuit_name, "country": r.circuit_country, "date": r.date}
            for r in races
        ]
    finally:
        db.close()


@mcp.tool()
def get_race_results(race_id: int) -> list[dict]:
    """Get all finishing results for a specific race.

    Args:
        race_id: The numeric ID of the race.
    """
    db = SessionLocal()
    try:
        results = (
            db.query(RaceResult)
            .filter(RaceResult.race_id == race_id)
            .order_by(RaceResult.finish_position)
            .all()
        )
        return [
            {
                "position": r.finish_position,
                "driver": r.driver.name if r.driver else "Unknown",
                "constructor": r.constructor.name if r.constructor else "Unknown",
                "points": r.points,
                "status": r.status,
            }
            for r in results
        ]
    finally:
        db.close()


@mcp.tool()
def get_race_ai_summary(race_id: int) -> dict:
    """Get an AI-generated narrative summary for a race.

    Args:
        race_id: The numeric ID of the race.
    """
    db = SessionLocal()
    try:
        result = get_race_summary(db, race_id)
        if result is None:
            return {"error": f"Race {race_id} not found"}
        return result
    finally:
        db.close()


# ── Analytics tools ───────────────────────────────────────────────────────────

@mcp.tool()
def get_driver_standings(season: int) -> list[dict]:
    """Get the driver championship standings for a given season.

    Args:
        season: The season year (e.g. 2024).
    """
    db = SessionLocal()
    try:
        return _get_driver_standings(db, season)
    finally:
        db.close()


@mcp.tool()
def get_constructor_standings_tool(season: int) -> list[dict]:
    """Get the constructor championship standings for a given season.

    Args:
        season: The season year (e.g. 2024).
    """
    db = SessionLocal()
    try:
        return get_constructor_standings(db, season)
    finally:
        db.close()


@mcp.tool()
def get_season_summary_tool(season: int) -> dict:
    """Get a high-level statistical summary for a Formula 1 season.

    Args:
        season: The season year (e.g. 2024).
    """
    db = SessionLocal()
    try:
        return get_season_summary(db, season)
    finally:
        db.close()


@mcp.tool()
def get_all_time_top_winners(limit: int = 10) -> list[dict]:
    """Get the drivers with the most race wins of all time.

    Args:
        limit: Number of top drivers to return (default 10).
    """
    db = SessionLocal()
    try:
        return get_top_race_winners(db, limit)
    finally:
        db.close()


@mcp.tool()
def get_driver_win_probability(driver_id: int, circuit_name: str = "") -> dict:
    """Estimate a driver's probability of winning at a given circuit.

    Uses the same logistic regression model as the REST API endpoint, with
    walk-forward feature construction and no look-ahead bias. The prediction
    is driven by decayed career win rate, circuit form, recent points form,
    and constructor form.

    Args:
        driver_id: The numeric ID of the driver.
        circuit_name: Optional circuit name (e.g. 'Monza'). If omitted,
                      returns an overall win probability across all circuits.
    """
    db = SessionLocal()
    try:
        result = get_win_probability(db, driver_id, circuit_name or None)
        if result is None:
            return {"error": f"Driver {driver_id} not found"}
        return result
    finally:
        db.close()


# ── Weather tools ─────────────────────────────────────────────────────────────

@mcp.tool()
def get_circuit_weather(circuit_name: str) -> dict:
    """Get the historical weather profile for an F1 circuit.

    Returns average temperature, rain frequency, and common conditions
    across all races at this circuit's location.

    Args:
        circuit_name: The circuit name (e.g. 'Silverstone Circuit', 'Circuit de Spa-Francorchamps').
    """
    db = SessionLocal()
    try:
        result = get_circuit_weather_profile(db, circuit_name)
        if result is None:
            return {"error": f"No weather data for circuit '{circuit_name}'"}
        return result
    finally:
        db.close()


@mcp.tool()
def get_driver_wet_vs_dry(driver_id: int) -> dict:
    """Compare a driver's performance in wet vs dry weather conditions.

    Splits the driver's race history into wet and dry races based on
    WMO weather codes and precipitation data, then compares win rate,
    podium rate, average finishing position, and points per race.

    Args:
        driver_id: The numeric ID of the driver.
    """
    db = SessionLocal()
    try:
        result = get_driver_weather_performance(db, driver_id)
        if result is None:
            return {"error": f"Driver {driver_id} not found"}
        return result
    finally:
        db.close()


@mcp.tool()
def get_race_weather(race_id: int) -> dict:
    """Get weather conditions and results for a specific race.

    Returns temperature, precipitation, wind speed, and condition
    classification alongside the complete race finishing order.

    Args:
        race_id: The numeric ID of the race.
    """
    db = SessionLocal()
    try:
        result = get_race_weather_impact(db, race_id)
        if result is None:
            return {"error": f"Race {race_id} not found"}
        return result
    finally:
        db.close()


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for stdio and SSE MCP transports."""
    import argparse

    parser = argparse.ArgumentParser(description="F1 Racing Intelligence MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE (HTTP) transport on port 3001 instead of stdio",
    )
    parser.add_argument(
        "--host",
        default=settings.mcp_sse_host,
        help="Host for SSE transport (default: MCP_SSE_HOST or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.mcp_sse_port,
        help="Port for SSE transport (default: MCP_SSE_PORT or 3001)",
    )
    args = parser.parse_args(argv)

    if args.sse:
        if not _is_loopback_host(args.host) and not settings.mcp_api_key:
            parser.error("MCP_API_KEY must be set before exposing SSE beyond localhost")

        print(f"Starting MCP server with SSE transport on http://{args.host}:{args.port}/sse")
        mcp.settings.port = args.port
        mcp.settings.host = args.host
        run_sse(args.host, args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
