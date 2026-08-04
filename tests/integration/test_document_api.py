"""Integration tests for Document Generation APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from taxos.domain.calculators.schema import CalculatorConfig


@pytest.mark.asyncio
async def test_generate_documents(client: AsyncClient) -> None:
    # Setup mock calculator config (from conftest or create on the fly)
    payload = {
        "format": "json",
        "template_id": "corporate",
        "inputs": {
            "gross_income": 75000,
            "tax_rate": 22
        }
    }
    
    # JSON
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    data = res.json()
    assert "results" in data
    
    # CSV
    payload["format"] = "csv"
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert b"Calculation Report" in res.content
    
    # HTML
    payload["format"] = "html"
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert b"<!DOCTYPE html>" in res.content
    
    # Markdown
    payload["format"] = "markdown"
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200
    assert "text/markdown" in res.headers["content-type"]
    assert b"## Summary" in res.content
    
    # Excel
    payload["format"] = "excel"
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200
    assert "spreadsheetml.sheet" in res.headers["content-type"]
    
    # PDF
    payload["format"] = "pdf"
    res = await client.post("/api/v1/documents/income-tax-calculator/generate", json=payload)
    assert res.status_code == 200, f"PDF generation failed: {res.text}"
    assert "application/pdf" in res.headers["content-type"]
    assert res.content.startswith(b"%PDF")
