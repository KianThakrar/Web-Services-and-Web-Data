"""AI summary service — cache-first race narrative generation using Claude.

Strategy:
  1. Check the ai_summary_cache table for an existing summary.
  2. If found, return it immediately (cached=True) — fully reproducible without API key.
  3. If not found AND ANTHROPIC_API_KEY is configured, call Claude and persist the result.
  4. If not found AND no API key, return a deterministic fallback summary.

This ensures the examiner can clone and run without any API key while still
demonstrating live AI integration when configured.
"""

from sqlalchemy.orm import Session

from app.config import settings
from app.models.ai_summary import AISummaryCache
from app.models.race import Race
from app.models.race_result import RaceResult


def _build_race_context(db: Session, race: Race) -> str:
    """Assemble race result data into a text prompt for Claude."""
    results = (
        db.query(RaceResult)
        .filter(RaceResult.race_id == race.id)
        .order_by(RaceResult.finish_position)
        .limit(10)
        .all()
    )

    lines = [f"Race: {race.name} ({race.season}), Circuit: {race.circuit_name}, {race.circuit_country}", ""]
    lines.append("Top finishers:")
    for r in results:
        pos = r.position_text or str(r.finish_position or "?")
        driver_name = r.driver.name if r.driver else "Unknown"
        constructor_name = r.constructor.name if r.constructor else "Unknown"
        lines.append(f"  P{pos}: {driver_name} ({constructor_name}) — {r.points} pts, Status: {r.status}")

    return "\n".join(lines)


def _generate_with_claude(race_context: str) -> str:
    """Call Claude Haiku to generate a narrative race summary."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are an F1 race commentator. Write a concise, engaging 2-3 sentence narrative "
                    f"summary of this race result for an API response. Focus on the winner, key battles, "
                    f"and any notable moments.\n\n{race_context}"
                ),
            }
        ],
    )
    return message.content[0].text


def _fallback_summary(race: Race, db: Session) -> str:
    """Generate a deterministic summary without any API call."""
    winner_result = (
        db.query(RaceResult)
        .filter(RaceResult.race_id == race.id, RaceResult.finish_position == 1)
        .first()
    )
    winner_name = winner_result.driver.name if winner_result and winner_result.driver else "Unknown"
    constructor_name = winner_result.constructor.name if winner_result and winner_result.constructor else "Unknown"
    return (
        f"{winner_name} claimed victory at the {race.name} ({race.season}) driving for {constructor_name}, "
        f"held at {race.circuit_name} in {race.circuit_country or 'an undisclosed location'}. "
        f"The race showcased the competitive nature of Formula 1 with drivers pushing to the limit."
    )


def get_race_summary(db: Session, race_id: int) -> dict:
    """Return a race narrative summary, using cache where available."""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        return None

    cached = db.query(AISummaryCache).filter(AISummaryCache.race_id == race_id).first()
    if cached:
        return {"race_id": race_id, "race_name": race.name, "season": race.season, "summary": cached.summary, "cached": True}

    if settings.anthropic_api_key:
        context = _build_race_context(db, race)
        summary_text = _generate_with_claude(context)
    else:
        summary_text = _fallback_summary(race, db)

    cache_entry = AISummaryCache(race_id=race_id, summary=summary_text)
    db.add(cache_entry)
    db.commit()

    return {"race_id": race_id, "race_name": race.name, "season": race.season, "summary": summary_text, "cached": False}
