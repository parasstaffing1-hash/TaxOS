"""India TDS (Tax Deducted at Source) & TCS (Tax Collected at Source) Engine."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel


class TDSRuleDefinition(BaseModel):
    """Specification of a statutory TDS/TCS section under the Income-tax Act."""

    section_code: str
    nature_of_payment: str
    rate_individual_huf: Decimal
    rate_others: Decimal
    threshold_limit: Decimal
    is_per_transaction_threshold: bool = False
    description: str


# Statutory TDS/TCS Master Registry
TDS_TCS_MASTER_REGISTRY: list[TDSRuleDefinition] = [
    TDSRuleDefinition(
        section_code="194A",
        nature_of_payment="Interest other than interest on securities (Bank/FD/Post Office)",
        rate_individual_huf=Decimal("0.10"),
        rate_others=Decimal("0.10"),
        threshold_limit=Decimal("40000.0"),  # ₹50,000 for senior citizens
        description="10% TDS if interest from bank deposits exceeds ₹40,000 (₹50,000 for Senior Citizens)",
    ),
    TDSRuleDefinition(
        section_code="194C",
        nature_of_payment="Payment to contractors / sub-contractors / advertising",
        rate_individual_huf=Decimal("0.01"),
        rate_others=Decimal("0.02"),
        threshold_limit=Decimal("100000.0"),  # Or single transaction ₹30,000
        description="1% for Individual/HUF, 2% for Companies/Firms if single bill > ₹30k or aggregate > ₹1,00,000",
    ),
    TDSRuleDefinition(
        section_code="194H",
        nature_of_payment="Commission or brokerage",
        rate_individual_huf=Decimal("0.02"),  # Reduced from 5% to 2% in Budget 2024
        rate_others=Decimal("0.02"),
        threshold_limit=Decimal("15000.0"),
        description="2% TDS on commission/brokerage exceeding ₹15,000 per financial year",
    ),
    TDSRuleDefinition(
        section_code="194I_LAND_BUILDING",
        nature_of_payment="Rent of land, building or furniture",
        rate_individual_huf=Decimal("0.10"),
        rate_others=Decimal("0.10"),
        threshold_limit=Decimal("240000.0"),
        description="10% TDS on rent of land/building exceeding ₹2,40,000 per year",
    ),
    TDSRuleDefinition(
        section_code="194I_PLANT_MACHINERY",
        nature_of_payment="Rent of plant, machinery or equipment",
        rate_individual_huf=Decimal("0.02"),
        rate_others=Decimal("0.02"),
        threshold_limit=Decimal("240000.0"),
        description="2% TDS on lease/hire of plant or machinery exceeding ₹2,40,000 per year",
    ),
    TDSRuleDefinition(
        section_code="194IB",
        nature_of_payment="Rent paid by Individual / HUF not liable to tax audit",
        rate_individual_huf=Decimal("0.02"),  # Budget 2024 reduced from 5% to 2%
        rate_others=Decimal("0.02"),
        threshold_limit=Decimal("50000.0"),
        is_per_transaction_threshold=True,  # Per month
        description="2% TDS on monthly residential rent exceeding ₹50,000 per month",
    ),
    TDSRuleDefinition(
        section_code="194J_PROFESSIONAL",
        nature_of_payment="Professional services / Director remuneration",
        rate_individual_huf=Decimal("0.10"),
        rate_others=Decimal("0.10"),
        threshold_limit=Decimal("30000.0"),
        description="10% TDS on professional fee / director fee exceeding ₹30,000 per financial year",
    ),
    TDSRuleDefinition(
        section_code="194J_TECHNICAL",
        nature_of_payment="Fees for technical services / Call center operations / Royalty",
        rate_individual_huf=Decimal("0.02"),
        rate_others=Decimal("0.02"),
        threshold_limit=Decimal("30000.0"),
        description="2% TDS on technical service fees or royalties exceeding ₹30,000 per financial year",
    ),
    TDSRuleDefinition(
        section_code="194Q",
        nature_of_payment="Purchase of goods (by buyer with turnover > ₹10 Crores)",
        rate_individual_huf=Decimal("0.001"),  # 0.1%
        rate_others=Decimal("0.001"),
        threshold_limit=Decimal("5000000.0"),
        description="0.1% TDS on value of goods purchased exceeding ₹50,00,000 in aggregate",
    ),
    TDSRuleDefinition(
        section_code="194S",
        nature_of_payment="Transfer of Virtual Digital Asset (Crypto / NFT)",
        rate_individual_huf=Decimal("0.01"),  # 1%
        rate_others=Decimal("0.01"),
        threshold_limit=Decimal("50000.0"),  # ₹10k for specified, ₹50k for others
        description="1% TDS on consideration for transfer of Crypto/VDA exceeding threshold",
    ),
    TDSRuleDefinition(
        section_code="206C_1H",
        nature_of_payment="TCS on sale of goods (Turnover > ₹10 Crores)",
        rate_individual_huf=Decimal("0.001"),  # 0.1%
        rate_others=Decimal("0.001"),
        threshold_limit=Decimal("5000000.0"),
        description="0.1% TCS collected by seller on receipt exceeding ₹50,00,000",
    ),
    TDSRuleDefinition(
        section_code="206C_1G_LRS",
        nature_of_payment="TCS on Foreign Remittance under RBI Liberalised Remittance Scheme (LRS)",
        rate_individual_huf=Decimal("0.20"),  # 20% for amount > 7L (5% for education loan)
        rate_others=Decimal("0.20"),
        threshold_limit=Decimal("700000.0"),
        description="20% TCS on overseas remittances exceeding ₹7,00,000 per financial year",
    ),
]


class TDSCalculationResult(BaseModel):
    """Result of a TDS/TCS calculation."""

    section_code: str
    nature_of_payment: str
    gross_payment_amount: Decimal
    applicable_threshold: Decimal
    is_tds_applicable: bool
    applicable_rate_percentage: Decimal
    tds_deductible_amount: Decimal
    net_payable_amount: Decimal
    explanation: str


class IndiaTDSEngine:
    """Enterprise engine for Indian TDS / TCS rate determination and deduction calculations."""

    def calculate_tds(
        self,
        section_code: str,
        payment_amount: Decimal,
        is_payee_individual_or_huf: bool = True,
        has_valid_pan: bool = True,
    ) -> TDSCalculationResult:
        """Calculate applicable TDS/TCS amount, higher rate u/s 206AA for missing PAN, and net payable."""
        # Find rule from master registry
        rule = next((r for r in TDS_TCS_MASTER_REGISTRY if r.section_code == section_code), None)
        if not rule:
            raise ValueError(f"Unknown TDS/TCS section code: '{section_code}'")

        is_applicable = payment_amount > rule.threshold_limit

        if not is_applicable:
            return TDSCalculationResult(
                section_code=rule.section_code,
                nature_of_payment=rule.nature_of_payment,
                gross_payment_amount=payment_amount,
                applicable_threshold=rule.threshold_limit,
                is_tds_applicable=False,
                applicable_rate_percentage=Decimal("0.0"),
                tds_deductible_amount=Decimal("0.0"),
                net_payable_amount=payment_amount,
                explanation=f"Payment amount (₹{payment_amount:,.0f}) is within the statutory threshold of ₹{rule.threshold_limit:,.0f}.",
            )

        # Base rate determination
        base_rate = rule.rate_individual_huf if is_payee_individual_or_huf else rule.rate_others

        # Higher rate under Section 206AA if PAN is missing (higher of 20% or statutory rate; 5% for 194Q)
        if not has_valid_pan:
            applied_rate = Decimal("0.05") if rule.section_code == "194Q" else Decimal("0.20")
            pan_note = (
                " Higher rate of 20% applied under Section 206AA due to missing/inoperative PAN."
            )
        else:
            applied_rate = base_rate
            pan_note = ""

        # For 194Q and 206C(1H), tax is calculated ONLY on the excess amount over ₹50 Lakhs
        if rule.section_code in ("194Q", "206C_1H"):
            taxable_amount = payment_amount - rule.threshold_limit
        else:
            taxable_amount = payment_amount

        tds_amount = (taxable_amount * applied_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        net_payable = payment_amount - tds_amount

        explanation = (
            f"TDS under Section {rule.section_code} applicable @ {applied_rate * 100:.2f}%. "
            f"Gross Amount: ₹{payment_amount:,.0f}, TDS Deducted: ₹{tds_amount:,.0f}, Net Payable: ₹{net_payable:,.0f}.{pan_note}"
        )

        return TDSCalculationResult(
            section_code=rule.section_code,
            nature_of_payment=rule.nature_of_payment,
            gross_payment_amount=payment_amount,
            applicable_threshold=rule.threshold_limit,
            is_tds_applicable=True,
            applicable_rate_percentage=applied_rate * Decimal("100.0"),
            tds_deductible_amount=tds_amount,
            net_payable_amount=net_payable,
            explanation=explanation,
        )

    def list_all_sections(self) -> list[TDSRuleDefinition]:
        """Return all supported statutory TDS/TCS sections."""
        return TDS_TCS_MASTER_REGISTRY
