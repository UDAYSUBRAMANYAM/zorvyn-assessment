"""Pydantic schemas for User endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole, UserStatus


# ── Request schemas ───────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.viewer


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Response schemas ──────────────────────────────────────────────────────────
class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserOut]
