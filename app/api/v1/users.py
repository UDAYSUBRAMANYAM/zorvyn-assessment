"""Users router — admin-level user management."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserListOut, UserOut, UserUpdate
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    soft_delete_user,
    update_user,
)

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.get(
    "/",
    response_model=UserListOut,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def list_all_users(
    role: UserRole | None = Query(None),
    status: UserStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional filtering. **Admin only.**"""
    total, users = await list_users(db, role=role, status=status, page=page, page_size=page_size)
    return UserListOut(total=total, page=page, page_size=page_size, items=users)


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def create_new_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a user with any role. **Admin only.**"""
    if await get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return await create_user(db, data)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch a single user by ID. **Admin only.**"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def update_existing_user(
    user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a user's name, role, or status. **Admin only.**"""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await update_user(db, user, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a user. **Admin only.**"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete their own account",
        )
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await soft_delete_user(db, user)
