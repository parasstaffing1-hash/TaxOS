"""Integration tests for Authentication API."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient) -> None:
    # 1. Register
    payload = {
        "email": "test@example.com",
        "password": "securepassword123"
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    
    # 2. Login
    login_data = {
        "username": "test@example.com",
        "password": "securepassword123"
    }
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
    await client.post("/api/v1/auth/register", json={"email": "org_owner@example.com", "password": "pass"})
    res = await client.post("/api/v1/auth/login", data={"username": "org_owner@example.com", "password": "pass"})
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
