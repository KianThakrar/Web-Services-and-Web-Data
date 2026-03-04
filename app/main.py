"""FastAPI application entry point with middleware and router registration."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

# ---------------------------------------------------------------------------
# Rate limiter — shared instance imported by auth router for login/register
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    description="A data-driven REST API for Formula 1 racing statistics, predictions, and AI-powered race analysis.",
    version="1.0.0",
)

# Attach rate limiter state so slowapi middleware can resolve it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — explicitly enumerate allowed origins; never use wildcard with credentials
# ---------------------------------------------------------------------------
allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
