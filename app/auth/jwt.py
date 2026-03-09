"""JWT token creation, decoding, and user authentication utilities."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
_BLACKLIST_CLEANUP_INTERVAL = timedelta(minutes=15)
_last_blacklist_cleanup: datetime | None = None


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _decode_with_key_rotation(token: str) -> dict:
    """Try the primary key first, then the previous key for zero-downtime rotation."""
    keys = [settings.secret_key]
    if settings.secret_key_previous:
        keys.append(settings.secret_key_previous)
    last_err: JWTError | None = None
    for key in keys:
        try:
            return jwt.decode(token, key, algorithms=[settings.algorithm])
        except JWTError as exc:
            last_err = exc
    raise last_err  # type: ignore[misc]


def decode_access_token(token: str) -> dict:
    """Decode a JWT using active key-rotation settings."""
    return _decode_with_key_rotation(token)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def purge_expired_blacklist_tokens(db: Session, *, now: datetime | None = None, force: bool = False) -> None:
    """Delete expired blacklist rows periodically to keep auth checks bounded."""
    from app.models.token_blacklist import TokenBlacklist

    global _last_blacklist_cleanup
    now = now or datetime.now(UTC)
    if not force and _last_blacklist_cleanup and now - _last_blacklist_cleanup < _BLACKLIST_CLEANUP_INTERVAL:
        return

    db.query(TokenBlacklist).filter(TokenBlacklist.expires_at < now).delete(synchronize_session=False)
    db.commit()
    _last_blacklist_cleanup = now


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.models.token_blacklist import TokenBlacklist
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        jti: str | None = payload.get("jti")
    except JWTError:
        raise credentials_exception

    purge_expired_blacklist_tokens(db)

    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
