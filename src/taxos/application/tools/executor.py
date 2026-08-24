"""Universal Catalog Tool Execution Engine."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from taxos.domain.catalog.tool_specifications import (
    ToolSpecification,
    get_master_spec_registry,
)
from taxos.domain.financial.formulas import apply_bankers_rounding
from taxos.domain.financial.trace import (
    ExplanationStep,
    StandardTaxCalculationResponse,
)
from taxos.domain.global_tax.engine import GlobalTaxEngine
from taxos.domain.global_tax.models import GlobalCalculationInput, GlobalTaxType
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


class UniversalToolExecutor:
    """Dispatches execution of any catalog tool to its authoritative domain engine."""

    def __init__(self) -> None:
        self.deduction_engine = IndiaDeductionEngine()
        self.house_property_engine = IndiaHousePropertyEngine()
        self.business_engine = IndiaBusinessTaxEngine()
        self.tcs_engine = IndiaTCSEngine()
        self.entity_engine = IndiaEntityTaxEngine()
        self.global_engine = GlobalTaxEngine()

    def execute_tool(  # noqa: PLR0911, PLR0915
        self, tool_id: str, payload: dict[str, Any], tax_year: str = "2024-25"
    ) -> StandardTaxCalculationResponse:
        spec: ToolSpecification | None = get_master_spec_registry().get_spec(tool_id)
        if not spec:
            raise ValueError(f"Catalog tool '{tool_id}' is not registered.")

        handler = spec.handler_key

        if handler == "india_deductions":
            inp = ChapterVIAInputs(
                sec_80c_epf_ppf_elss_lic_tuition=Decimal(
                    str(payload.get("sec_80c_epf_ppf_elss_lic_tuition", "0"))
                ),
                sec_80ccc_pension_fund=Decimal(str(payload.get("sec_80ccc_pension_fund", "0"))),
                sec_80ccd1_nps_employee=Decimal(str(payload.get("sec_80ccd1_nps_employee", "0"))),
                sec_80ccd1b_nps_additional=Decimal(
                    str(payload.get("sec_80ccd1b_nps_additional", "0"))
                ),
                sec_80d_self_family_premium=Decimal(
                    str(payload.get("sec_80d_self_family_premium", "0"))
                ),
                is_self_senior_citizen=bool(payload.get("is_self_senior_citizen", False)),
                sec_80d_parents_premium=Decimal(str(payload.get("sec_80d_parents_premium", "0"))),
                are_parents_senior_citizens=bool(payload.get("are_parents_senior_citizens", True)),
                sec_80d_preventive_checkup=Decimal(
                    str(payload.get("sec_80d_preventive_checkup", "0"))
                ),
                sec_80e_education_loan_interest=Decimal(
                    str(payload.get("sec_80e_education_loan_interest", "0"))
                ),
                sec_80eea_affordable_housing_interest=Decimal(
                    str(payload.get("sec_80eea_affordable_housing_interest", "0"))
                ),
                sec_80eeb_electric_vehicle_interest=Decimal(
                    str(payload.get("sec_80eeb_electric_vehicle_interest", "0"))
                ),
                sec_80g_donations_100_pct=Decimal(
                    str(payload.get("sec_80g_donations_100_pct", "0"))
                ),
                sec_80g_donations_50_pct=Decimal(
                    str(payload.get("sec_80g_donations_50_pct", "0"))
                ),
                sec_80gg_rent_paid_no_hra=Decimal(
                    str(payload.get("sec_80gg_rent_paid_no_hra", "0"))
                ),
                adjusted_total_income_for_80gg=Decimal(
                    str(payload.get("adjusted_total_income_for_80gg", "0"))
                ),
                sec_80tta_savings_interest=Decimal(
                    str(payload.get("sec_80tta_savings_interest", "0"))
                ),
                sec_80ttb_senior_deposit_interest=Decimal(
                    str(payload.get("sec_80ttb_senior_deposit_interest", "0"))
                ),
                sec_80dd_has_dependent_disability=bool(
                    payload.get("sec_80dd_has_dependent_disability", False)
                ),
                sec_80dd_dependent_disability_severe=bool(
                    payload.get("sec_80dd_dependent_disability_severe", False)
                ),
                sec_80u_has_self_disability=bool(
                    payload.get("sec_80u_has_self_disability", False)
                ),
                sec_80u_self_disability_severe=bool(
                    payload.get("sec_80u_self_disability_severe", False)
                ),
            )
            _, trace = self.deduction_engine.calculate_deductions(inp, tax_year=tax_year)
            return trace

        if handler == "india_house_property":
            occ = payload.get("occupancy_type", "self_occupied")
            try:
                occ_enum = PropertyOccupancyType(occ)
            except ValueError:
                occ_enum = PropertyOccupancyType.SELF_OCCUPIED

            hp_inp = HousePropertyInputs(
                occupancy_type=occ_enum,
                municipal_value=Decimal(str(payload.get("municipal_value", "0"))),
                fair_rent=Decimal(str(payload.get("fair_rent", "0"))),
                standard_rent=Decimal(str(payload.get("standard_rent", "0"))),
                actual_rent_received_annual=Decimal(
                    str(payload.get("actual_rent_received_annual", "0"))
                ),
                unrealized_rent=Decimal(str(payload.get("unrealized_rent", "0"))),
                vacancy_loss=Decimal(str(payload.get("vacancy_loss", "0"))),
                municipal_taxes_paid_by_owner=Decimal(
                    str(payload.get("municipal_taxes_paid_by_owner", "0"))
                ),
                home_loan_interest_annual=Decimal(
                    str(payload.get("home_loan_interest_annual", "0"))
                ),
                pre_construction_interest_installment=Decimal(
                    str(payload.get("pre_construction_interest_installment", "0"))
                ),
                loan_sanctioned_after_1999=bool(payload.get("loan_sanctioned_after_1999", True)),
                construction_completed_within_5_years=bool(
                    payload.get("construction_completed_within_5_years", True)
                ),
                is_joint_ownership=bool(payload.get("is_joint_ownership", False)),
                ownership_share_percentage=Decimal(
                    str(payload.get("ownership_share_percentage", "100.0"))
                ),
            )
            _, trace = self.house_property_engine.calculate_property_income(
                hp_inp, tax_year=tax_year
            )
            return trace

        if handler == "india_business":
            scheme = payload.get("scheme_type", "44AD")
            try:
                scheme_enum = PresumptiveSchemeType(scheme)
            except ValueError:
                scheme_enum = PresumptiveSchemeType.SEC_44AD_BUSINESS

            biz_inp = BusinessTaxInputs(
                scheme_type=scheme_enum,
                gross_turnover_digital=Decimal(str(payload.get("gross_turnover_digital", "0"))),
                gross_turnover_cash=Decimal(str(payload.get("gross_turnover_cash", "0"))),
                actual_net_profit_declared=Decimal(
                    str(payload.get("actual_net_profit_declared", "0"))
                ),
                num_heavy_goods_vehicles=int(payload.get("num_heavy_goods_vehicles", 0)),
                heavy_vehicle_avg_gross_tonnage=Decimal(
                    str(payload.get("heavy_vehicle_avg_gross_tonnage", "0"))
                ),
                heavy_vehicle_operating_months=int(
                    payload.get("heavy_vehicle_operating_months", 12)
                ),
                num_other_goods_vehicles=int(payload.get("num_other_goods_vehicles", 0)),
                other_vehicle_operating_months=int(
                    payload.get("other_vehicle_operating_months", 12)
                ),
                msme_overdue_payments_unpaid_at_year_end=Decimal(
                    str(payload.get("msme_overdue_payments_unpaid_at_year_end", "0"))
                ),
                sec_40a3_cash_payments_exceeding_10k=Decimal(
                    str(payload.get("sec_40a3_cash_payments_exceeding_10k", "0"))
                ),
                sec_40a_ia_tds_default_expenses=Decimal(
                    str(payload.get("sec_40a_ia_tds_default_expenses", "0"))
                ),
            )
            _, trace = self.business_engine.calculate_business_tax(biz_inp, tax_year=tax_year)
            return trace

        if handler == "india_tcs":
            cat = payload.get("category", "206C(1F)_motor_vehicle")
            try:
                cat_enum = TCSCategory(cat)
            except ValueError:
                cat_enum = TCSCategory.MOTOR_VEHICLE_1F

            tcs_inp = TCSInputs(
                category=cat_enum,
                transaction_amount=Decimal(str(payload.get("transaction_amount", "0"))),
                cumulative_amount_financial_year=Decimal(
                    str(payload.get("cumulative_amount_financial_year", "0"))
                ),
                has_valid_pan=bool(payload.get("has_valid_pan", True)),
                seller_preceding_fy_turnover_above_10cr=bool(
                    payload.get("seller_preceding_fy_turnover_above_10cr", True)
                ),
                is_tds_194q_deducted_by_buyer=bool(
                    payload.get("is_tds_194q_deducted_by_buyer", False)
                ),
            )
            _, trace = self.tcs_engine.calculate_tcs(tcs_inp, tax_year=tax_year)
            return trace

        if handler == "india_corporate":
            etype = payload.get("entity_type", "domestic_company_115baa")
            try:
                etype_enum = EntityType(etype)
            except ValueError:
                etype_enum = EntityType.DOMESTIC_COMPANY_115BAA

            corp_inp = EntityTaxInputs(
                entity_type=etype_enum,
                taxable_income=Decimal(str(payload.get("taxable_income", "0"))),
                book_profits_for_mat=Decimal(str(payload.get("book_profits_for_mat", "0"))),
                turnover_in_base_year_cr=Decimal(
                    str(payload.get("turnover_in_base_year_cr", "100"))
                ),
                firm_book_profit=Decimal(str(payload.get("firm_book_profit", "0"))),
                partner_remuneration_claimed=Decimal(
                    str(payload.get("partner_remuneration_claimed", "0"))
                ),
                partner_capital_interest_rate=Decimal(
                    str(payload.get("partner_capital_interest_rate", "12"))
                ),
                partner_capital_amount=Decimal(str(payload.get("partner_capital_amount", "0"))),
            )
            _, trace = self.entity_engine.calculate_entity_tax(corp_inp, tax_year=tax_year)
            return trace

        if handler == "global_tax":
            country = str(
                payload.get(
                    "country_code", spec.jurisdiction if spec.jurisdiction != "GLOBAL" else "US"
                )
            )
            raw_tax_type = str(payload.get("tax_type", "income_tax"))
            try:
                tt_enum = GlobalTaxType(raw_tax_type)
            except ValueError:
                tt_enum = GlobalTaxType.INCOME_TAX

            gross = Decimal(
                str(payload.get("gross_income_or_revenue", payload.get("gross_amount", "100000")))
            )
            deductions = Decimal(str(payload.get("allowable_deductions", "0")))

            global_inp = GlobalCalculationInput(
                country_code=country,
                gross_income_or_revenue=gross,
                tax_type=tt_enum,
                expenses_or_deductions=deductions,
            )

            res = self.global_engine.calculate(global_inp)

            steps = [
                ExplanationStep(
                    step_number=1,
                    label=f"Tax Calculation for {country} ({raw_tax_type})",
                    formula_or_rule=f"Applied statutory rule pack {res.rule_version}",
                    inputs={"gross_amount": str(gross), "deductions": str(deductions)},
                    applied_rate_or_limit=res.effective_tax_rate_percent,
                    result=apply_bankers_rounding(res.calculated_tax),
                    notes="Evaluated through global country tax engine.",
                )
            ]

            return StandardTaxCalculationResponse(
                jurisdiction=country,
                tax_type=raw_tax_type,
                tax_year=tax_year,
                effective_date="2024-01-01",
                rule_version=res.rule_version,
                taxpayer_type="taxpayer",
                inputs=payload,
                calculation={
                    "gross_amount": str(res.gross_basis),
                    "taxable_base": str(res.taxable_basis),
                    "base_tax": str(res.calculated_tax),
                    "net_tax_payable": str(res.calculated_tax),
                    "effective_tax_rate": str(res.effective_tax_rate_percent),
                },
                slabs_breakdown=res.slabs_breakdown,
                steps=steps,
                assumptions=res.assumptions,
                official_sources=spec.official_sources,
            )

        # Default Generic Financial Handler
        gross = Decimal(str(payload.get("gross_amount", payload.get("amount", "100000"))))
        rate_pct = Decimal(str(payload.get("applicable_rate_pct", payload.get("rate", "18"))))
        tax_credits = Decimal(str(payload.get("exemptions_or_credits", "0")))

        base_tax = gross * (rate_pct / Decimal("100.0"))
        net_tax = max(Decimal("0.00"), base_tax - tax_credits)

        steps = [
            ExplanationStep(
                step_number=1,
                label=f"Statutory {spec.title} Computation",
                formula_or_rule=f"Gross ({gross}) * Rate ({rate_pct}%) - Credits ({tax_credits})",
                inputs={
                    "gross_amount": str(gross),
                    "rate_pct": str(rate_pct),
                    "credits": str(tax_credits),
                },
                applied_rate_or_limit=rate_pct,
                result=apply_bankers_rounding(net_tax),
                notes="Standard precision statutory computation.",
            )
        ]

        return StandardTaxCalculationResponse(
            jurisdiction=spec.jurisdiction,
            tax_type=spec.family.value,
            tax_year=tax_year,
            effective_date=f"{tax_year[:4]}-04-01",
            rule_version=f"{spec.jurisdiction}-{spec.family.value.upper()}-{tax_year}.1",
            taxpayer_type="taxpayer",
            inputs=payload,
            calculation={
                "gross_amount": str(apply_bankers_rounding(gross)),
                "applied_rate_pct": str(rate_pct),
                "credits_applied": str(apply_bankers_rounding(tax_credits)),
                "net_tax_payable": str(apply_bankers_rounding(net_tax)),
            },
            steps=steps,
            warnings=[],
            assumptions=["Statutory calculation rendered with strict Decimal precision."],
            official_sources=spec.official_sources,
        )


_UNIVERSAL_TOOL_EXECUTOR = UniversalToolExecutor()


def get_universal_tool_executor() -> UniversalToolExecutor:
    return _UNIVERSAL_TOOL_EXECUTOR
