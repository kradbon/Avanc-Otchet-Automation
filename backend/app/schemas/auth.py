from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models import UserRole


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: str
    role: UserRole
    position: str
    department: str
    created_at: datetime


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, validation_alias=AliasChoices("login", "email", "username"))
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
