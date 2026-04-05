"""Integration tests for financial records and RBAC."""
import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient, email: str, role: str = "viewer") -> str:
    """Register + login a user, return the JWT."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "pass12345", "role": role},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "pass12345"}
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_can_create_record(client: AsyncClient):
    token = await _get_token(client, "admin_rec@example.com", "admin")
    resp = await client.post(
        "/api/v1/records/",
        json={
            "amount": 5000.0,
            "type": "income",
            "category": "salary",
            "record_date": "2024-01-15",
            "description": "January salary",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["amount"] == 5000.0
    assert data["category"] == "salary"


@pytest.mark.asyncio
async def test_viewer_cannot_create_record(client: AsyncClient):
    token = await _get_token(client, "viewer_rec@example.com", "viewer")
    resp = await client.post(
        "/api/v1/records/",
        json={
            "amount": 100.0,
            "type": "expense",
            "category": "food",
            "record_date": "2024-01-20",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_read_records(client: AsyncClient):
    token = await _get_token(client, "viewer_read@example.com", "viewer")
    resp = await client.get(
        "/api/v1/records/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_analyst_can_access_dashboard(client: AsyncClient):
    token = await _get_token(client, "analyst_dash@example.com", "analyst")
    resp = await client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "total_income" in body
    assert "net_balance" in body


@pytest.mark.asyncio
async def test_viewer_cannot_access_dashboard(client: AsyncClient):
    token = await _get_token(client, "viewer_dash@example.com", "viewer")
    resp = await client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_record_filter_by_type(client: AsyncClient):
    admin_token = await _get_token(client, "admin_filter@example.com", "admin")
    # Create expense record
    await client.post(
        "/api/v1/records/",
        json={"amount": 200.0, "type": "expense", "category": "utilities", "record_date": "2024-02-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = await client.get(
        "/api/v1/records/?type=expense",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["type"] == "expense"


@pytest.mark.asyncio
async def test_invalid_amount_rejected(client: AsyncClient):
    token = await _get_token(client, "admin_val@example.com", "admin")
    resp = await client.post(
        "/api/v1/records/",
        json={"amount": -50.0, "type": "income", "category": "test", "record_date": "2024-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    resp = await client.get("/api/v1/records/")
    assert resp.status_code == 403
