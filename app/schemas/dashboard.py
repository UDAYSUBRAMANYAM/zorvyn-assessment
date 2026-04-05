"""Pydantic schemas for Dashboard summary endpoints."""
from typing import Optional

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float


class RecentRecord(BaseModel):
    id: str
    amount: float
    type: str
    category: str
    record_date: str
    description: Optional[str]


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    record_count: int
    category_breakdown: list[CategorySummary]
    monthly_trends: list[MonthlyTrend]
    recent_records: list[RecentRecord]
