"""Input Tax Credit (ITC) Eligibility & Section 17(5) Blocked Credit Checker."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class ITCCategory(StrEnum):
    """Statutory categories of purchases for ITC assessment."""

    GENERAL_BUSINESS_GOODS_SERVICES = "general_business"
    CAPITAL_GOODS_MACHINERY = "capital_goods"
    MOTOR_VEHICLES_SEATING_UNDER_13 = "motor_vehicles_under_13"
    FOOD_BEVERAGES_OUTDOOR_CATERING = "food_and_beverages"
    BEAUTY_HEALTH_SERVICES = "beauty_and_health"
    MEMBERSHIP_CLUB_HEALTH_FITNESS = "club_and_fitness_membership"
    WORKS_CONTRACT_IMMOVABLE_PROPERTY = "works_contract_immovable_property"
    GOODS_LOST_STOLEN_DESTROYED = "goods_lost_stolen_destroyed"
    PERSONAL_CONSUMPTION = "personal_consumption"
    CSR_EXPENSES = "csr_expenses"


class ITCEligibilityAssessment(BaseModel):
    """Result of statutory ITC eligibility check."""

    is_eligible: bool
    blocked_under_section_17_5: bool
    statutory_clause: str | None = None
    reason: str
    reversal_required: bool = False


class IndiaITCEligibilityEngine:
    """Engine checking ITC eligibility under Section 16 and blocked credits u/s 17(5)."""

    def evaluate_itc(  # noqa: PLR0911
        self,
        category: ITCCategory,
        tax_amount: Decimal,  # noqa: ARG002
        is_used_for_taxable_business: bool = True,
        is_further_supply_of_same_category: bool = False,
    ) -> ITCEligibilityAssessment:
        """Evaluate if ITC is claimable or blocked under Section 17(5) of CGST Act."""
        if not is_used_for_taxable_business:
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(1) / Section 17(5)(g)",
                reason="Goods or services used for non-business or personal purposes are strictly ineligible.",
            )

        if category == ITCCategory.MOTOR_VEHICLES_SEATING_UNDER_13:
            if is_further_supply_of_same_category:
                return ITCEligibilityAssessment(
                    is_eligible=True,
                    blocked_under_section_17_5=False,
                    reason="Eligible: Used for making further taxable supply of motor vehicles or passenger transportation.",
                )
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(5)(a)",
                reason="Blocked credit: Motor vehicles for transportation of persons having approved seating capacity <= 13 persons.",
            )

        if category in (
            ITCCategory.FOOD_BEVERAGES_OUTDOOR_CATERING,
            ITCCategory.BEAUTY_HEALTH_SERVICES,
            ITCCategory.MEMBERSHIP_CLUB_HEALTH_FITNESS,
        ):
            if is_further_supply_of_same_category:
                return ITCEligibilityAssessment(
                    is_eligible=True,
                    blocked_under_section_17_5=False,
                    reason="Eligible: Inward supply used for making outward taxable supply of same category.",
                )
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(5)(b)",
                reason="Blocked credit: Food and beverages, catering, beauty treatment, and club memberships are blocked unless statutory obligation under law.",
            )

        if category == ITCCategory.WORKS_CONTRACT_IMMOVABLE_PROPERTY:
            if is_further_supply_of_same_category:
                return ITCEligibilityAssessment(
                    is_eligible=True,
                    blocked_under_section_17_5=False,
                    reason="Eligible: Works contract service for further supply of works contract.",
                )
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(5)(c)",
                reason="Blocked credit: Works contract services for construction of immovable property (other than plant and machinery).",
            )

        if category in (ITCCategory.GOODS_LOST_STOLEN_DESTROYED, ITCCategory.PERSONAL_CONSUMPTION):
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(5)(h)",
                reason="Blocked credit: Goods lost, stolen, destroyed, written off or disposed of by way of gift or free samples.",
            )

        if category == ITCCategory.CSR_EXPENSES:
            return ITCEligibilityAssessment(
                is_eligible=False,
                blocked_under_section_17_5=True,
                statutory_clause="Section 17(5)(fa) (Finance Act 2023 amendment)",
                reason="Blocked credit: Goods or services used for activities relating to corporate social responsibility (CSR).",
            )

        return ITCEligibilityAssessment(
            is_eligible=True,
            blocked_under_section_17_5=False,
            reason="Fully eligible: Standard inward supply used in the course or furtherance of taxable business.",
        )
