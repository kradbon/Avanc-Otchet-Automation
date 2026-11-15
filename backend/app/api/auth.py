from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, get_current_user, verify_password
from app.db.database import get_db, row_to_user
from app.models import UserRecord
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    row = db.execute(
        "SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1",
        (payload.login, payload.login),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль.",
        )

    user = row_to_user(row)
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль.",
        )

    token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=token, user=UserProfile.model_validate(user))


@router.get("/me", response_model=UserProfile)
def me(current_user: UserRecord = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)
