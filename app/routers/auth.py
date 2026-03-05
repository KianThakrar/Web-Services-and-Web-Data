"""Authentication router: register, login, logout, and current user endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt as _jwt
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, get_current_user, oauth2_scheme
from app.config import settings
from app.database import get_db
from app.main import limiter
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.user_service import authenticate_user, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):  # noqa: ARG001 (request used by slowapi decorator)
    """Register a new user account. Rate limited to 10 requests/minute per IP."""
    return register_user(db, data)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):  # noqa: ARG001 (request used by slowapi decorator)
    """Authenticate and return a JWT access token. Rate limited to 10 requests/minute per IP."""
    user = authenticate_user(db, form_data.username, form_data.password)
    token = create_access_token({"sub": user.username})
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),  # noqa: ARG001 (validates token before blacklisting)
    db: Session = Depends(get_db),
):
    """Revoke the current access token. All subsequent requests with this token return 401."""
    payload = _jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    jti = payload.get("jti")
    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    db.add(TokenBlacklist(jti=jti, expires_at=expires_at))
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
