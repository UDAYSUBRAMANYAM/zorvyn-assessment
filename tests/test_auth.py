"""Integration tests for the auth flow."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Admin",
            "password": "securepass123",
            "role": "admin",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "admin"

    # Login
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200, resp.text
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_duplicate_register(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob",
            "password": "securepass123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "full_name": "Bob Again",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
