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

from mcp.server.fastmcp import FastMCP

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
)
from app.services.ai_service import get_race_summary

mcp = FastMCP("F1 Racing Intelligence API")


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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="F1 Racing Intelligence MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE (HTTP) transport on port 3001 instead of stdio",
    )
    parser.add_argument("--port", type=int, default=3001, help="Port for SSE transport (default: 3001)")
    args = parser.parse_args()

    if args.sse:
        print(f"Starting MCP server with SSE transport on http://localhost:{args.port}/sse")
        mcp.run(transport="sse", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")
