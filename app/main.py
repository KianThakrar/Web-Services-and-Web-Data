"""FastAPI application entry point with middleware and router registration."""

import logging
import os

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter — shared instance imported by auth router for login/register
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    description="A data-driven REST API for Formula 1 racing statistics, predictions, and AI-powered race analysis.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Health", "description": "Server health checks and API metadata."},
        {"name": "Authentication", "description": "User registration, JWT login/logout, and token management. Protected endpoints require a Bearer token."},
        {"name": "Drivers", "description": "Browse and search the F1 driver database (874 drivers, 2000–2025). Supports filtering by name and nationality."},
        {"name": "Constructors", "description": "Browse F1 constructor (team) records. Supports filtering by nationality."},
        {"name": "Races", "description": "Query race calendar and results across 25 seasons. Supports filtering by season."},
        {"name": "Predictions", "description": "CRUD operations for user race predictions. Requires authentication — each user manages their own predictions."},
        {"name": "Favourites", "description": "CRUD operations for user favourite drivers. Requires authentication — each user manages their own list."},
        {"name": "Analytics", "description": "Advanced statistical endpoints: championship standings, head-to-head comparisons, win probability models, era dominance analysis, weather × performance correlation, and more."},
        {"name": "AI", "description": "AI-powered race narrative summaries using Claude Haiku. Uses a cache-first strategy with deterministic fallback when no API key is configured."},
    ],
)

# Attach rate limiter state so slowapi middleware can resolve it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:  # noqa: ARG001
    """Preserve intended HTTP status codes and details for expected application errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ---------------------------------------------------------------------------
# CORS — explicitly enumerate allowed origins; never use wildcard with credentials
# ---------------------------------------------------------------------------
allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Security response headers middleware (OWASP recommended)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
from app.routers import health, auth, drivers, constructors, races, predictions, favourites, analytics, ai  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(constructors.router)
app.include_router(races.router)
app.include_router(predictions.router)
app.include_router(favourites.router)
app.include_router(analytics.router)
app.include_router(ai.router)


# ---------------------------------------------------------------------------
# Frontend — serve the SPA dashboard at the root path
# ---------------------------------------------------------------------------
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
_FRONTEND = os.path.join(_FRONTEND_DIR, "index.html")

app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(_FRONTEND)
