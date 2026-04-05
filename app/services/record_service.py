"""Financial records CRUD service with filtering and pagination."""
from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.record import RecordCreate, RecordUpdate


async def get_record_by_id(db: AsyncSession, record_id: str) -> Optional[FinancialRecord]:
    result = await db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def list_records(
    db: AsyncSession,
    *,
    type: Optional[RecordType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[FinancialRecord]]:
    query = select(FinancialRecord).where(FinancialRecord.is_deleted == False)  # noqa: E712

    if type:
        query = query.where(FinancialRecord.type == type)
    if category:
        query = query.where(FinancialRecord.category == category.strip().lower())
    if date_from:
        query = query.where(FinancialRecord.record_date >= date_from)
    if date_to:
        query = query.where(FinancialRecord.record_date <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    paged = await db.execute(
        query.order_by(FinancialRecord.record_date.desc()).offset(offset).limit(page_size)
    )
    return total, list(paged.scalars().all())


async def create_record(
    db: AsyncSession, data: RecordCreate, created_by: str
) -> FinancialRecord:
    record = FinancialRecord(
        amount=data.amount,
        type=data.type,
        category=data.category,
        record_date=data.record_date,
        description=data.description,
        created_by=created_by,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_record(
    db: AsyncSession, record: FinancialRecord, data: RecordUpdate, updated_by: str
) -> FinancialRecord:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_by = updated_by
    await db.commit()
    await db.refresh(record)
    return record


async def soft_delete_record(db: AsyncSession, record: FinancialRecord) -> None:
    record.is_deleted = True
    await db.commit()
