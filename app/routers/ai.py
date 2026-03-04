"""AI-powered endpoints — race narrative summaries using Claude."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_service import get_race_summary

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


@router.get("/races/{race_id}/summary")
def race_summary(race_id: int, db: Session = Depends(get_db)):
    """
    Generate or retrieve an AI-powered narrative summary for a race.

    Uses a cache-first strategy: returns a pre-cached summary instantly
    if available. Falls back to calling Claude Haiku when an API key is
    configured, or generates a deterministic summary otherwise.
    """
    result = get_race_summary(db, race_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return result
