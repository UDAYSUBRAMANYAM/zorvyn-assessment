"""
Async SQLAlchemy engine + session factory.

Supports both SQLite (dev) and PostgreSQL (prod) via the DATABASE_URL setting.
SQLite requires `check_same_thread=False`; that connect arg is injected only
when the URL contains "sqlite".
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables (idempotent). Called on app startup."""
    # Import models so SQLAlchemy registers them before creating tables
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
