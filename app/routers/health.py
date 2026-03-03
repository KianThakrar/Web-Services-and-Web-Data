"""Root and health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def root() -> dict:
    """Root endpoint returning API information."""
    return {
        "name": "F1 Racing Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@router.get("/health")
def health_check() -> dict:
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
