"""Smoke tests verifying critical module imports and application entry points."""


def test_import_taxos_main():
    """Verify that taxos.main and FastAPI create_app can be imported and initialized."""
    from taxos.main import create_app

    app = create_app()
    assert app is not None
    assert app.title == "TaxOS"


def test_import_api_routers():
    """Verify API v1 router modules are all importable."""
    from taxos.api.v1.router import create_v1_router
    from taxos.core.config import get_settings

    settings = get_settings()
    router = create_v1_router(settings)
    assert router is not None
    assert len(router.routes) > 0


def test_import_core_domain_engines():
    """Verify all domain calculation engines can be imported cleanly."""
    from taxos.domain.catalog.registry import get_catalog_registry
    from taxos.domain.compliance.calendar import IndiaComplianceCalendarEngine
    from taxos.domain.documents.extractor import Form16ExtractionResult
    from taxos.domain.financial.trace import StandardTaxCalculationResponse
    from taxos.domain.global_tax.engine import GlobalTaxEngine
    from taxos.domain.gst.calculator import IndiaGSTEngine
    from taxos.domain.india.advance_tax_interest import IndiaAdvanceTaxEngine
    from taxos.domain.india.capital_gains import IndiaCapitalGainsEngine
    from taxos.domain.india.income_tax import IndiaIncomeTaxEngine
    from taxos.domain.india.salary_ctc import IndiaSalaryEngine
    from taxos.domain.india.tds_tcs import IndiaTDSEngine
    from taxos.domain.reconciliation.engine import ReusableReconciliationEngine

    assert get_catalog_registry() is not None
    assert IndiaIncomeTaxEngine() is not None
    assert IndiaSalaryEngine() is not None
    assert IndiaCapitalGainsEngine() is not None
    assert IndiaAdvanceTaxEngine() is not None
    assert IndiaTDSEngine() is not None
    assert IndiaGSTEngine() is not None
    assert ReusableReconciliationEngine() is not None
    assert GlobalTaxEngine() is not None
    assert IndiaComplianceCalendarEngine() is not None
    assert Form16ExtractionResult is not None
    assert StandardTaxCalculationResponse is not None
