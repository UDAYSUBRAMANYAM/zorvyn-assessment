"""Auth service: password hashing and user authentication.

Uses bcrypt directly (bypassing passlib) to avoid the passlib 1.7.x /
bcrypt 4.x incompatibility where passlib's wrap-bug detection tries to
hash 255-byte secrets and fails.
"""
from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserStatus

# bcrypt max effective secret length
_BCRYPT_MAX = 72


def _encode(plain: str) -> bytes:
    """Encode and hard-truncate to bcrypt's 72-byte limit."""
    return plain.encode("utf-8")[:_BCRYPT_MAX]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_encode(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Return the active User if credentials are valid, else None."""
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if not user:
        return None
    if user.status == UserStatus.inactive:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
