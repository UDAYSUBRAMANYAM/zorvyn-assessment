"""Financial records router with role-based access control.

Permissions
-----------
- viewer   : GET /records, GET /records/{id}
- analyst  : viewer + access to dashboard (see dashboard router)
- admin    : full CRUD
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.financial_record import RecordType
from app.models.user import User, UserRole
from app.schemas.record import RecordCreate, RecordListOut, RecordOut, RecordUpdate
from app.services.record_service import (
    create_record,
    get_record_by_id,
    list_records,
    soft_delete_record,
    update_record,
)

router = APIRouter()

_READ_ROLES = (UserRole.viewer, UserRole.analyst, UserRole.admin)
_WRITE_ROLES = (UserRole.admin,)


@router.get("/", response_model=RecordListOut)
async def list_financial_records(
    type: Optional[RecordType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*_READ_ROLES)),
):
    """
    List financial records with optional filters.

    **Accessible by:** viewer, analyst, admin
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`date_from` must be before or equal to `date_to`",
        )
    total, records = await list_records(
        db,
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return RecordListOut(total=total, page=page, page_size=page_size, items=records)


@router.get("/{record_id}", response_model=RecordOut)
async def get_financial_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*_READ_ROLES)),
):
    """Get a single record by ID. **Accessible by:** viewer, analyst, admin"""
    record = await get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.post("/", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
async def create_financial_record(
    data: RecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
):
    """Create a new financial record. **Admin only.**"""
    return await create_record(db, data, current_user.id)


@router.patch("/{record_id}", response_model=RecordOut)
async def update_financial_record(
    record_id: str,
    data: RecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
):
    """Update an existing record. **Admin only.**"""
    record = await get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return await update_record(db, record, data, current_user.id)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_financial_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*_WRITE_ROLES)),
):
    """Soft-delete a financial record. **Admin only.**"""
    record = await get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    await soft_delete_record(db, record)
