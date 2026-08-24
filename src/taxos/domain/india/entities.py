"""India Taxpayer Entities & Residential Status Models and Calculators.

Supports:
- Taxpayer Types: Individual, HUF, Partnership Firm, LLP, Domestic Company, Foreign Company, AOP/BOI.
- Residential Status: Resident & Ordinarily Resident (ROR), Resident but Not Ordinarily Resident (RNOR), Non-Resident (NRI).
- Statutory Tax Rules for Firms, LLPs, Companies (Sec 115BAA/115BAB) and Presumptive Business Tax.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from taxos.domain.financial.trace import (
    ConfidenceLevel,
    ExplanationStep,
    OfficialSourceReference,
    StandardTaxCalculationResponse,
    TaxRegime,
)


class TaxpayerEntityType(StrEnum):
    """Statutory Indian taxpayer legal entities."""

    INDIVIDUAL = "individual"
    HUF = "huf"
    PARTNERSHIP_FIRM = "partnership_firm"
    LLP = "llp"
    DOMESTIC_COMPANY = "domestic_company"
    FOREIGN_COMPANY = "foreign_company"
    AOP_BOI = "aop_boi"


class ResidentialStatus(StrEnum):
    """Statutory residential status u/s 6 of Income-tax Act, 1961."""

    RESIDENT_ORDINARILY = "resident_ordinarily"  # ROR (Global income taxable in India)
    RESIDENT_NOT_ORDINARILY = "resident_not_ordinarily"  # RNOR
    NON_RESIDENT = "non_resident"  # NRI (Only Indian-sourced income taxable)


class EntityTaxInput(BaseModel):
    """Input parameters for Non-Individual entities (Firm, LLP, Company)."""

    entity_type: TaxpayerEntityType
    assessment_year: str = "2025-26"
    net_taxable_profit: Decimal = Field(ge=0, description="Net taxable business profit")
    gross_turnover: Decimal = Field(
        default=Decimal("0.0"), ge=0, description="Annual gross receipts / turnover"
    )
    is_concessional_115baa: bool = Field(
        default=True,
        description="Whether domestic company opts for 22% rate u/s 115BAA without incentives",
    )
    is_manufacturing_115bab: bool = Field(
        default=False, description="Whether new manufacturing domestic company u/s 115BAB (15%)"
    )
    tds_tcs_advance_tax_credits: Decimal = Field(default=Decimal("0.0"), ge=0)


class IndiaEntityTaxEngine:
    """Tax calculation engine for Firms, LLPs, Domestic Companies, and Foreign Companies."""

    def calculate_entity_tax(  # noqa: PLR0912, PLR0915
        self, payload: EntityTaxInput
    ) -> StandardTaxCalculationResponse:
        """Calculate corporate, LLP, or partnership firm tax liability with statutory surcharge and cess."""
        profit = payload.net_taxable_profit
        steps: list[ExplanationStep] = []
        assumptions: list[str] = []
        warnings: list[str] = []
        sources: list[OfficialSourceReference] = []

        base_tax_rate: Decimal
        surcharge_rate = Decimal("0.0")

        if payload.entity_type in (TaxpayerEntityType.PARTNERSHIP_FIRM, TaxpayerEntityType.LLP):
            # Flat 30% tax u/s 115JB / Chapter XVII
            base_tax_rate = Decimal("0.30")
            base_tax = profit * base_tax_rate
            sources.append(
                OfficialSourceReference(
                    source_id="sec-firm-30",
                    title="Tax on Partnership Firms and LLPs",
                    section_or_rule="Section 167B / Finance Act",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in",
                    effective_date="2024-04-01",
                )
            )
            # Surcharge: 12% if total income exceeds ₹1 Crore
            if profit > Decimal("10000000.0"):
                surcharge_rate = Decimal("0.12")
                assumptions.append("Surcharge of 12% applied on taxable profit exceeding ₹1 Crore")

        elif payload.entity_type == TaxpayerEntityType.DOMESTIC_COMPANY:
            sources.append(
                OfficialSourceReference(
                    source_id="sec-115baa",
                    title="Tax on Domestic Companies opting for Concessional Regime",
                    section_or_rule="Section 115BAA / 115BAB",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in",
                    effective_date="2024-04-01",
                )
            )
            if payload.is_manufacturing_115bab:
                base_tax_rate = Decimal("0.15")
                surcharge_rate = Decimal("0.10")  # Flat 10% surcharge u/s 115BAB
                assumptions.append(
                    "Section 115BAB concessional rate of 15% + 10% surcharge for new manufacturing company"
                )
            elif payload.is_concessional_115baa:
                base_tax_rate = Decimal("0.22")
                surcharge_rate = Decimal("0.10")  # Flat 10% surcharge u/s 115BAA
                assumptions.append(
                    "Section 115BAA concessional rate of 22% + 10% mandatory surcharge applied"
                )
            else:
                # Regular company rate: 25% if turnover <= ₹400 Cr in baseline year, else 30%
                if payload.gross_turnover <= Decimal("4000000000.0"):
                    base_tax_rate = Decimal("0.25")
                    assumptions.append("Domestic company with turnover <= ₹400 Cr taxed at 25%")
                else:
                    base_tax_rate = Decimal("0.30")
                    assumptions.append("Domestic company with turnover > ₹400 Cr taxed at 30%")

                # Regular surcharge: 7% if profit > ₹1 Cr and <= ₹10 Cr; 12% if profit > ₹10 Cr
                if profit > Decimal("100000000.0"):
                    surcharge_rate = Decimal("0.12")
                elif profit > Decimal("10000000.0"):
                    surcharge_rate = Decimal("0.07")

        elif payload.entity_type == TaxpayerEntityType.FOREIGN_COMPANY:
            # Flat 40% (or 35% as per recent Budget amendment for foreign companies)
            base_tax_rate = Decimal("0.35")
            sources.append(
                OfficialSourceReference(
                    source_id="sec-foreign-co",
                    title="Tax on Foreign Companies",
                    section_or_rule="Finance Act, 2024",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in",
                    effective_date="2024-04-01",
                )
            )
            # Surcharge: 2% if profit > ₹1 Cr and <= ₹10 Cr; 5% if profit > ₹10 Cr
            if profit > Decimal("100000000.0"):
                surcharge_rate = Decimal("0.05")
            elif profit > Decimal("10000000.0"):
                surcharge_rate = Decimal("0.02")

        else:
            base_tax_rate = Decimal("0.30")

        base_tax = profit * base_tax_rate
        surcharge_amount = base_tax * surcharge_rate
        tax_before_cess = base_tax + surcharge_amount
        cess_amount = tax_before_cess * Decimal("0.04")
        total_tax_liability = (tax_before_cess + cess_amount).quantize(Decimal("1.0"))
        net_tax_payable = max(
            Decimal("0.0"), total_tax_liability - payload.tds_tcs_advance_tax_credits
        )

        steps.append(
            ExplanationStep(
                step_number=1,
                label=f"Base Entity Tax @ {base_tax_rate * 100}%",
                formula_or_rule="Net Taxable Profit * Base Tax Rate",
                inputs={"net_taxable_profit": profit, "rate": base_tax_rate},
                applied_rate_or_limit=base_tax_rate,
                result=base_tax,
                notes=f"Applicable for entity type: {payload.entity_type.value}",
            )
        )
        if surcharge_amount > Decimal("0.0"):
            steps.append(
                ExplanationStep(
                    step_number=2,
                    label=f"Statutory Surcharge @ {surcharge_rate * 100}%",
                    formula_or_rule="Base Tax * Surcharge Rate",
                    inputs={"base_tax": base_tax, "surcharge_rate": surcharge_rate},
                    applied_rate_or_limit=surcharge_rate,
                    result=surcharge_amount,
                )
            )
        steps.append(
            ExplanationStep(
                step_number=3,
                label="Health & Education Cess @ 4%",
                formula_or_rule="(Base Tax + Surcharge) * 4%",
                inputs={"tax_and_surcharge": tax_before_cess},
                applied_rate_or_limit=Decimal("0.04"),
                result=cess_amount,
            )
        )

        return StandardTaxCalculationResponse(
            jurisdiction="IN",
            tax_type="entity_income_tax",
            tax_year="2024-25",
            assessment_year=payload.assessment_year,
            effective_date="2024-04-01",
            rule_version="IN-ENTITY-2025.1",
            taxpayer_type=payload.entity_type.value,
            regime=TaxRegime.SPECIAL if payload.is_concessional_115baa else TaxRegime.REGULAR,
            inputs={
                "net_taxable_profit": profit,
                "gross_turnover": payload.gross_turnover,
                "entity_type": payload.entity_type.value,
            },
            calculation={
                "taxable_profit": profit,
                "base_tax_rate": base_tax_rate,
                "base_tax": base_tax,
                "surcharge_rate": surcharge_rate,
                "surcharge": surcharge_amount,
                "health_and_education_cess": cess_amount,
                "total_tax_liability": total_tax_liability,
                "prepaid_tax_credits": payload.tds_tcs_advance_tax_credits,
                "net_tax_payable": net_tax_payable,
            },
            steps=steps,
            warnings=warnings,
            assumptions=assumptions,
            official_sources=sources,
            confidence=ConfidenceLevel.DETERMINISTIC,
        )
