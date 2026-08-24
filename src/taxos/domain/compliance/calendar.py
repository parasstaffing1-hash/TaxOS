"""Tax Compliance Calendar, Obligation Tracking & Notice Management Engine."""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class ComplianceFrequency(StrEnum):
    """Frequency of tax filing obligation."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONE_TIME = "one_time"


class FilingStatus(StrEnum):
    """Current compliance filing status."""

    PENDING = "pending"
    UPCOMING = "upcoming"
    FILED_ON_TIME = "filed_on_time"
    FILED_LATE = "filed_late"
    OVERDUE = "overdue"


class AutomationMode(StrEnum):
    """Six-level automation execution mode."""

    ANALYZE_ONLY = "analyze_only"
    CALCULATE = "calculate"
    RECONCILE = "reconcile"
    PREPARE = "prepare"
    SAFE_AUTO_FIX = "safe_auto_fix"
    FULL_AUTOMATION = "full_automation"


class ComplianceObligation(BaseModel):
    """A statutory tax filing or payment obligation."""

    obligation_id: str
    jurisdiction: str = "IN"
    tax_family: str  # "income_tax", "gst", "tds", "advance_tax"
    form_or_filing_name: str
    frequency: ComplianceFrequency
    statutory_due_date_rule: str
    applicable_period: str
    taxpayer_category: str  # "individual", "salaried", "non_audit_business", "tax_audit_company"
    threshold_or_applicability: str
    consequences_of_delay: str
    source_reference: str
    rule_version: str = "IN-2025.1"
    effective_from: date = date(2025, 4, 1)
    effective_to: date | None = None
    resolved_due_date: date | None = None


class ComplianceTask(BaseModel):
    """User/workspace tracking state layered over a statutory obligation."""

    task_id: str
    obligation_id: str
    status: FilingStatus = FilingStatus.PENDING
    due_date: date | None = None
    notes: str | None = None
    updated_at: date = Field(default_factory=date.today)


# Master Indian Statutory Compliance Obligations Calendar
INDIA_COMPLIANCE_OBLIGATIONS: list[ComplianceObligation] = [
    ComplianceObligation(
        obligation_id="itr-individual-non-audit",
        jurisdiction="IN",
        tax_family="income_tax",
        form_or_filing_name="ITR-1 / ITR-2 / ITR-4 (Non-Audit Individuals & HUF)",
        frequency=ComplianceFrequency.ANNUAL,
        statutory_due_date_rule="31st July of the Assessment Year",
        applicable_period="FY 2024-25 (AY 2025-26)",
        taxpayer_category="individual",
        threshold_or_applicability="Total income exceeds basic exemption limit",
        consequences_of_delay="Fee u/s 234F up to ₹5,000 + Interest u/s 234A @ 1%/month + Loss of carry forward",
        source_reference="Section 139(1) of the Income-tax Act, 1961",
    ),
    ComplianceObligation(
        obligation_id="itr-tax-audit-entities",
        jurisdiction="IN",
        tax_family="income_tax",
        form_or_filing_name="ITR-3 / ITR-5 / ITR-6 (Tax Audit & Corporate Cases)",
        frequency=ComplianceFrequency.ANNUAL,
        statutory_due_date_rule="31st October of the Assessment Year",
        applicable_period="FY 2024-25 (AY 2025-26)",
        taxpayer_category="tax_audit_company",
        threshold_or_applicability="Business turnover > ₹1Cr (₹10Cr if digital) or Company",
        consequences_of_delay="Penalty u/s 271B @ 0.5% turnover (max ₹1.5L) + 234F fee",
        source_reference="Section 44AB & Section 139(1)",
    ),
    ComplianceObligation(
        obligation_id="gstr-1-monthly",
        jurisdiction="IN",
        tax_family="gst",
        form_or_filing_name="GSTR-1 (Monthly Outward Supplies)",
        frequency=ComplianceFrequency.MONTHLY,
        statutory_due_date_rule="11th of the succeeding month",
        applicable_period="Monthly",
        taxpayer_category="regular_gst_taxpayer",
        threshold_or_applicability="Turnover > ₹5 Crores or monthly opted taxpayers",
        consequences_of_delay="Late fee ₹50/day (₹20 for Nil) + Blocked E-Way Bill generation",
        source_reference="Section 37 of CGST Act read with Rule 59",
    ),
    ComplianceObligation(
        obligation_id="gstr-3b-monthly",
        jurisdiction="IN",
        tax_family="gst",
        form_or_filing_name="GSTR-3B (Monthly Summary & Tax Payment)",
        frequency=ComplianceFrequency.MONTHLY,
        statutory_due_date_rule="20th of the succeeding month",
        applicable_period="Monthly",
        taxpayer_category="regular_gst_taxpayer",
        threshold_or_applicability="All regular GST registered taxpayers",
        consequences_of_delay="Late fee ₹50/day + 18% p.a. interest on unpaid tax u/s 50",
        source_reference="Section 39 of CGST Act read with Rule 61",
    ),
    ComplianceObligation(
        obligation_id="advance-tax-q1",
        jurisdiction="IN",
        tax_family="advance_tax",
        form_or_filing_name="Advance Tax 1st Installment (15%)",
        frequency=ComplianceFrequency.QUARTERLY,
        statutory_due_date_rule="15th June of the Financial Year",
        applicable_period="Q1 (Apr-Jun)",
        taxpayer_category="all_liable_taxpayers",
        threshold_or_applicability="Net estimated tax >= ₹10,000",
        consequences_of_delay="Interest u/s 234C @ 1% per month for 3 months on shortfall",
        source_reference="Section 208 to 211 of Income-tax Act",
    ),
    ComplianceObligation(
        obligation_id="advance-tax-q2",
        jurisdiction="IN",
        tax_family="advance_tax",
        form_or_filing_name="Advance Tax 2nd Installment (45% Cumulative)",
        frequency=ComplianceFrequency.QUARTERLY,
        statutory_due_date_rule="15th September of the Financial Year",
        applicable_period="Q2 (Jul-Sep)",
        taxpayer_category="all_liable_taxpayers",
        threshold_or_applicability="Net estimated tax >= ₹10,000",
        consequences_of_delay="Interest u/s 234C @ 1% per month for 3 months on shortfall",
        source_reference="Section 208 to 211 of Income-tax Act",
    ),
    ComplianceObligation(
        obligation_id="advance-tax-q3",
        jurisdiction="IN",
        tax_family="advance_tax",
        form_or_filing_name="Advance Tax 3rd Installment (75% Cumulative)",
        frequency=ComplianceFrequency.QUARTERLY,
        statutory_due_date_rule="15th December of the Financial Year",
        applicable_period="Q3 (Oct-Dec)",
        taxpayer_category="all_liable_taxpayers",
        threshold_or_applicability="Net estimated tax >= ₹10,000",
        consequences_of_delay="Interest u/s 234C @ 1% per month for 3 months on shortfall",
        source_reference="Section 208 to 211 of Income-tax Act",
    ),
    ComplianceObligation(
        obligation_id="advance-tax-q4",
        jurisdiction="IN",
        tax_family="advance_tax",
        form_or_filing_name="Advance Tax 4th Installment (100% Cumulative)",
        frequency=ComplianceFrequency.QUARTERLY,
        statutory_due_date_rule="15th March of the Financial Year",
        applicable_period="Q4 (Jan-Mar)",
        taxpayer_category="all_liable_taxpayers",
        threshold_or_applicability="Net estimated tax >= ₹10,000",
        consequences_of_delay="Interest u/s 234C @ 1% per month for 1 month on shortfall",
        source_reference="Section 208 to 211 of Income-tax Act",
    ),
    ComplianceObligation(
        obligation_id="tds-quarterly-return",
        jurisdiction="IN",
        tax_family="tds",
        form_or_filing_name="Quarterly TDS Return (Form 24Q Salary / 26Q Non-Salary)",
        frequency=ComplianceFrequency.QUARTERLY,
        statutory_due_date_rule="31st July (Q1), 31st Oct (Q2), 31st Jan (Q3), 31st May (Q4)",
        applicable_period="Quarterly",
        taxpayer_category="all_deductors",
        threshold_or_applicability="TDS deducted during the quarter",
        consequences_of_delay="Late fee u/s 234E of ₹200/day + Penalty u/s 271H up to ₹1,00,000",
        source_reference="Section 200(3) read with Rule 31A",
    ),
]


class IndiaComplianceCalendarEngine:
    """Engine for statutory tax compliance tracking and deadline alerts."""

    def list_obligations(
        self,
        tax_family: str | None = None,
        taxpayer_category: str | None = None,
    ) -> list[ComplianceObligation]:
        """Fetch matching statutory tax obligations."""
        results = list(INDIA_COMPLIANCE_OBLIGATIONS)
        if tax_family:
            results = [r for r in results if r.tax_family == tax_family]
        if taxpayer_category:
            results = [
                r
                for r in results
                if r.taxpayer_category == taxpayer_category
                or r.taxpayer_category in ("individual", "all_liable_taxpayers")
            ]
        return results

    def resolve_due_dates(
        self, obligations: list[ComplianceObligation], assessment_year: str
    ) -> list[ComplianceObligation]:
        """Resolve fixed statutory dates where the rule is expressible safely."""
        match = re.match(r"^(\d{4})-\d{2}$", assessment_year)
        if not match:
            return obligations
        assessment_year_start = int(match.group(1))
        resolved: list[ComplianceObligation] = []
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        for obligation in obligations:
            date_match = re.search(
                r"(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s+of the",
                obligation.statutory_due_date_rule,
            )
            if not date_match:
                resolved.append(obligation)
                continue
            day = int(date_match.group(1))
            month = months.get(date_match.group(2).lower())
            if month is None:
                resolved.append(obligation)
                continue
            year = (
                assessment_year_start
                if "Assessment Year" in obligation.statutory_due_date_rule
                else assessment_year_start - 1
            )
            resolved.append(
                obligation.model_copy(update={"resolved_due_date": date(year, month, day)})
            )
        return resolved
