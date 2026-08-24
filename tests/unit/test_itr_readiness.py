"""Unit tests for ITR Form Eligibility and Pre-Filing Defect Risk Checker."""

from decimal import Decimal

from taxos.domain.india.itr_readiness import (
    IndiaITRReadinessEngine,
    ITRForm,
    TaxpayerProfileInput,
)


def test_itr_1_sahaj_eligibility_simple_salaried():
    """Verify standard salaried individual with income <= 50L qualifies for ITR-1 Sahaj."""
    engine = IndiaITRReadinessEngine()
    profile = TaxpayerProfileInput(
        is_resident=True,
        total_gross_income=Decimal("1500000.0"),
        has_salary_income=True,
        house_properties_count=1,
        has_capital_gains=False,
        has_business_or_professional_income=False,
    )
    report = engine.evaluate_readiness(profile)
    assert report.recommended_form == ITRForm.ITR_1_SAHAJ
    assert report.is_filing_ready
    assert len(report.blocking_defects) == 0


def test_itr_2_eligibility_for_capital_gains_or_foreign_assets():
    """Verify individual with capital gains or foreign assets must file ITR-2."""
    engine = IndiaITRReadinessEngine()
    profile = TaxpayerProfileInput(
        is_resident=True,
        total_gross_income=Decimal("2500000.0"),
        has_salary_income=True,
        has_capital_gains=True,
        has_foreign_assets_or_foreign_income=True,
    )
    report = engine.evaluate_readiness(profile)
    assert report.recommended_form == ITRForm.ITR_2
    assert "Schedule FA (Foreign Assets Disclosure)" in report.statutory_mandatory_schedules
    assert len(report.compliance_warnings) > 0


def test_itr_4_sugam_for_presumptive_business():
    """Verify individual with 44AD/44ADA business under 50L qualifies for ITR-4 Sugam."""
    engine = IndiaITRReadinessEngine()
    profile = TaxpayerProfileInput(
        is_resident=True,
        total_gross_income=Decimal("3000000.0"),
        has_business_or_professional_income=True,
        is_presumptive_business_44ad_44ada=True,
    )
    report = engine.evaluate_readiness(profile)
    assert report.recommended_form == ITRForm.ITR_4_SUGAM


def test_itr_6_for_companies():
    """Verify company taxpayer must file ITR-6."""
    engine = IndiaITRReadinessEngine()
    profile = TaxpayerProfileInput(
        is_company=True,
        is_individual_or_huf=False,
        total_gross_income=Decimal("50000000.0"),
    )
    report = engine.evaluate_readiness(profile)
    assert report.recommended_form == ITRForm.ITR_6
    assert "Schedule MAT/115JB" in report.statutory_mandatory_schedules
