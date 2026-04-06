
"""
Finance Data Processing & Access Control Backend
=================================================
Application entry point. Creates the FastAPI app, registers routers,
attaches middleware, and initialises the database on startup.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, users, records, dashboard
from app.seed import run_seed   # ✅ ADD THIS


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and seed data on startup."""
    await init_db()

    # ✅ AUTO SEED (runs once, skips if data exists)
    await run_seed()

    yield


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance Dashboard API",
    description=(
        "Role-based access control API for managing financial records "
        "with dashboard analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(users.router,     prefix="/api/v1/users",     tags=["Users"])
app.include_router(records.router,   prefix="/api/v1/records",   tags=["Financial Records"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "service": "Finance Dashboard API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    )


@app.get("/api/v1/health", tags=["Health"])
async def health():
    return {"status": "ok", "environment": settings.APP_ENV}

