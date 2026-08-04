"""Integration tests for Authentication API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient) -> None:
    # 1. Register
    payload = {"email": "test@example.com", "password": "securepassword123"}
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # 2. Login
    login_data = {"username": "test@example.com", "password": "securepassword123"}
    # OAuth2PasswordRequestForm expects form data, not json
    res = await client.post("/api/v1/auth/login", data=login_data)
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Get Me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    me_data = res.json()
    assert me_data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_create_organization(client: AsyncClient) -> None:
    # Register and login first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "org_owner@example.com", "password": "securepassword123"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "org_owner@example.com", "password": "securepassword123"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create org
    res = await client.post("/api/v1/organizations", json={"name": "Acme Corp"}, headers=headers)
    assert res.status_code == 201
    org_data = res.json()
    assert org_data["name"] == "Acme Corp"

    # List orgs
    res = await client.get("/api/v1/organizations", headers=headers)
    assert res.status_code == 200
    orgs = res.json()
    assert len(orgs) == 1
    assert orgs[0]["name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_browser_cookie_session_and_admin_guard(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "browser_session@example.com", "password": "securepassword123"},
    )

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "browser_session@example.com", "password": "securepassword123"},
    )
    assert login.status_code == 200
    assert "taxos_access_token" in login.headers["set-cookie"]

    # A browser session uses the HttpOnly cookie instead of exposing the JWT to JavaScript.
    current_user = await client.get("/api/v1/auth/me")
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "browser_session@example.com"

    # Authenticated users still cannot mutate public calculator configuration.
    rejected_mutation = await client.delete("/api/v1/dynamic-calculators/income-tax-calculator")
    assert rejected_mutation.status_code == 403

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert "taxos_access_token" in logout.headers["set-cookie"]

    unauthenticated = await client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 401
