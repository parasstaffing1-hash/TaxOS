"""Master Tool Specifications & Schema Definitions for all 845 Catalog Tools."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from taxos.domain.catalog.master_plan import MASTER_PLAN_TOOL_NAMES
from taxos.domain.catalog.models import ToolFamily, ToolPersona, ToolType
from taxos.domain.catalog.registry import (
    _family_for_plan_number,
    _jurisdiction_for_plan_number,
    _slugify,
    _tool_type_for_title,
)
from taxos.domain.financial.trace import OfficialSourceReference


class FieldType(StrEnum):
    NUMBER = "number"
    TEXT = "text"
    SELECT = "select"
    BOOLEAN = "boolean"


class InputFieldSpec(BaseModel):
    """Schema specification for a tool's interactive input parameter."""

    name: str
    label: str
    field_type: FieldType = FieldType.NUMBER
    default_value: Any = 0
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    options: list[dict[str, str]] | None = None
    unit: str | None = "₹"
    tooltip: str | None = None
    required: bool = True


class ToolSpecification(BaseModel):
    """Complete executable domain specification for a catalog tool."""

    tool_id: str
    number: int
    title: str
    family: ToolFamily
    jurisdiction: str
    tool_type: ToolType
    description: str
    personas: list[ToolPersona] = Field(default_factory=lambda: [ToolPersona.INDIVIDUAL])
    tags: list[str] = Field(default_factory=list)
    handler_key: str
    input_fields: list[InputFieldSpec]
    official_sources: list[OfficialSourceReference]


def _build_sources_for_family(  # noqa: PLR0911
    family: ToolFamily, jurisdiction: str
) -> list[OfficialSourceReference]:
    """Provide statutory official legal references for each tool family."""
    if jurisdiction == "IN":
        if family in (
            ToolFamily.INDIA_INCOME_TAX,
            ToolFamily.INDIA_SALARY_TAX,
            ToolFamily.INDIA_DEDUCTIONS,
            ToolFamily.INDIA_CAPITAL_GAINS,
            ToolFamily.INDIA_SECURITIES,
            ToolFamily.INDIA_CRYPTO_VDA,
            ToolFamily.INDIA_HOUSE_PROPERTY,
            ToolFamily.INDIA_BUSINESS_PROFESSION,
            ToolFamily.INDIA_PRESUMPTIVE,
            ToolFamily.INDIA_ADVANCE_TAX,
            ToolFamily.INDIA_INTEREST_PENALTY,
            ToolFamily.INDIA_TDS,
            ToolFamily.INDIA_TCS,
            ToolFamily.INDIA_FORM16_AIS_26AS,
            ToolFamily.INDIA_ITR,
            ToolFamily.INDIA_CORPORATE_TAX,
            ToolFamily.INDIA_LLP_PARTNERSHIP_HUF,
            ToolFamily.INDIA_INTERNATIONAL_TAX,
            ToolFamily.INDIA_COMPLIANCE_PLATFORM,
        ):
            return [
                OfficialSourceReference(
                    source_id="IN-ITA-1961",
                    title="Income-tax Act, 1961 & Income-tax Rules, 1962",
                    section_or_rule="Statutory provisions and Finance Act notifications",
                    act_name="Income-tax Act, 1961",
                    url="https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
                    effective_date="2024-04-01",
                )
            ]
        if family in (
            ToolFamily.INDIA_GST_CALCULATOR,
            ToolFamily.INDIA_GST_REGISTRATION,
            ToolFamily.INDIA_HSN_SAC,
            ToolFamily.INDIA_GST_INVOICE,
            ToolFamily.INDIA_GST_RETURNS,
            ToolFamily.INDIA_ITC,
            ToolFamily.INDIA_GST_RECONCILIATION,
            ToolFamily.INDIA_GST_EINVOICE,
            ToolFamily.INDIA_EWAY_BILL,
            ToolFamily.INDIA_GST_SPECIAL,
        ):
            return [
                OfficialSourceReference(
                    source_id="IN-CGST-2017",
                    title="Central Goods and Services Tax Act, 2017 & CGST Rules, 2017",
                    section_or_rule="Statutory GST sections, rates, and CBIC notifications",
                    act_name="Central Goods and Services Tax Act, 2017",
                    url="https://cbic-gst.gov.in/",
                    effective_date="2017-07-01",
                )
            ]
        if family == ToolFamily.INDIA_CUSTOMS:
            return [
                OfficialSourceReference(
                    source_id="IN-CUSTOMS-1962",
                    title="Customs Act, 1962 & Customs Tariff Act, 1975",
                    section_or_rule="Basic Customs Duty & Social Welfare Surcharge",
                    act_name="Customs Act, 1962",
                    url="https://www.cbic.gov.in/",
                    effective_date="2024-04-01",
                )
            ]
    elif jurisdiction == "US":
        return [
            OfficialSourceReference(
                source_id="US-IRC-26",
                title="Internal Revenue Code (Title 26) & Treasury Regulations",
                section_or_rule="IRS Federal Tax Code & State Department of Revenue Guidelines",
                act_name="Internal Revenue Code of 1986",
                url="https://www.irs.gov/",
                effective_date="2024-01-01",
            )
        ]
    elif jurisdiction == "GB":
        return [
            OfficialSourceReference(
                source_id="UK-HMRC-2024",
                title="HMRC Income Tax Act 2007 & Value Added Tax Act 1994",
                section_or_rule="UK PAYE, NIC & VAT regulations",
                act_name="Income Tax Act 2007 / Value Added Tax Act 1994",
                url="https://www.gov.uk/government/organisations/hm-revenue-customs",
                effective_date="2024-04-06",
            )
        ]
    elif jurisdiction == "AE":
        return [
            OfficialSourceReference(
                source_id="AE-FTA-2023",
                title="Federal Decree-Law No. 47 of 2022 on Corporate Tax & VAT",
                section_or_rule="UAE Federal Tax Authority Regulations",
                act_name="Corporate Tax Law No. 47 / VAT Decree-Law No. 8",
                url="https://tax.gov.ae/",
                effective_date="2023-06-01",
            )
        ]

    return [
        OfficialSourceReference(
            source_id="GLOBAL-OECD-MTC",
            title="OECD Model Tax Convention & National Statutory Guidelines",
            section_or_rule="Standard international tax rules & rate tables",
            act_name="OECD / National Statutory Framework",
            url="https://www.oecd.org/tax/",
            effective_date="2024-01-01",
        )
    ]


