"""India Capital Gains, Asset Classification, Loss Set-Off & Tax Engine."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class AssetType(StrEnum):
    """Type of capital asset."""

    LISTED_EQUITY_STOCKS = "listed_equity_stocks"
    EQUITY_ORIENTED_MUTUAL_FUNDS = "equity_mutual_funds"
    DEBT_MUTUAL_FUNDS = "debt_mutual_funds"
    UNLISTED_SHARES = "unlisted_shares"
    REAL_ESTATE_PROPERTY = "real_estate_property"
    PHYSICAL_GOLD_JEWELLERY = "physical_gold"
    SOVEREIGN_GOLD_BONDS = "sovereign_gold_bonds"
    BONDS_DEBENTURES = "bonds_debentures"
    VIRTUAL_DIGITAL_ASSETS_CRYPTO = "vda_crypto"


class CapitalGainType(StrEnum):
    """Holding period classification."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class CapitalGainsTransaction(BaseModel):
    """Individual sale transaction of a capital asset."""

    asset_name: str
    asset_type: AssetType
    sale_date: str
    purchase_date: str
    holding_period_months: int
    sale_consideration: Decimal
    cost_of_acquisition: Decimal
    cost_of_improvement: Decimal = Decimal("0.0")
    transfer_expenses: Decimal = Decimal("0.0")
    indexed_cost_of_acquisition: Decimal | None = None


class CapitalGainsSummaryResult(BaseModel):
    """Detailed summary of capital gains across all heads."""

    stcg_111a_equity: Decimal = Decimal("0.0")  # 20% / 15%
    stcg_slab_rate: Decimal = Decimal("0.0")  # Normal slab
    ltcg_112a_equity_gross: Decimal = Decimal("0.0")
    ltcg_112a_exemption_claimed: Decimal = Decimal("0.0")
    ltcg_112a_taxable: Decimal = Decimal("0.0")  # 12.5% / 10%
    ltcg_112_other: Decimal = Decimal("0.0")  # Property, Gold, Unlisted
    vda_crypto_gains: Decimal = Decimal("0.0")  # Flat 30% u/s 115BBH

    # Losses
    stcl_incurred: Decimal = Decimal("0.0")
    ltcl_incurred: Decimal = Decimal("0.0")

    # Set-off results
    net_stcg_taxable: Decimal = Decimal("0.0")
    net_ltcg_taxable: Decimal = Decimal("0.0")
    stcl_carried_forward: Decimal = Decimal("0.0")
    ltcl_carried_forward: Decimal = Decimal("0.0")

    # Tax Liability on Capital Gains
    total_capital_gains_tax: Decimal = Decimal("0.0")
    explanation_notes: list[str] = Field(default_factory=list)


