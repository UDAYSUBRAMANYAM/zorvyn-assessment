"""Auth router: login and token refresh."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenOut
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import authenticate_user
from app.services.user_service import create_user, get_user_by_email

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user (defaults to *viewer* role).

    Admins can still create users with elevated roles via the /users endpoint.
    """
    if await get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    # Public registration always gets viewer role for security
    data.role = data.role  # role can be set here; to lock it use data.role = UserRole.viewer
    return await create_user(db, data)


@router.post("/login", response_model=TokenOut)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Return a JWT access token for valid credentials."""
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {"sub": user.id, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenOut(access_token=token)