def _build_input_fields_for_tool(  # noqa: PLR0911
    _number: int, family: ToolFamily, jurisdiction: str, title: str
) -> tuple[str, list[InputFieldSpec]]:
    """Generate precise, tailored input fields and execution handler keys for each tool."""
    title_lower = title.lower()
    unit = (
        "₹"
        if jurisdiction == "IN"
        else (
            "$"
            if jurisdiction == "US"
            else ("£" if jurisdiction == "GB" else ("AED " if jurisdiction == "AE" else "$"))
        )
    )

    # 1. Deductions Family (51-70)
    if family == ToolFamily.INDIA_DEDUCTIONS:
        handler_key = "india_deductions"
        if "80c" in title_lower:
            fields = [
                InputFieldSpec(
                    name="sec_80c_epf_ppf_elss_lic_tuition",
                    label="Section 80C Claim (EPF, PPF, ELSS, LIC, Tuition)",
                    default_value=150000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80ccc_pension_fund",
                    label="Section 80CCC Pension Fund",
                    default_value=0,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80ccd1_nps_employee",
                    label="Section 80CCD(1) NPS Employee",
                    default_value=0,
                    unit=unit,
                ),
            ]
        elif "80d" in title_lower:
            fields = [
                InputFieldSpec(
                    name="sec_80d_self_family_premium",
                    label="Self & Family Health Premium",
                    default_value=25000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="is_self_senior_citizen",
                    label="Is Self/Spouse Senior Citizen (60+)?",
                    field_type=FieldType.BOOLEAN,
                    default_value=False,
                ),
                InputFieldSpec(
                    name="sec_80d_parents_premium",
                    label="Parents Health Insurance Premium",
                    default_value=25000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="are_parents_senior_citizens",
                    label="Are Parents Senior Citizens (60+)?",
                    field_type=FieldType.BOOLEAN,
                    default_value=True,
                ),
                InputFieldSpec(
                    name="sec_80d_preventive_checkup",
                    label="Preventive Health Checkup (Max ₹5,000)",
                    default_value=5000,
                    unit=unit,
                ),
            ]
        elif "80g" in title_lower:
            fields = [
                InputFieldSpec(
                    name="sec_80g_donations_100_pct",
                    label="Donations with 100% Deduction (PMNRF, etc.)",
                    default_value=10000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80g_donations_50_pct",
                    label="Donations with 50% Deduction (PM CARES/Trusts)",
                    default_value=10000,
                    unit=unit,
                ),
            ]
        elif "80e" in title_lower:
            fields = [
                InputFieldSpec(
                    name="sec_80e_education_loan_interest",
                    label="Education Loan Interest Paid",
                    default_value=40000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80eea_affordable_housing_interest",
                    label="Affordable Housing Interest u/s 80EEA",
                    default_value=0,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80eeb_electric_vehicle_interest",
                    label="Electric Vehicle Loan Interest u/s 80EEB",
                    default_value=0,
                    unit=unit,
                ),
            ]
        elif "80tta" in title_lower or "80ttb" in title_lower:
            fields = [
                InputFieldSpec(
                    name="sec_80tta_savings_interest",
                    label="Savings Bank Account Interest",
                    default_value=12000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80ttb_senior_deposit_interest",
                    label="Senior Citizen FD/Savings Interest",
                    default_value=50000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="is_self_senior_citizen",
                    label="Are you a Senior Citizen (60+)?",
                    field_type=FieldType.BOOLEAN,
                    default_value=False,
                ),
            ]
        else:
            fields = [
                InputFieldSpec(
                    name="sec_80c_epf_ppf_elss_lic_tuition",
                    label="Section 80C Claim (EPF/PPF/ELSS)",
                    default_value=150000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80ccd1b_nps_additional",
                    label="Section 80CCD(1B) Additional NPS (₹50k)",
                    default_value=50000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80d_self_family_premium",
                    label="Section 80D Health Insurance",
                    default_value=25000,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80e_education_loan_interest",
                    label="Section 80E Education Loan Interest",
                    default_value=0,
                    unit=unit,
                ),
                InputFieldSpec(
                    name="sec_80tta_savings_interest",
                    label="Section 80TTA Savings Bank Interest",
                    default_value=10000,
                    unit=unit,
                ),
            ]
        return handler_key, fields

    # 2. House Property Family (111-150)
    if family == ToolFamily.INDIA_HOUSE_PROPERTY:
        handler_key = "india_house_property"
        fields = [
            InputFieldSpec(
                name="occupancy_type",
                label="Occupancy Status",
                field_type=FieldType.SELECT,
                default_value=(
                    "let_out"
                    if ("let-out" in title_lower or "rent" in title_lower)
                    else "self_occupied"
                ),
                options=[
                    {"label": "Self-Occupied (Living in property)", "value": "self_occupied"},
                    {"label": "Let-Out (Rented out)", "value": "let_out"},
                    {"label": "Deemed Let-Out (Vacant second home)", "value": "deemed_let_out"},
                ],
            ),
            InputFieldSpec(
                name="actual_rent_received_annual",
                label="Annual Rent Received / Receivable",
                default_value=360000,
                unit=unit,
            ),
            InputFieldSpec(
                name="municipal_taxes_paid_by_owner",
                label="Municipal / Property Taxes Paid by Owner",
                default_value=15000,
                unit=unit,
            ),
            InputFieldSpec(
                name="home_loan_interest_annual",
                label="Annual Home Loan Interest Paid (Sec 24b)",
                default_value=200000,
                unit=unit,
            ),
            InputFieldSpec(
                name="ownership_share_percentage",
                label="Your Ownership Share %",
                default_value=100,
                unit="%",
            ),
        ]
        return handler_key, fields

    # 3. Business & Presumptive Family (151-180)
    if family in (ToolFamily.INDIA_BUSINESS_PROFESSION, ToolFamily.INDIA_PRESUMPTIVE):
        handler_key = "india_business"
        scheme = (
            "44ADA"
            if ("44ada" in title_lower or "profession" in title_lower)
            else ("44AE" if "44ae" in title_lower else "44AD")
        )
        fields = [
            InputFieldSpec(
                name="scheme_type",
                label="Presumptive Tax Scheme",
                field_type=FieldType.SELECT,
                default_value=scheme,
                options=[
                    {
                        "label": "Section 44AD (Small Business: 6% digital / 8% cash)",
                        "value": "44AD",
                    },
                    {"label": "Section 44ADA (Professionals: 50% profit)", "value": "44ADA"},
                    {"label": "Section 44AE (Goods Carriage Transporters)", "value": "44AE"},
                    {"label": "Regular PGBP (Normal books of accounts)", "value": "regular_pgbp"},
                ],
            ),
            InputFieldSpec(
                name="gross_turnover_digital",
                label="Gross Digital / Bank Receipts",
                default_value=2500000,
                unit=unit,
            ),
            InputFieldSpec(
                name="gross_turnover_cash", label="Gross Cash Receipts", default_value=0, unit=unit
            ),
            InputFieldSpec(
                name="actual_net_profit_declared",
                label="Actual Net Profit (if higher than statutory min)",
                default_value=0,
                unit=unit,
            ),
            InputFieldSpec(
                name="msme_overdue_payments_unpaid_at_year_end",
                label="Overdue MSME Payments (>45 days) u/s 43B(h)",
                default_value=0,
                unit=unit,
            ),
        ]
        return handler_key, fields

    # 4. TCS Family (221-230)
    if family == ToolFamily.INDIA_TCS:
        handler_key = "india_tcs"
        cat = (
            "206C(1G)_tour_package"
            if "tour" in title_lower
            else (
                "206C(1G)_other_remittance"
                if "lrs" in title_lower
                else (
                    "206C(1H)_goods_above_50l"
                    if "goods" in title_lower
                    else "206C(1F)_motor_vehicle"
                )
            )
        )
        fields = [
            InputFieldSpec(
                name="category",
                label="TCS Transaction Category",
                field_type=FieldType.SELECT,
                default_value=cat,
                options=[
                    {
                        "label": "Section 206C(1F) - Motor Vehicle Value > ₹10 Lakhs (1%)",
                        "value": "206C(1F)_motor_vehicle",
                    },
                    {
                        "label": "Section 206C(1G) - Overseas Tour Program Package (5%/20%)",
                        "value": "206C(1G)_tour_package",
                    },
                    {
                        "label": "Section 206C(1G) - LRS Foreign Remittance for Education/Medical (5%)",
                        "value": "206C(1G)_education_medical",
                    },
                    {
                        "label": "Section 206C(1G) - LRS Other Foreign Remittances (20%)",
                        "value": "206C(1G)_other_remittance",
                    },
                    {
                        "label": "Section 206C(1H) - Sale of Goods exceeding ₹50 Lakhs (0.1%)",
                        "value": "206C(1H)_goods_above_50l",
                    },
                    {"label": "Section 206C(1) - Scrap Sale (1%)", "value": "206C(1)_scrap"},
                    {
                        "label": "Section 206C(1) - Minerals (Coal/Lignite/Iron Ore) (1%)",
                        "value": "206C(1)_minerals",
                    },
                ],
            ),
            InputFieldSpec(
                name="transaction_amount",
                label="Current Transaction Value",
                default_value=1200000,
                unit=unit,
            ),
            InputFieldSpec(
                name="cumulative_amount_financial_year",
                label="Prior Cumulative Transactions in FY",
                default_value=0,
                unit=unit,
            ),
            InputFieldSpec(
                name="has_valid_pan",
                label="Does Buyer / Remitter have a Valid PAN?",
                field_type=FieldType.BOOLEAN,
                default_value=True,
            ),
        ]
        return handler_key, fields

    # 5. Corporate & Entity Tax Family (426-450)
    if family in (ToolFamily.INDIA_CORPORATE_TAX, ToolFamily.INDIA_LLP_PARTNERSHIP_HUF):
        handler_key = "india_corporate"
        etype = (
            "partnership_firm_or_llp"
            if "llp" in title_lower or "partnership" in title_lower
            else (
                "domestic_company_115bab" if "115bab" in title_lower else "domestic_company_115baa"
            )
        )
        fields = [
            InputFieldSpec(
                name="entity_type",
                label="Entity Classification",
                field_type=FieldType.SELECT,
                default_value=etype,
                options=[
                    {
                        "label": "Domestic Company (Section 115BAA @ 22% + 10% sur + 4% cess)",
                        "value": "domestic_company_115baa",
                    },
                    {
                        "label": "New Manufacturing Co. (Section 115BAB @ 15% + 10% sur + 4% cess)",
                        "value": "domestic_company_115bab",
                    },
                    {
                        "label": "Standard Domestic Company (25% / 30% + Normal Surcharge + MAT)",
                        "value": "domestic_company_standard",
                    },
                    {
                        "label": "Partnership Firm / LLP (Flat 30% + Surcharge + Cess)",
                        "value": "partnership_firm_or_llp",
                    },
                    {"label": "Foreign Company (35% in AY 2025-26)", "value": "foreign_company"},
                ],
            ),
            InputFieldSpec(
                name="taxable_income",
                label="Taxable Income / Net Profits",
                default_value=5000000,
                unit=unit,
            ),
            InputFieldSpec(
                name="book_profits_for_mat",
                label="Book Profits for MAT u/s 115JB (if standard co)",
                default_value=0,
                unit=unit,
            ),
            InputFieldSpec(
                name="firm_book_profit",
                label="Firm Book Profit (for Sec 40(b) partner remuneration limit)",
                default_value=2000000,
                unit=unit,
            ),
            InputFieldSpec(
                name="partner_remuneration_claimed",
                label="Partner Remuneration Claimed",
                default_value=1200000,
                unit=unit,
            ),
        ]
        return handler_key, fields

    # 6. Global Tax Families (491-640)
    if jurisdiction != "IN":
        handler_key = "global_tax"
        tax_type = (
            "vat_gst"
            if ("vat" in title_lower or "gst" in title_lower or "sales" in title_lower)
            else ("corporate_tax" if "corporate" in title_lower else "income_tax")
        )
        fields = [
            InputFieldSpec(
                name="country_code",
                label="Country / Jurisdiction",
                field_type=FieldType.SELECT,
                default_value=jurisdiction if jurisdiction != "GLOBAL" else "US",
                options=[
                    {"label": "United States (US)", "value": "US"},
                    {"label": "United Kingdom (GB)", "value": "GB"},
                    {"label": "United Arab Emirates (AE)", "value": "AE"},
                    {"label": "Canada (CA)", "value": "CA"},
                    {"label": "Australia (AU)", "value": "AU"},
                    {"label": "Singapore (SG)", "value": "SG"},
                    {"label": "Germany (DE)", "value": "DE"},
                ],
            ),
            InputFieldSpec(
                name="tax_type",
                label="Tax Type",
                field_type=FieldType.SELECT,
                default_value=tax_type,
                options=[
                    {"label": "Personal Income Tax", "value": "income_tax"},
                    {"label": "Corporate Income Tax", "value": "corporate_tax"},
                    {"label": "VAT / GST / Sales Tax", "value": "vat_gst"},
                ],
            ),
            InputFieldSpec(
                name="gross_income_or_revenue",
                label="Gross Annual Income / Taxable Revenue",
                default_value=100000,
                unit=unit,
            ),
            InputFieldSpec(
                name="allowable_deductions",
                label="Allowable Deductions / Personal Allowance",
                default_value=0,
                unit=unit,
            ),
        ]
        return handler_key, fields

    # 7. Default Generic / Financial Tool
    handler_key = "generic_financial"
    fields = [
        InputFieldSpec(
            name="gross_amount",
            label="Gross Principal Amount / Tax Base",
            default_value=1000000,
            unit=unit,
        ),
        InputFieldSpec(
            name="applicable_rate_pct",
            label="Applicable Rate / Percentage (%)",
            default_value=18,
            unit="%",
        ),
        InputFieldSpec(
            name="exemptions_or_credits",
            label="Exemptions / Allowances / Credits",
            default_value=0,
            unit=unit,
        ),
    ]
    return handler_key, fields