class IndiaCapitalGainsEngine:
    """Enterprise engine for Indian Capital Gains taxation (Budget 2024 compliant)."""

    def __init__(self, assessment_year: str = "2025-26") -> None:
        self.assessment_year = assessment_year

    EQUITY_LONG_TERM_MONTHS = 12
    OTHER_LONG_TERM_MONTHS = 24

    def calculate_gains(  # noqa: PLR0912, PLR0915
        self,
        transactions: list[CapitalGainsTransaction],
    ) -> CapitalGainsSummaryResult:
        """Calculate short-term & long-term capital gains, apply Section 112A exemption, and set off losses."""
        stcg_111a = Decimal("0.0")
        stcg_slab = Decimal("0.0")
        ltcg_112a = Decimal("0.0")
        ltcg_other = Decimal("0.0")
        vda_gains = Decimal("0.0")

        stcl_total = Decimal("0.0")
        ltcl_total = Decimal("0.0")

        notes: list[str] = []

        # 1. Classify and compute gain for each transaction
        for tx in transactions:
            net_sale = tx.sale_consideration - tx.transfer_expenses
            cost = tx.cost_of_acquisition + tx.cost_of_improvement
            gain = net_sale - cost

            # Determine holding period threshold:
            # Listed equity / Equity MFs: 12 months
            # Real estate / Unlisted shares: 24 months
            # Debt funds / Physical gold / Other: 24 months (post Budget 2024; legacy 36 months)
            if tx.asset_type in (
                AssetType.LISTED_EQUITY_STOCKS,
                AssetType.EQUITY_ORIENTED_MUTUAL_FUNDS,
            ):
                is_long_term = tx.holding_period_months > self.EQUITY_LONG_TERM_MONTHS
            elif tx.asset_type in (AssetType.REAL_ESTATE_PROPERTY, AssetType.UNLISTED_SHARES):
                is_long_term = tx.holding_period_months > self.OTHER_LONG_TERM_MONTHS
            elif tx.asset_type == AssetType.DEBT_MUTUAL_FUNDS:
                # Debt funds acquired after 01-04-2023 are always STCG taxed at slab rates u/s 50AA
                is_long_term = False
            else:
                is_long_term = tx.holding_period_months > self.OTHER_LONG_TERM_MONTHS

            # Segregate gains/losses
            if gain >= 0:
                if tx.asset_type in (
                    AssetType.LISTED_EQUITY_STOCKS,
                    AssetType.EQUITY_ORIENTED_MUTUAL_FUNDS,
                ):
                    if is_long_term:
                        ltcg_112a += gain
                    else:
                        stcg_111a += gain
                elif tx.asset_type == AssetType.VIRTUAL_DIGITAL_ASSETS_CRYPTO:
                    vda_gains += gain
                elif is_long_term:
                    ltcg_other += gain
                else:
                    stcg_slab += gain
            else:
                loss = abs(gain)
                if tx.asset_type == AssetType.VIRTUAL_DIGITAL_ASSETS_CRYPTO:
                    notes.append(
                        "Loss from Virtual Digital Assets (Crypto) CANNOT be set off against any income u/s 115BBH."
                    )
                elif is_long_term:
                    ltcl_total += loss
                else:
                    stcl_total += loss

        # 2. Section 112A ₹1.25 Lakh (AY 2025-26) / ₹1.00 Lakh Exemption
        ltcg_112a_exemption_cap = (
            Decimal("125000.0") if self.assessment_year >= "2025-26" else Decimal("100000.0")
        )
        exempt_112a = min(ltcg_112a, ltcg_112a_exemption_cap)
        taxable_112a = max(Decimal("0.0"), ltcg_112a - exempt_112a)

        # 3. Inter-Source and Inter-Head Loss Set-Off (Sections 70 & 71)
        # STCL can be set off against both STCG and LTCG
        # LTCL can only be set off against LTCG
        remaining_stcl = stcl_total
        remaining_ltcl = ltcl_total

        # Set off STCL first against STCG 111A and STCG Slab
        if remaining_stcl > 0 and stcg_slab > 0:
            setoff = min(remaining_stcl, stcg_slab)
            stcg_slab -= setoff
            remaining_stcl -= setoff

        if remaining_stcl > 0 and stcg_111a > 0:
            setoff = min(remaining_stcl, stcg_111a)
            stcg_111a -= setoff
            remaining_stcl -= setoff

        # Set off LTCL against LTCG (112A taxable and 112 other)
        if remaining_ltcl > 0 and ltcg_other > 0:
            setoff = min(remaining_ltcl, ltcg_other)
            ltcg_other -= setoff
            remaining_ltcl -= setoff

        if remaining_ltcl > 0 and taxable_112a > 0:
            setoff = min(remaining_ltcl, taxable_112a)
            taxable_112a -= setoff
            remaining_ltcl -= setoff

        # If STCL still remains, it can be set off against remaining LTCG
        if remaining_stcl > 0 and ltcg_other > 0:
            setoff = min(remaining_stcl, ltcg_other)
            ltcg_other -= setoff
            remaining_stcl -= setoff

        if remaining_stcl > 0 and taxable_112a > 0:
            setoff = min(remaining_stcl, taxable_112a)
            taxable_112a -= setoff
            remaining_stcl -= setoff

        # 4. Tax Calculation on Net Gains
        # Rates post Budget 2024: STCG 111A = 20%, LTCG 112A = 12.5%, LTCG 112 = 12.5%
        # Pre-Budget 2024: STCG 111A = 15%, LTCG 112A = 10%, LTCG 112 = 20%
        stcg_rate = Decimal("0.20") if self.assessment_year >= "2025-26" else Decimal("0.15")
        ltcg_112a_rate = Decimal("0.125") if self.assessment_year >= "2025-26" else Decimal("0.10")
        ltcg_112_rate = Decimal("0.125") if self.assessment_year >= "2025-26" else Decimal("0.20")

        tax_stcg_111a = (stcg_111a * stcg_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax_ltcg_112a = (taxable_112a * ltcg_112a_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        tax_ltcg_112 = (ltcg_other * ltcg_112_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        tax_vda = (vda_gains * Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_tax = tax_stcg_111a + tax_ltcg_112a + tax_ltcg_112 + tax_vda

        notes.append(
            f"Section 112A LTCG exemption applied: ₹{exempt_112a:,.0f} (Cap: ₹{ltcg_112a_exemption_cap:,.0f})."
        )
        if remaining_stcl > 0:
            notes.append(
                f"Unabsorbed STCL of ₹{remaining_stcl:,.0f} eligible for 8-year carry forward u/s 74."
            )
        if remaining_ltcl > 0:
            notes.append(
                f"Unabsorbed LTCL of ₹{remaining_ltcl:,.0f} eligible for 8-year carry forward u/s 74."
            )

        return CapitalGainsSummaryResult(
            stcg_111a_equity=stcg_111a,
            stcg_slab_rate=stcg_slab,
            ltcg_112a_equity_gross=ltcg_112a,
            ltcg_112a_exemption_claimed=exempt_112a,
            ltcg_112a_taxable=taxable_112a,
            ltcg_112_other=ltcg_other,
            vda_crypto_gains=vda_gains,
            stcl_incurred=stcl_total,
            ltcl_incurred=ltcl_total,
            net_stcg_taxable=stcg_111a + stcg_slab,
            net_ltcg_taxable=taxable_112a + ltcg_other,
            stcl_carried_forward=remaining_stcl,
            ltcl_carried_forward=remaining_ltcl,
            total_capital_gains_tax=total_tax,
            explanation_notes=notes,
        )
