"""Unit tests for Pydantic financial validators."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from taxos.domain.financial.validation import (
    DemographicProfile,
    IncomeProfile,
    LocationProfile,
)
from taxos.domain.rules import FilingStatus


class TestIncomeValidation:
    """Test income parsing and sanitization."""

    def test_clean_string_parsing(self) -> None:
        """Test sanitization of common financial strings."""
        # Clean USD strings
        profile1 = IncomeProfile(gross_income="$1,234.56")
        assert profile1.gross_income == Decimal("1234.56")

        # Clean strings with spaces and weird currencies
        profile2 = IncomeProfile(gross_income="€ 50,000.00")
        assert profile2.gross_income == Decimal("50000.00")

    def test_gross_income_computation_salary(self) -> None:
        """Test computing gross income from salary and bonus."""
        profile = IncomeProfile(salary="50000", bonus="5000")
        assert profile.gross_income == Decimal("55000")

    def test_gross_income_computation_hourly(self) -> None:
        """Test computing gross income from hourly wage."""
        profile = IncomeProfile(hourly_wage="50.00", hours_per_week="40")
        # 50 * 40 * 52 = 104000
        assert profile.gross_income == Decimal("104000.00")

    def test_gross_income_computation_new_types(self) -> None:
        """Test computing gross income with contractor, freelance, rsu, etc."""
        profile = IncomeProfile(
            salary="50000",
            contractor_income="10000",
            freelance_income="5000",
            commission="2000",
            rsu_income="15000",
            stock_option_income="3000",
        )
        # 50000 + 10000 + 5000 + 2000 + 15000 + 3000 = 85000
        assert profile.gross_income == Decimal("85000")

    def test_negative_income_fails(self) -> None:
        """Ensure negative income raises validation errors."""
        with pytest.raises(ValidationError):
            IncomeProfile(gross_income="-5000")

        with pytest.raises(ValidationError):
            IncomeProfile(salary="5000", bonus="-10000")


class TestLocationValidation:
    """Test strict location boundary checks."""

    def test_valid_location(self) -> None:
        loc = LocationProfile(country="US", state="CA", zip_code="90210")
        assert loc.country == "US"

    def test_international_postal_codes(self) -> None:
        loc = LocationProfile(country="GB", zip_code="SW1A 1AA")
        assert loc.zip_code == "SW1A 1AA"

    def test_invalid_country_code(self) -> None:
        with pytest.raises(ValidationError):
            LocationProfile(country="U")  # Too short

    def test_invalid_zip_code(self) -> None:
        with pytest.raises(ValidationError):
            LocationProfile(country="US", zip_code="!@#$%")  # Invalid chars


class TestDemographicValidation:
    """Test demographic logic."""

    def test_valid_demographic(self) -> None:
        demo = DemographicProfile(filing_status=FilingStatus.MARRIED_JOINTLY, dependents=2)
        assert demo.dependents == 2

    def test_invalid_dependents(self) -> None:
        with pytest.raises(ValidationError):
            DemographicProfile(filing_status=FilingStatus.SINGLE, dependents=-1)

    def test_invalid_year(self) -> None:
        with pytest.raises(ValidationError):
            DemographicProfile(filing_status=FilingStatus.SINGLE, tax_year=1800)
