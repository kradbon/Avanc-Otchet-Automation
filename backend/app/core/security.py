from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.database import get_db, row_to_user
from app.models import UserRecord, UserRole


HASH_ITERATIONS = 390_000
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = hashed_password.split("$")
    except ValueError:
        return False

    if scheme != "pbkdf2_sha256":
        return False

    salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
    expected_digest = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)
    return "$".join(
        [
            "pbkdf2_sha256",
            str(HASH_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def create_access_token(subject: str, role: UserRole) -> str:
    expires_delta = timedelta(hours=settings.access_token_expire_hours)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db),
) -> UserRecord:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_error
        user_id = int(subject)
    except (JWTError, ValueError):
        raise credentials_error from None

    row = db.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1",
        (user_id,),
    ).fetchone()
    if row is None:
        raise credentials_error
    return row_to_user(row)


def require_role(*allowed_roles: UserRole) -> Callable[..., UserRecord]:
    def dependency(current_user: UserRecord = Depends(get_current_user)) -> UserRecord:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции.",
            )
        return current_user

    return dependency
