"""Unit tests for India Salary & HRA Exemption Engine."""

from decimal import Decimal

from taxos.domain.india.models import SalaryStructureInput
from taxos.domain.india.salary_ctc import IndiaSalaryEngine


def test_hra_exemption_calculation():
    """Verify Section 10(13A) rule 2A calculation for Metro city."""
    engine = IndiaSalaryEngine()
    # Basic = ₹6,00,000 (₹50k/mo), HRA = ₹3,00,000 (₹25k/mo), Rent = ₹2,40,000 (₹20k/mo) in Metro
    # 1. Actual HRA = ₹3,00,000
    # 2. Rent - 10% Basic = 2,40,000 - 60,000 = ₹1,80,000
    # 3. 50% Basic = ₹3,00,000
    # Exemption = Min(300k, 180k, 300k) = ₹1,80,000
    res = engine.calculate_hra_exemption(
        basic_salary=Decimal("600000.0"),
        hra_received=Decimal("300000.0"),
        annual_rent_paid=Decimal("240000.0"),
        is_metro=True,
    )
    assert res.exempt_hra_amount == Decimal("180000.0")
    assert res.taxable_hra_amount == Decimal("120000.0")


def test_ctc_to_take_home():
    """Verify CTC to Take-home salary breakdown."""
    engine = IndiaSalaryEngine()
    salary_input = SalaryStructureInput(
        annual_ctc=Decimal("1200000.0"),
        basic_percentage=Decimal("0.40"),
        hra_percentage=Decimal("0.20"),
        actual_rent_paid_annually=Decimal("180000.0"),
    )
    breakdown = engine.calculate_take_home(salary_input)

    assert breakdown.annual_ctc == Decimal("1200000.0")
    assert breakdown.basic_salary == Decimal("480000.0")
    assert breakdown.employee_epf > 0
    assert breakdown.monthly_take_home > Decimal("50000.0")
