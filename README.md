# Finance Data Processing & Access Control Backend

A production-grade REST API built with **FastAPI**, **SQLAlchemy 2.0 async**, **SQLite / PostgreSQL**, and **JWT authentication** for a role-based finance dashboard system.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Roles & Permissions](#roles--permissions)
5. [API Reference](#api-reference)
6. [Setup & Running](#setup--running)
7. [Running Tests](#running-tests)
8. [Database](#database)
9. [Design Decisions & Assumptions](#design-decisions--assumptions)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│              FastAPI Application (main.py)                 │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ /auth    │  │ /users   │  │ /records │  │/dashboard│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │              │        │
│  ┌────▼─────────────▼──────────────▼──────────────▼─────┐  │
│  │         Dependencies (JWT validation + RBAC)          │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │   Services  (auth_service, user_service,              │ │
│  │              record_service, dashboard_service)        │ │
│  └────────────────────────┬──────────────────────────────┘ │
│                           │                                │
│  ┌────────────────────────▼──────────────────────────────┐ │
│  │   SQLAlchemy Async ORM  →  SQLite (dev) / PostgreSQL  │ │
│  └───────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

The backend follows a **layered architecture**:

| Layer | Responsibility |
|---|---|
| **Routers** (`app/api/v1/`) | HTTP interface — routes, request parsing, response shaping |
| **Dependencies** (`app/dependencies/`) | JWT auth validation, role-based access guards |
| **Services** (`app/services/`) | Business logic — CRUD, aggregations, auth |
| **Models** (`app/models/`) | SQLAlchemy ORM table definitions |
| **Schemas** (`app/schemas/`) | Pydantic request/response models + validation |
| **Core** (`app/core/`) | Config, DB engine, JWT utilities |

---

## Technology Stack

| Component | Library |
|---|---|
| Web framework | FastAPI 0.111 |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Database (dev) | SQLite via `aiosqlite` |
| Database (prod) | PostgreSQL via `asyncpg` |
| Migrations | Alembic |
| Auth | JWT via `python-jose` |
| Password hashing | `bcrypt` |
| Runtime env | Python `venv` |
| Testing | pytest + pytest-asyncio + HTTPX |
| Validation | Pydantic v2 |
| Config | pydantic-settings (`.env` file) |

---

## Project Structure

```
zorvyn/
├── main.py                     # App factory, router registration
├── seed.py                     # Database seeder (demo data)
├── pytest.ini
├── requirements.txt
├── .env                        # Local secrets (not committed)
├── .env.example                # Template
│
├── app/
│   ├── core/
│   │   ├── config.py           # Settings from env vars
│   │   ├── database.py         # Async engine, session, Base, init_db
│   │   └── security.py         # JWT create/decode
│   │
│   ├── models/
│   │   ├── user.py             # User ORM model (UserRole, UserStatus enums)
│   │   └── financial_record.py # FinancialRecord ORM model (RecordType enum)
│   │
│   ├── schemas/
│   │   ├── auth.py             # LoginRequest, TokenOut
│   │   ├── user.py             # UserCreate, UserUpdate, UserOut, UserListOut
│   │   ├── record.py           # RecordCreate, RecordUpdate, RecordOut, RecordListOut
│   │   └── dashboard.py        # DashboardSummary, CategorySummary, MonthlyTrend
│   │
│   ├── services/
│   │   ├── auth_service.py     # hash_password, verify_password, authenticate_user
│   │   ├── user_service.py     # User CRUD + pagination
│   │   ├── record_service.py   # FinancialRecord CRUD + filtering + pagination
│   │   └── dashboard_service.py# SQL aggregations for dashboard
│   │
│   ├── dependencies/
│   │   └── auth.py             # get_current_user(), require_roles() factory
│   │
│   └── api/v1/
│       ├── auth.py             # POST /register, POST /login
│       ├── users.py            # CRUD /users/*
│       ├── records.py          # CRUD /records/*
│       └── dashboard.py        # GET /dashboard/summary
│
└── tests/
    ├── conftest.py             # In-memory SQLite + async HTTPX client fixtures
    ├── test_auth.py            # Auth flow tests
    └── test_records.py         # RBAC + record operation tests
```

---

## Roles & Permissions

| Endpoint | viewer | analyst | admin |
|---|:---:|:---:|:---:|
| `POST /auth/register` | ✅ | ✅ | ✅ |
| `POST /auth/login` | ✅ | ✅ | ✅ |
| `GET /users/me` | ✅ | ✅ | ✅ |
| `GET /users/` | ❌ | ❌ | ✅ |
| `POST /users/` | ❌ | ❌ | ✅ |
| `PATCH /users/{id}` | ❌ | ❌ | ✅ |
| `DELETE /users/{id}` | ❌ | ❌ | ✅ |
| `GET /records/` | ✅ | ✅ | ✅ |
| `GET /records/{id}` | ✅ | ✅ | ✅ |
| `POST /records/` | ❌ | ❌ | ✅ |
| `PATCH /records/{id}` | ❌ | ❌ | ✅ |
| `DELETE /records/{id}` | ❌ | ❌ | ✅ |
| `GET /dashboard/summary` | ❌ | ✅ | ✅ |

Access control is enforced per-route using the `require_roles()` dependency factory in `app/dependencies/auth.py`.

---

## API Reference

### Auth

| Method | URL | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user | None |
| POST | `/api/v1/auth/login` | Get JWT token | None |

**Register body:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepass123",
  "role": "viewer"
}
```

**Login body:**
```json
{ "email": "user@example.com", "password": "securepass123" }
```

**Login response:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### Users (Admin only)

| Method | URL | Description |
|---|---|---|
| GET | `/api/v1/users/me` | My profile (all roles) |
| GET | `/api/v1/users/` | List users (`?role=admin&status=active&page=1&page_size=20`) |
| POST | `/api/v1/users/` | Create user |
| GET | `/api/v1/users/{id}` | Get user |
| PATCH | `/api/v1/users/{id}` | Update user role/status/name |
| DELETE | `/api/v1/users/{id}` | Soft-delete user |

---

### Financial Records

| Method | URL | Description |
|---|---|---|
| GET | `/api/v1/records/` | List records with filters |
| GET | `/api/v1/records/{id}` | Get single record |
| POST | `/api/v1/records/` | Create record (admin) |
| PATCH | `/api/v1/records/{id}` | Update record (admin) |
| DELETE | `/api/v1/records/{id}` | Soft-delete record (admin) |

**Filter query params for GET /records/:**
- `type` — `income` or `expense`
- `category` — string (case-insensitive)
- `date_from` — `YYYY-MM-DD`
- `date_to` — `YYYY-MM-DD`
- `page` — default 1
- `page_size` — default 20, max 100

**Create record body:**
```json
{
  "amount": 5000.00,
  "type": "income",
  "category": "salary",
  "record_date": "2024-01-15",
  "description": "January salary"
}
```

---

### Dashboard

| Method | URL | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary` | Full summary | analyst, admin |

**Response:**
```json
{
  "total_income": 101636.76,
  "total_expense": 111186.13,
  "net_balance": -9549.37,
  "record_count": 30,
  "category_breakdown": [
    { "category": "food", "total": 31184.85, "count": 5 }
  ],
  "monthly_trends": [
    { "year": 2024, "month": 1, "income": 12000, "expense": 3500, "net": 8500 }
  ],
  "recent_records": [ ... ]
}
```

---

## Setup & Running

### Prerequisites

- Python 3.11+

### Quick Start

```bash
# 1. Clone / enter directory
cd zorvyn

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (already done — .env exists in dev)
# For production: copy .env.example → .env and update values

# 5. Seed with demo data (creates finance.db + demo users)
python seed.py

# 6. Start the server
uvicorn main:app --reload

# API is live at http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

### Demo Credentials (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@123456 |
| Analyst | analyst@example.com | Analyst@123 |
| Viewer | viewer@example.com | Viewer@1234 |

### Switching to PostgreSQL

Change `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/finance_db
```

Install the driver:
```bash
pip install asyncpg
```

Run Alembic migrations (or let the app auto-create tables on startup):
```bash
alembic upgrade head
```

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

Tests use an **in-memory SQLite database** and an async HTTPX test client — no external services needed.

**Test coverage:**
- Auth: register, duplicate detection, wrong password
- RBAC: viewer blocked from writes, viewer blocked from dashboard
- Records: admin create, filter by type, invalid amount rejection
- Auth: unauthenticated request rejection

---

## Database

### Schema

**`users` table**

| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(36) | UUID primary key |
| email | VARCHAR(255) | Unique, indexed |
| full_name | VARCHAR(255) | |
| hashed_password | VARCHAR(255) | bcrypt hash |
| role | ENUM | viewer / analyst / admin |
| status | ENUM | active / inactive |
| is_deleted | BOOLEAN | Soft delete flag |
| created_at | DATETIME | UTC |
| updated_at | DATETIME | UTC, auto-updated |

**`financial_records` table**

| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(36) | UUID primary key |
| amount | FLOAT | Must be > 0 |
| type | ENUM | income / expense |
| category | VARCHAR(100) | Indexed, lowercase-normalised |
| record_date | DATE | Indexed |
| description | TEXT | Optional |
| is_deleted | BOOLEAN | Soft delete flag, indexed |
| created_by | VARCHAR(36) | FK → users.id |
| updated_by | VARCHAR(36) | Nullable audit field |
| created_at | DATETIME | UTC |
| updated_at | DATETIME | UTC, auto-updated |

---

## Design Decisions & Assumptions

### Soft Deletes
Both users and financial records use soft deletes (`is_deleted = True`) instead of hard deletes. This preserves audit history and allows recovery. All service queries filter `is_deleted == False`.

### Category Normalisation
All categories are stored lowercased and stripped of whitespace (enforced via a Pydantic validator). This prevents duplicates like `"Food"` vs `"food"`.

### Role-Based Access Control
RBAC is implemented via the `require_roles()` factory dependency. This returns a FastAPI dependency closure that checks the current user's role against a whitelist. It cleanly separates auth concerns from business logic.

### Password Hashing
`passlib` 1.7.x is incompatible with `bcrypt` 4.x (wrap-bug detection with 255-byte secrets fails). The service uses `bcrypt` directly and truncates passwords to 72 bytes before hashing — bcrypt's documented effective limit.

### Async Throughout
All DB operations, route handlers, and service functions are `async`. This maximises throughput under concurrent load, especially important for I/O-bound database operations.

### SQLite Dev / PostgreSQL Prod
The `DATABASE_URL` env var controls the backend. SQLite is used by default for zero-setup local development. Switching to PostgreSQL is one environment variable change.

### Pagination
All list endpoints return `{ total, page, page_size, items }` so clients can build pagination UIs without additional requests.

### Assumptions
- Email is the unique identifier for users (no username field).
- The `viewer` role can self-register; Admin creates analyst/admin accounts via `/users/`.
- Financial amounts are stored as `FLOAT`. For production finance systems, `DECIMAL` precision should be used.
- No rate limiting is implemented (noted as an optional enhancement).
