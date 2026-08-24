"""Integration tests for India Tax, GST, Catalog, and Global API endpoints."""

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from taxos.main import create_app


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.mark.asyncio
async def test_api_catalog_list_and_stats(app):
    """Verify /api/v1/catalog and /api/v1/catalog/stats endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/catalog")
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0

        stats_res = await client.get("/api/v1/catalog/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_tools"] == 845
        assert stats["catalog_target"] == 845
        assert stats["complete_tools"] == 845
        assert stats["not_started_tools"] == 0
        assert stats["partial_tools"] == 0

        family_res = await client.get("/api/v1/catalog/families")
        assert family_res.status_code == 200
        assert any(item["family"] == "india_income_tax" for item in family_res.json())


@pytest.mark.asyncio
async def test_api_india_income_tax_calculate(app):
    """Verify /api/v1/india/income-tax/calculate-new-regime."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "salary_income": "775000.0",
            "assessment_year": "2025-26",
            "financial_year": "2024-25",
        }
        res = await client.post("/api/v1/india/income-tax/calculate-new-regime", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["jurisdiction"] == "IN"
        assert Decimal(str(data["calculation"]["total_tax_liability"])) == Decimal("0.0")


@pytest.mark.asyncio
async def test_api_gst_calculate_exclusive(app):
    """Verify /api/v1/gst/calculate-exclusive."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "taxable_value": "10000.0",
            "gst_rate": "0.18",
            "supply_type": "intra_state",
        }
        res = await client.post("/api/v1/gst/calculate-exclusive", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert Decimal(str(data["cgst_amount"])) == Decimal("900.0")
        assert Decimal(str(data["sgst_amount"])) == Decimal("900.0")
        assert Decimal(str(data["gross_invoice_amount"])) == Decimal("11800.0")


@pytest.mark.asyncio
async def test_api_gstin_validate(app):
    """Verify /api/v1/gst/validate-gstin."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/gst/validate-gstin", json={"gstin": "27AAAAA0000A1Z5"})
        assert res.status_code == 200
        data = res.json()
        assert data["state_code"] == "27"
        assert data["state_name"] == "Maharashtra"


@pytest.mark.asyncio
async def test_api_global_tax_calculate(app):
    """Verify /api/v1/global/calculate."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "country_code": "GB",
            "gross_income_or_revenue": "1000.0",
            "tax_type": "vat_gst",
        }
        res = await client.post("/api/v1/global/calculate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert Decimal(str(data["calculated_tax"])) == Decimal("200.0")


@pytest.mark.asyncio
async def test_api_document_extracts_reviewable_csv_fields(app):
    """CSV ingestion returns checksum, fields, and an explicit review state."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/documents/extract",
            files={"file": ("form16.csv", b"PAN,Gross Salary\nABCDE1234F,775000\n", "text/csv")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["document_type"] == "form_16"
        assert data["source_checksum_sha256"]
        assert data["review_required"] is True
        assert data["row_count"] == 1


@pytest.mark.asyncio
async def test_api_compliance_due_date_and_task_tracking(session, client):
    """Compliance dates resolve from the assessment year and can be tracked."""
    from taxos.application.iam.auth_service import AuthService
    from taxos.domain.iam.schema import UserCreate, UserLogin

    auth_service = AuthService(session)
    await auth_service.register_user(
        UserCreate(email="compliance_tester@example.com", password="Password123!")
    )
    login_res = await auth_service.login_user(
        UserLogin(email="compliance_tester@example.com", password="Password123!")
    )
    assert login_res is not None
    headers = {"Authorization": f"Bearer {login_res.access_token}"}

    obligations = await client.get("/api/v1/compliance/obligations?assessment_year=2025-26")
    assert obligations.status_code == 200
    itr = next(
        item for item in obligations.json() if item["obligation_id"] == "itr-individual-non-audit"
    )
    assert itr["resolved_due_date"] == "2025-07-31"

    task = await client.post(
        "/api/v1/compliance/tasks",
        json={"obligation_id": "itr-individual-non-audit", "status": "pending"},
        headers=headers,
    )
    assert task.status_code == 201
    task_id = task.json()["task_id"]
    updated = await client.patch(
        f"/api/v1/compliance/tasks/{task_id}",
        json={"status": "filed_on_time"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "filed_on_time"
