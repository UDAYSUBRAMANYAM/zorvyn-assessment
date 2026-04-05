"""Dashboard aggregation service.

All queries run directly against the DB for efficiency instead of
pulling every record into Python and summing in-memory.
"""
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.dashboard import (
    CategorySummary,
    DashboardSummary,
    MonthlyTrend,
    RecentRecord,
)


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummary:
    # ── Totals ────────────────────────────────────────────────────────────────
    base = select(FinancialRecord).where(FinancialRecord.is_deleted == False)  # noqa: E712

    income_q = await db.execute(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(
            FinancialRecord.is_deleted == False,  # noqa: E712
            FinancialRecord.type == RecordType.income,
        )
    )
    expense_q = await db.execute(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(
            FinancialRecord.is_deleted == False,  # noqa: E712
            FinancialRecord.type == RecordType.expense,
        )
    )
    count_q = await db.execute(
        select(func.count(FinancialRecord.id)).where(FinancialRecord.is_deleted == False)  # noqa: E712
    )

    total_income: float = income_q.scalar_one()
    total_expense: float = expense_q.scalar_one()
    record_count: int = count_q.scalar_one()

    # ── Category breakdown ────────────────────────────────────────────────────
    cat_q = await db.execute(
        select(
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )
    category_breakdown = [
        CategorySummary(category=row.category, total=row.total, count=row.count)
        for row in cat_q.all()
    ]

    # ── Monthly trends (last 12 months) ──────────────────────────────────────
    monthly_q = await db.execute(
        select(
            extract("year", FinancialRecord.record_date).label("year"),
            extract("month", FinancialRecord.record_date).label("month"),
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .group_by("year", "month", FinancialRecord.type)
        .order_by("year", "month")
    )

    # Merge income + expense rows into one MonthlyTrend per month
    # key = (year, month)
    trend_map: dict[tuple, dict] = {}
    for row in monthly_q.all():
        key = (int(row.year), int(row.month))
        if key not in trend_map:
            trend_map[key] = {"year": key[0], "month": key[1], "income": 0.0, "expense": 0.0}
        if row.type == RecordType.income:
            trend_map[key]["income"] += row.total
        else:
            trend_map[key]["expense"] += row.total

    monthly_trends = [
        MonthlyTrend(
            year=v["year"],
            month=v["month"],
            income=v["income"],
            expense=v["expense"],
            net=v["income"] - v["expense"],
        )
        for v in sorted(trend_map.values(), key=lambda x: (x["year"], x["month"]))
    ]

    # ── Recent records (last 10) ──────────────────────────────────────────────
    recent_q = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .order_by(FinancialRecord.record_date.desc(), FinancialRecord.created_at.desc())
        .limit(10)
    )
    recent_records = [
        RecentRecord(
            id=r.id,
            amount=r.amount,
            type=r.type.value,
            category=r.category,
            record_date=str(r.record_date),
            description=r.description,
        )
        for r in recent_q.scalars().all()
    ]

    return DashboardSummary(
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        net_balance=round(total_income - total_expense, 2),
        record_count=record_count,
        category_breakdown=category_breakdown,
        monthly_trends=monthly_trends,
        recent_records=recent_records,
    )
