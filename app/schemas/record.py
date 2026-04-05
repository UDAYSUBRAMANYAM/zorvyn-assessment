"""Pydantic schemas for Financial Record endpoints."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.financial_record import RecordType


# ── Request schemas ───────────────────────────────────────────────────────────
class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be a positive number")
    type: RecordType
    category: str = Field(..., min_length=1, max_length=100)
    record_date: date
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        return v.strip().lower()


class RecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    record_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if v else v


# ── Response schemas ──────────────────────────────────────────────────────────
class RecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    amount: float
    type: RecordType
    category: str
    record_date: date
    description: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class RecordListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RecordOut]
