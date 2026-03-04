"""FastAPI application entry point with middleware and router registration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="A data-driven REST API for Formula 1 racing statistics, predictions, and AI-powered race analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routers import health, auth  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
