"""Integration tests for Taxpayer Profiles and Saved Calculations with Tenancy and Encryption."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.application.iam.auth_service import AuthService
from taxos.application.iam.organization_service import OrganizationService
from taxos.domain.iam.schema import UserCreate, UserLogin


@pytest.mark.asyncio
async def test_taxpayer_profile_and_saved_calculations_flow(
    session: AsyncSession, client: AsyncClient
):
    """Verify taxpayer profile encryption/masking and saved calculations audit trail."""
    auth_service = AuthService(session)
    org_service = OrganizationService(session)

    # 1. Create User A in Org 1
    user_a = await auth_service.register_user(
        UserCreate(email="taxpayer_user_a@example.com", password="Password123!")
    )
    org_1 = await org_service.create_organization("Org 1 Wealth Advisors", user_a.id)

    login_a = await auth_service.login_user(
        UserLogin(email="taxpayer_user_a@example.com", password="Password123!")
    )
    assert login_a is not None
    headers_a = {
        "Authorization": f"Bearer {login_a.access_token}",
        "X-Organization-ID": str(org_1.id),
    }

    # 2. Create User B in Org 2
    user_b = await auth_service.register_user(
        UserCreate(email="taxpayer_user_b@example.com", password="Password123!")
    )
    org_2 = await org_service.create_organization("Org 2 Global Audit", user_b.id)

    login_b = await auth_service.login_user(
        UserLogin(email="taxpayer_user_b@example.com", password="Password123!")
    )
    assert login_b is not None
    headers_b = {
        "Authorization": f"Bearer {login_b.access_token}",
        "X-Organization-ID": str(org_2.id),
    }

    # --- Test Taxpayer Profiles ---
    tp_resp = await client.post(
        "/api/v1/taxpayers",
        json={
            "taxpayer_name": "Rohan Sharma",
            "pan": "ABCDE1234F",
            "gstin": "29ABCDE1234F1Z5",
            "entity_type": "individual",
            "jurisdiction": "IN",
            "residential_status": "resident_ordinarily",
        },
        headers=headers_a,
    )
    assert tp_resp.status_code == 201, tp_resp.text
    tp_data = tp_resp.json()
    tp_id = tp_data["id"]
    assert tp_data["taxpayer_name"] == "Rohan Sharma"
    assert tp_data["pan_masked"] == "ABCDE****F"

    # User A lists taxpayers -> Sees Rohan Sharma
    list_tp = await client.get("/api/v1/taxpayers", headers=headers_a)
    assert list_tp.status_code == 200
    assert any(t["id"] == tp_id for t in list_tp.json())

    # User B lists taxpayers -> DOES NOT see User A's taxpayer
    list_tp_b = await client.get("/api/v1/taxpayers", headers=headers_b)
    assert list_tp_b.status_code == 200
    assert not any(t["id"] == tp_id for t in list_tp_b.json())

    # User B tries to fetch User A's taxpayer -> 404
    get_tp_b = await client.get(f"/api/v1/taxpayers/{tp_id}", headers=headers_b)
    assert get_tp_b.status_code == 404

    # --- Test Saved Calculations ---
    calc_payload = {
        "taxpayer_profile_id": tp_id,
        "tool_id": "india-income-tax-universal",
        "jurisdiction": "IN",
        "financial_year": "2024-25",
        "assessment_year": "2025-26",
        "rule_version": "IN-IT-2025.1",
        "inputs": {"salary_income": 1200000.0},
        "results": {"total_tax_payable": 71500.0, "net_take_home": 1128500.0},
        "trace_steps": [
            {"step": 1, "label": "Standard Deduction", "result": 75000.0},
            {"step": 2, "label": "Taxable Income", "result": 1125000.0},
        ],
        "total_tax_payable": 71500.0,
        "effective_tax_rate": 5.95,
        "is_favourite": False,
    }
    calc_resp = await client.post("/api/v1/calculations", json=calc_payload, headers=headers_a)
    assert calc_resp.status_code == 201, calc_resp.text
    calc_data = calc_resp.json()
    calc_id = calc_data["id"]
    assert calc_data["total_tax_payable"] == 71500.0
    assert calc_data["rule_version"] == "IN-IT-2025.1"
    assert len(calc_data["trace_steps"]) == 2

    # User A lists calculations
    list_calcs_a = await client.get("/api/v1/calculations", headers=headers_a)
    assert list_calcs_a.status_code == 200
    assert any(c["id"] == calc_id for c in list_calcs_a.json())

    # User A toggles favourite
    fav_resp = await client.patch(f"/api/v1/calculations/{calc_id}/favourite", headers=headers_a)
    assert fav_resp.status_code == 200
    assert fav_resp.json()["is_favourite"] is True

    # User B cannot access User A's calculation -> 404
    get_calc_b = await client.get(f"/api/v1/calculations/{calc_id}", headers=headers_b)
    assert get_calc_b.status_code == 404

    # User B cannot delete User A's calculation -> 404
    del_calc_b = await client.delete(f"/api/v1/calculations/{calc_id}", headers=headers_b)
    assert del_calc_b.status_code == 404

    # User A can delete their calculation -> 204
    del_calc_a = await client.delete(f"/api/v1/calculations/{calc_id}", headers=headers_a)
    assert del_calc_a.status_code == 204
