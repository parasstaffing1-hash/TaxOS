"""Unit tests for specialized India tax domain engines."""

from __future__ import annotations

from decimal import Decimal

from taxos.domain.india.business_tax import (
    BusinessTaxInputs,
    IndiaBusinessTaxEngine,
    PresumptiveSchemeType,
)
from taxos.domain.india.corporate_and_entity import (
    EntityTaxInputs,
    EntityType,
    IndiaEntityTaxEngine,
)
from taxos.domain.india.deductions import (
    ChapterVIAInputs,
    IndiaDeductionEngine,
)
from taxos.domain.india.house_property import (
    HousePropertyInputs,
    IndiaHousePropertyEngine,
    PropertyOccupancyType,
)
from taxos.domain.india.tcs_engine import (
    IndiaTCSEngine,
    TCSCategory,
    TCSInputs,
)


def test_chapter_via_deductions_engine():
    engine = IndiaDeductionEngine()
    inputs = ChapterVIAInputs(
        sec_80c_epf_ppf_elss_lic_tuition=Decimal("180000.00"),  # > 1.5L cap
        sec_80ccd1b_nps_additional=Decimal("60000.00"),  # > 50k cap
        sec_80d_self_family_premium=Decimal("30000.00"),  # 25k cap non-senior
        is_self_senior_citizen=False,
        sec_80d_parents_premium=Decimal("60000.00"),  # 50k cap senior
        are_parents_senior_citizens=True,
        sec_80d_preventive_checkup=Decimal("5000.00"),
        sec_80e_education_loan_interest=Decimal("45000.00"),  # fully allowed
        sec_80tta_savings_interest=Decimal("15000.00"),  # 10k cap
    )
    result, trace = engine.calculate_deductions(inputs)

    # 80CCE cap = 1.5L
    assert result.breakdown_by_section["80C_80CCC_80CCD1"] == Decimal("150000.00")
    # 80CCD(1B) cap = 50k
    assert result.breakdown_by_section["80CCD_1B"] == Decimal("50000.00")
    # 80D self (25k max including checkup) + parents (50k max) = 75k
    assert result.breakdown_by_section["80D"] == Decimal("75000.00")
    # 80E = 45k
    assert result.breakdown_by_section["80E"] == Decimal("45000.00")
    # 80TTA = 10k
    assert result.breakdown_by_section["80TTA"] == Decimal("10000.00")

    # Total = 150k + 50k + 75k + 45k + 10k = 330,000
    assert result.total_deductions_allowed == Decimal("330000.00")
    assert len(trace.steps) >= 5


def test_house_property_self_occupied_and_let_out():
    engine = IndiaHousePropertyEngine()

    # 1. Self-Occupied
    self_inp = HousePropertyInputs(
        occupancy_type=PropertyOccupancyType.SELF_OCCUPIED,
        home_loan_interest_annual=Decimal("250000.00"),  # > 2L cap
    )
    res_self, _ = engine.calculate_property_income(self_inp)
    assert res_self.gross_annual_value == Decimal("0.00")
    assert res_self.net_annual_value == Decimal("0.00")
    assert res_self.section_24b_interest_deduction == Decimal("200000.00")
    assert res_self.net_income_or_loss_house_property == Decimal("-200000.00")

    # 2. Let-Out
    let_inp = HousePropertyInputs(
        occupancy_type=PropertyOccupancyType.LET_OUT,
        actual_rent_received_annual=Decimal("600000.00"),
        municipal_taxes_paid_by_owner=Decimal("40000.00"),
        home_loan_interest_annual=Decimal("150000.00"),
    )
    res_let, _ = engine.calculate_property_income(let_inp)
    assert res_let.gross_annual_value == Decimal("600000.00")
    assert res_let.net_annual_value == Decimal("560000.00")
    # Standard deduction 30% of 560,000 = 168,000
    assert res_let.section_24a_standard_deduction == Decimal("168000.00")
    # Net income = 560,000 - 168,000 - 150,000 = 242,000
    assert res_let.net_income_or_loss_house_property == Decimal("242000.00")


def test_presumptive_business_tax_engine():
    engine = IndiaBusinessTaxEngine()

    # 44AD with 95%+ digital
    inp_44ad = BusinessTaxInputs(
        scheme_type=PresumptiveSchemeType.SEC_44AD_BUSINESS,
        gross_turnover_digital=Decimal("20000000.00"),  # 2 Cr digital
        gross_turnover_cash=Decimal("500000.00"),  # 5 Lakh cash
    )
    res_44ad, _ = engine.calculate_business_tax(inp_44ad)
    assert res_44ad.is_eligible_for_presumptive is True
    # 6% of 2 Cr = 12 Lakh, 8% of 5 Lakh = 40,000 -> Total = 12,40,000
    assert res_44ad.statutory_minimum_presumptive_profit == Decimal("1240000.00")
    assert res_44ad.taxable_business_profit == Decimal("1240000.00")
    assert res_44ad.tax_audit_required_sec_44ab is False

    # 44ADA Professional
    inp_44ada = BusinessTaxInputs(
        scheme_type=PresumptiveSchemeType.SEC_44ADA_PROFESSION,
        gross_turnover_digital=Decimal("4000000.00"),
    )
    res_44ada, _ = engine.calculate_business_tax(inp_44ada)
    # 50% of 40 Lakh = 20 Lakh
    assert res_44ada.statutory_minimum_presumptive_profit == Decimal("2000000.00")


def test_tcs_engine_calculations():
    engine = IndiaTCSEngine()

    # Motor vehicle > 10L (1%)
    car_inp = TCSInputs(
        category=TCSCategory.MOTOR_VEHICLE_1F,
        transaction_amount=Decimal("1500000.00"),
        has_valid_pan=True,
    )
    car_res, _ = engine.calculate_tcs(car_inp)
    assert car_res.tcs_amount == Decimal("15000.00")
    assert car_res.is_penalty_rate_applied_206cc is False

    # LRS Overseas Tour Package (5% on first 7L, 20% above 7L)
    tour_inp = TCSInputs(
        category=TCSCategory.LRS_OVERSEAS_TOUR_PACKAGE,
        transaction_amount=Decimal("1000000.00"),
        cumulative_amount_financial_year=Decimal("0.00"),
    )
    tour_res, _ = engine.calculate_tcs(tour_inp)
    # (700,000 * 5%) + (300,000 * 20%) = 35,000 + 60,000 = 95,000
    assert tour_res.tcs_amount == Decimal("95000.00")


def test_corporate_and_entity_tax_engine():
    engine = IndiaEntityTaxEngine()

    # Domestic company u/s 115BAA (22% base + 10% surcharge + 4% cess)
    corp_inp = EntityTaxInputs(
        entity_type=EntityType.DOMESTIC_COMPANY_115BAA,
        taxable_income=Decimal("10000000.00"),  # 1 Crore
    )
    corp_res, _ = engine.calculate_entity_tax(corp_inp)
    # Base = 22 Lakh, Surcharge 10% = 2.2 Lakh, Subtotal = 24.2 Lakh, Cess 4% = 96,800 -> Total = 25,16,800
    assert corp_res.total_normal_tax_liability == Decimal("2516800.00")
    assert corp_res.final_tax_payable == Decimal("2516800.00")
