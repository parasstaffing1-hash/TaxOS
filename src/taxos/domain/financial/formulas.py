"""Universal Formula Engine for deterministic tax calculations."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from taxos.domain.rules import TaxBracket


def apply_bankers_rounding(amount: Decimal, precision: int = 2) -> Decimal:
    """Applies Banker's Rounding (ROUND_HALF_EVEN) to the given precision."""
    quantizer = Decimal("1." + "0" * precision) if precision > 0 else Decimal("1")
    return amount.quantize(quantizer, rounding=ROUND_HALF_EVEN)


def calculate_progressive_tax(income: Decimal, brackets: list[TaxBracket]) -> tuple[Decimal, list[dict[str, Any]]]:
    """
    Calculates tax based on progressive marginal brackets.
    
    Returns:
        A tuple of (total_tax, breakdown_details).
    """
    total_tax = Decimal("0.0")
    details = []

    # Ensure brackets are sorted by minimum amount
    sorted_brackets = sorted(brackets, key=lambda b: b.min_amount)

    for bracket in sorted_brackets:
        if income <= bracket.min_amount:
            break

        upper_bound = bracket.max_amount if bracket.max_amount is not None else income
        taxable_in_bracket = min(income, upper_bound) - bracket.min_amount
        
        # Apply rate and fixed amount
        bracket_tax = (taxable_in_bracket * bracket.rate) + bracket.fixed_amount
        bracket_tax = apply_bankers_rounding(bracket_tax)
        
        total_tax += bracket_tax

        details.append({
            "min_amount": str(bracket.min_amount),
            "max_amount": str(bracket.max_amount) if bracket.max_amount else "infinity",
            "rate": str(bracket.rate),
            "fixed_amount": str(bracket.fixed_amount),
            "taxable_in_bracket": str(taxable_in_bracket),
            "tax": str(bracket_tax),
        })

    return total_tax, details


def calculate_flat_tax(income: Decimal, rate: Decimal) -> Decimal:
    """Calculates flat tax on income."""
    return apply_bankers_rounding(income * rate)


def calculate_payroll_tax(
    income: Decimal, employee_rate: Decimal, employer_rate: Decimal, wage_base_limit: Decimal | None
) -> tuple[Decimal, Decimal]:
    """
    Calculates payroll tax respecting wage base limits.
    
    Returns:
        A tuple of (employee_tax, employer_tax).
    """
    basis = income
    if wage_base_limit is not None:
        basis = min(basis, wage_base_limit)

    employee_tax = apply_bankers_rounding(basis * employee_rate)
    employer_tax = apply_bankers_rounding(basis * employer_rate)

    return employee_tax, employer_tax


def calculate_vat(amount: Decimal, rate: Decimal) -> Decimal:
    """Calculates VAT or Sales Tax."""
    return apply_bankers_rounding(amount * rate)


def calculate_effective_tax_rate(total_tax: Decimal, gross_income: Decimal) -> Decimal:
    """Calculates the effective tax rate."""
    if gross_income <= 0:
        return Decimal("0.0")
    return apply_bankers_rounding(total_tax / gross_income, precision=4)
