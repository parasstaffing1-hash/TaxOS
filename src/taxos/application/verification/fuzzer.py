"""Randomized Fuzz Testing for the Universal Tax Engine."""

import random
import asyncio
from typing import Any
from decimal import Decimal

from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository

class VerificationFuzzer:
    """Generates thousands of edge cases to ensure engine stability and invariant compliance."""

    def __init__(self, rule_service: RuleEngineService = None):
        self.engine = UniversalTaxEngine()
        # Fallback to local init if not provided
        if rule_service is None:
            repo = FileBasedRuleRepository(base_dir="c:/Users/HP/Desktop/Tax/rules")
            self.rule_service = RuleEngineService(repo)
        else:
            self.rule_service = rule_service

    async def run_fuzz_test(self, iterations: int = 100) -> dict[str, Any]:
        """Runs random inputs through the engine and verifies invariants."""
        results = {
            "total_runs": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        # Jurisdictions to test against
        jurisdictions = [
            ("US", "CA", "San Francisco"),
            ("US", "TX", "Austin"),
            ("UK", None, "London")
        ]

        for _ in range(iterations):
            jurisdiction = random.choice(jurisdictions)
            gross = Decimal(random.uniform(0, 10_000_000)).quantize(Decimal("0.01"))
            
            # Fuzz demographics
            is_married = random.random() > 0.5
            filing_status = "married" if is_married else "single"
            
            try:
                rules = await self.rule_service.get_applicable_rules(
                    country=jurisdiction[0],
                    year=2024,
                    filing_status=filing_status,
                    state=jurisdiction[1],
                    city=jurisdiction[2],
                )
            except Exception:
                continue # Skip if rules not found for mock

            results["total_runs"] += 1
            try:
                # Fuzz the calculation
                resp = self.engine.calculate(gross, rules)
                
                # Check Invariants
                net = Decimal(str(resp["net_pay"]))
                total_tax = Decimal(str(resp["total_tax"]))
                eff_rate = Decimal(str(resp["effective_tax_rate"]))

                if net < 0 and gross > 0:
                    raise ValueError(f"Net pay cannot be negative. Gross: {gross}, Net: {net}")
                
                if total_tax < 0:
                    raise ValueError(f"Total tax cannot be negative. Tax: {total_tax}")
                
                if eff_rate > Decimal("1.0"):
                    raise ValueError(f"Effective rate > 100%: {eff_rate}")

                results["passed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "gross": str(gross),
                    "jurisdiction": jurisdiction,
                    "error": str(e)
                })

        return results
