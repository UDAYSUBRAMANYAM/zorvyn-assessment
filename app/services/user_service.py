"""User CRUD service."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import hash_password


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    *,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[User]]:
    """Return (total_count, page_of_users)."""
    query = select(User).where(User.is_deleted == False)  # noqa: E712
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    paged = await db.execute(query.offset(offset).limit(page_size))
    return total, list(paged.scalars().all())


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role,
        status=UserStatus.active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user: User) -> None:
    user.is_deleted = True
    user.status = UserStatus.inactive
    await db.commit()
