"""Central Tool and Calculator Catalog domain models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ToolFamily(StrEnum):
    """Tax tool family category."""

    INDIA_INCOME_TAX = "india_income_tax"
    INDIA_SALARY_TAX = "india_salary_tax"
    INDIA_DEDUCTIONS = "india_deductions"
    INDIA_CAPITAL_GAINS = "india_capital_gains"
    INDIA_SECURITIES = "india_securities"
    INDIA_CRYPTO_VDA = "india_crypto_vda"
    INDIA_HOUSE_PROPERTY = "india_house_property"
    INDIA_BUSINESS_PROFESSION = "india_business_profession"
    INDIA_PRESUMPTIVE = "india_presumptive"
    INDIA_ADVANCE_TAX = "india_advance_tax"
    INDIA_INTEREST_PENALTY = "india_interest_penalty"
    INDIA_TDS = "india_tds"
    INDIA_TCS = "india_tcs"
    INDIA_FORM16_AIS_26AS = "india_form16_ais_26as"
    INDIA_ITR = "india_itr"
    INDIA_GST_CALCULATOR = "india_gst_calculator"
    INDIA_GST_REGISTRATION = "india_gst_registration"
    INDIA_HSN_SAC = "india_hsn_sac"
    INDIA_GST_INVOICE = "india_gst_invoice"
    INDIA_GST_RETURNS = "india_gst_returns"
    INDIA_ITC = "india_itc"
    INDIA_GST_RECONCILIATION = "india_gst_reconciliation"
    INDIA_GST_EINVOICE = "india_gst_einvoice"
    INDIA_EWAY_BILL = "india_eway_bill"
    INDIA_GST_SPECIAL = "india_gst_special"
    INDIA_CUSTOMS = "india_customs"
    INDIA_CORPORATE_TAX = "india_corporate_tax"
    INDIA_LLP_PARTNERSHIP_HUF = "india_llp_partnership_huf"
    INDIA_INTERNATIONAL_TAX = "india_international_tax"
    INDIA_COMPLIANCE_PLATFORM = "india_compliance_platform"

    # Global Tax Families
    GLOBAL_PERSONAL_TAX = "global_personal_tax"
    GLOBAL_PAYROLL_TAX = "global_payroll_tax"
    GLOBAL_CORPORATE_TAX = "global_corporate_tax"
    GLOBAL_VAT_GST = "global_vat_gst"
    US_SALES_TAX = "us_sales_tax"
    EU_VAT = "eu_vat"
    UK_VAT = "uk_vat"
    CANADA_TAX = "canada_tax"
    AUSTRALIA_TAX = "australia_tax"
    UAE_GCC_TAX = "uae_gcc_tax"
    ASIA_PACIFIC_TAX = "asia_pacific_tax"
    CROSS_BORDER_TAX = "cross_border_tax"
    TRANSFER_PRICING = "transfer_pricing"
    GLOBAL_MINIMUM_TAX = "global_minimum_tax"
    GLOBAL_EINVOICING = "global_einvoicing"
    GLOBAL_CUSTOMS = "global_customs"
    ECOMMERCE_TAX = "ecommerce_tax"
    DIGITAL_SERVICES_TAX = "digital_services_tax"
    PROPERTY_REAL_ESTATE_TAX = "property_real_estate_tax"
    ESTATE_GIFT_WEALTH_TAX = "estate_gift_wealth_tax"
    GLOBAL_COMPLIANCE = "global_compliance"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    AUDIT_RECONCILIATION = "audit_reconciliation"
    SCENARIO_PLANNING = "scenario_planning"
    AUTOMATED_WORKFLOWS = "automated_workflows"


class ToolPersona(StrEnum):
    """Target persona for the tax tool."""

    INDIVIDUAL = "individual"
    SALARIED = "salaried"
    FREELANCER = "freelancer"
    INVESTOR = "investor"
    BUSINESS_OWNER = "business_owner"
    ACCOUNTANT_CA = "accountant_ca"
    CFO_ENTERPRISE = "cfo_enterprise"
    NRI_EXPAT = "nri_expat"
    CROSS_BORDER = "cross_border"


class ToolType(StrEnum):
    """Functional nature of the tool."""

    CALCULATOR = "calculator"
    VALIDATOR = "validator"
    CHECKER = "checker"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    RECONCILER = "reconciler"
    COMPARATOR = "comparator"
    SIMULATOR = "simulator"
    WORKFLOW = "workflow"


class ImplementationStatus(StrEnum):
    """Implementation status of a catalog tool."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    NOT_STARTED = "not_started"
    BLOCKED = "blocked"


class TaxTool(BaseModel):
    """Individual tax tool definition in the central catalog."""

    id: str = Field(description="Unique tool slug, e.g. 'india-income-tax-calculator'")
    number: int = Field(description="Catalog sequence number from 1 to 845+")
    title: str
    description: str
    family: ToolFamily
    jurisdiction: str = Field(
        default="IN", description="Country code (IN, US, GB, AE, etc.) or 'GLOBAL'"
    )
    tool_type: ToolType
    personas: list[ToolPersona] = Field(default_factory=list)
    route: str = Field(
        description="Frontend & SEO route path, e.g. '/tax/india/income-tax-calculator'"
    )
    api_endpoint: str | None = None
    status: ImplementationStatus = ImplementationStatus.NOT_STARTED
    tags: list[str] = Field(default_factory=list)
    has_golden_fixtures: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
