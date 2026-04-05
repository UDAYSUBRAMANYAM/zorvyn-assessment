"""
FastAPI dependencies for authentication and role-based access control.

Usage
-----
    from app.dependencies.auth import get_current_user, require_roles

    @router.get("/secret")
    async def secret(user: User = Depends(require_roles(UserRole.admin))):
        ...
"""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.services.user_service import get_user_by_id
from sqlalchemy.ext.asyncio import AsyncSession

_bearer = HTTPBearer(auto_error=True)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer token and return the corresponding User."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _CREDENTIALS_EXCEPTION

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    if user.status == UserStatus.inactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


def require_roles(*roles: UserRole) -> Callable:
    """
    Return a FastAPI dependency that ensures the current user
    has one of the specified roles.

    Example::

        @router.delete("/{id}")
        async def delete(user = Depends(require_roles(UserRole.admin))):
            ...
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{[r.value for r in roles]}"
                ),
            )
        return current_user

    return _check
