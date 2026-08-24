"""Calculation Explainability, Trace & Standard Response Models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceLevel(StrEnum):
    """Confidence level of the calculation or extraction."""

    DETERMINISTIC = "deterministic"
    HIGH = "high"
    MODERATE = "moderate"
    REVIEW_REQUIRED = "review_required"


class TaxRegime(StrEnum):
    """Tax regime classification."""

    NEW = "new"
    OLD = "old"
    COMPOSITION = "composition"
    REGULAR = "regular"
    SPECIAL = "special"


class ExplanationStep(BaseModel):
    """A granular calculation step explaining how a specific value was derived."""

    model_config = ConfigDict(frozen=True)

    step_number: int
    label: str
    formula_or_rule: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    applied_rate_or_limit: Decimal | str | None = None
    result: Decimal | str
    notes: str | None = None


class TaxSlabBreakdown(BaseModel):
    """Granular tax breakdown for a specific bracket/slab."""

    model_config = ConfigDict(frozen=True)

    min_amount: Decimal
    max_amount: Decimal | None = None
    rate: Decimal
    taxable_in_slab: Decimal
    tax_amount: Decimal


class OfficialSourceReference(BaseModel):
    """Statutory legal source reference for a tax rule."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    title: str
    section_or_rule: str
    act_name: str = "Income-tax Act, 1961 / Central Goods and Services Tax Act, 2017"
    url: str | None = None
    effective_date: str | None = None


class StandardTaxCalculationResponse(BaseModel):
    """Standardized enterprise response model returned by all TaxOS engines."""

    jurisdiction: str = Field(description="Country or jurisdiction code, e.g. 'IN', 'US', 'GB'")
    tax_type: str = Field(description="Type of tax, e.g. 'income_tax', 'salary_tax', 'gst'")
    tax_year: str = Field(
        description="Financial or tax year, e.g. '2024-25', '2025-26', '2026-27'"
    )
    assessment_year: str | None = Field(
        default=None, description="Assessment year where applicable, e.g. '2025-26'"
    )
    rule_version: str = Field(
        description="Unique version string of the applied rule pack, e.g. 'IN-IT-2025.1'"
    )
    taxpayer_type: str = Field(
        default="individual", description="individual, huf, firm, llp, company, etc."
    )
    regime: TaxRegime | str | None = None

    inputs: dict[str, Any] = Field(
        description="Sanitized and normalized input parameters used for calculation"
    )
    calculation: dict[str, Any] = Field(
        description="Summary calculated financial values (gross, deductions, base tax, cess, net tax)"
    )
    slabs_breakdown: list[TaxSlabBreakdown] = Field(
        default_factory=list, description="Bracket-by-bracket calculation breakdown"
    )
    steps: list[ExplanationStep] = Field(
        default_factory=list,
        description="Chronological explanation steps for complete transparency",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Important notices, boundary conditions, or planning considerations",
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Explicit assumptions made during calculation"
    )
    official_sources: list[OfficialSourceReference] = Field(
        default_factory=list, description="Statutory rule and legal source references"
    )

    confidence: ConfidenceLevel = ConfidenceLevel.DETERMINISTIC
    review_required: bool = False
    review_reason: str | None = None
    calculated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
