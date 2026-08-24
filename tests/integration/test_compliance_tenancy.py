"""Integration tests verifying multi-tenant isolation and persistence for Compliance Tasks."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.application.iam.auth_service import AuthService
from taxos.application.iam.organization_service import OrganizationService
from taxos.domain.iam.schema import UserCreate, UserLogin


@pytest.mark.asyncio
async def test_compliance_task_organization_isolation(session: AsyncSession, client: AsyncClient):
    """Verify that compliance tasks are strictly isolated by organization tenancy."""
    auth_service = AuthService(session)
    org_service = OrganizationService(session)

    # 1. Create User A and Org 1
    user_a = await auth_service.register_user(
        UserCreate(email="user_a@example.com", password="Password123!")
    )
    org_1 = await org_service.create_organization("Org 1 Tax Consulting", user_a.id)

    # 2. Create User B and Org 2
    user_b = await auth_service.register_user(
        UserCreate(email="user_b@example.com", password="Password123!")
    )
    org_2 = await org_service.create_organization("Org 2 Global Advisory", user_b.id)

    # Generate JWT tokens
    login_a = await auth_service.login_user(
        UserLogin(email="user_a@example.com", password="Password123!")
    )
    assert login_a is not None
    token_a = login_a.access_token

    login_b = await auth_service.login_user(
        UserLogin(email="user_b@example.com", password="Password123!")
    )
    assert login_b is not None
    token_b = login_b.access_token

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": str(org_1.id)}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": str(org_2.id)}

    # User A creates a compliance task in Org 1
    create_resp = await client.post(
        "/api/v1/compliance/tasks",
        json={
            "obligation_id": "itr-individual-non-audit",
            "status": "pending",
            "notes": "User A Private Client Task",
        },
        headers=headers_a,
    )
    assert create_resp.status_code == 201, create_resp.text
    task_data = create_resp.json()
    task_id = task_data["task_id"]
    assert task_data["notes"] == "User A Private Client Task"

    # User A lists tasks -> Sees task
    list_a = await client.get("/api/v1/compliance/tasks", headers=headers_a)
    assert list_a.status_code == 200
    tasks_a = list_a.json()
    assert len(tasks_a) >= 1
    assert any(t["task_id"] == task_id for t in tasks_a)

    # User B lists tasks in Org 2 -> DOES NOT see User A's task
    list_b = await client.get("/api/v1/compliance/tasks", headers=headers_b)
    assert list_b.status_code == 200
    tasks_b = list_b.json()
    assert not any(t["task_id"] == task_id for t in tasks_b)

    # User B tries to update User A's task -> 404 Not Found (isolated)
    patch_b = await client.patch(
        f"/api/v1/compliance/tasks/{task_id}",
        json={"notes": "Hacked Notes"},
        headers=headers_b,
    )
    assert patch_b.status_code == 404

    # User B tries to impersonate Org 1 with header -> 403 Forbidden
    headers_b_impersonate = {
        "Authorization": f"Bearer {token_b}",
        "X-Organization-ID": str(org_1.id),
    }
    impersonate_resp = await client.get("/api/v1/compliance/tasks", headers=headers_b_impersonate)
    assert impersonate_resp.status_code == 403

    # User B tries to delete User A's task -> 404 Not Found
    delete_b = await client.delete(f"/api/v1/compliance/tasks/{task_id}", headers=headers_b)
    assert delete_b.status_code == 404

    # User A can delete their own task -> 204 No Content
    delete_a = await client.delete(f"/api/v1/compliance/tasks/{task_id}", headers=headers_a)
    assert delete_a.status_code == 204
