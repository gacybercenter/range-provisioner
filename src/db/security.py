"""
Security utilities: Password hashing, verification, and JWT authentication.
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

# Secret key for JWT signing (loads from env or creates persistent local token)
SECRET_KEY = os.environ.get("RANGE_PROVISIONER_SECRET_KEY", "range-provisioner-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key(prefix: str = "rp_live_") -> tuple[str, str, str]:
    """Generate a high-entropy API key, returning (full_key, key_prefix, key_hash)."""
    raw_secret = secrets.token_urlsafe(32)
    full_key = f"{prefix}{raw_secret}"
    key_prefix = full_key[:12] + "..."
    key_hash = hashlib.sha256(full_key.encode("utf-8")).hexdigest()
    return full_key, key_prefix, key_hash


def hash_password(password: str) -> str:
    """Hash password using salt + pbkdf2_hmac sha256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        salt, key_hex = hashed_password.split("$", 1)
        test_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return secrets.compare_digest(test_key.hex(), key_hex)
    except Exception:
        return False


from datetime import datetime, timedelta, timezone

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key_val: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retrieve currently authenticated user via JWT Bearer token or API key."""
    # 1. Check API Key (from X-API-Key or Bearer header)
    candidate_key = api_key_val or (token if token and token.startswith("rp_") else None)
    if candidate_key:
        h = hashlib.sha256(candidate_key.strip().encode("utf-8")).hexdigest()
        try:
            from .models import ApiKey
            matched_key = db.query(ApiKey).filter(ApiKey.key_hash == h, ApiKey.is_active == True).first()
            if matched_key and matched_key.user and matched_key.user.is_active:
                matched_key.last_used_at = datetime.now(timezone.utc)
                db.commit()
                return matched_key.user
        except Exception:
            pass

    # 2. Check JWT Bearer Token
    if not token or token.startswith("rp_"):
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    return user



def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency that strictly requires an authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    """Dependency that strictly requires an admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource",
        )
    return user