class MasterToolSpecificationRegistry:
    """Registry maintaining full domain specifications for all 845 tools."""

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpecification] = {}
        self._initialize_specs()

    def _initialize_specs(self) -> None:
        existing_ids: set[str] = set()
        for number, title in sorted(MASTER_PLAN_TOOL_NAMES.items(), key=lambda x: x[0]):
            family = _family_for_plan_number(number)
            jurisdiction = _jurisdiction_for_plan_number(number)
            tool_id = _slugify(title, number, existing_ids)
            existing_ids.add(tool_id)
            tool_type = _tool_type_for_title(title)

            handler_key, input_fields = _build_input_fields_for_tool(
                number, family, jurisdiction, title
            )
            sources = _build_sources_for_family(family, jurisdiction)

            description = (
                f"Statutory {title} ({jurisdiction}) for {family.value.replace('_', ' ').title()}. "
                f"Computes authoritative tax liability, statutory deductions, exemptions, and compliance requirements with complete audit traces."
            )

            spec = ToolSpecification(
                tool_id=tool_id,
                number=number,
                title=title,
                family=family,
                jurisdiction=jurisdiction,
                tool_type=tool_type,
                description=description,
                personas=[
                    ToolPersona.INDIVIDUAL,
                    ToolPersona.ACCOUNTANT_CA,
                    ToolPersona.BUSINESS_OWNER,
                ],
                tags=[family.value, jurisdiction.lower(), tool_type.value],
                handler_key=handler_key,
                input_fields=input_fields,
                official_sources=sources,
            )
            self._specs[tool_id] = spec

    def get_spec(self, tool_id: str) -> ToolSpecification | None:
        return self._specs.get(tool_id)

    def get_all_specs(self) -> list[ToolSpecification]:
        return sorted(self._specs.values(), key=lambda s: s.number)


_MASTER_SPEC_REGISTRY = MasterToolSpecificationRegistry()


def get_master_spec_registry() -> MasterToolSpecificationRegistry:
    return _MASTER_SPEC_REGISTRY
