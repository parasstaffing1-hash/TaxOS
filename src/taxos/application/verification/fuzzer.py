"""Randomized Fuzz Testing for the Universal Tax Engine."""

import random
from decimal import Decimal
from pathlib import Path
from typing import Any

from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.domain.rules import FilingStatus
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository

MARRIED_FILING_THRESHOLD = 0.5


class VerificationFuzzer:
    """Generates thousands of edge cases to ensure engine stability and invariant compliance."""

    def __init__(self, rule_service: RuleEngineService | None = None) -> None:
        self.engine = UniversalTaxEngine()
        # Fallback to local init if not provided
        if rule_service is None:
            project_root = Path(__file__).resolve().parents[4]
            repo = FileBasedRuleRepository(base_dir=project_root / "rules")
            self.rule_service = RuleEngineService(repo)
        else:
            self.rule_service = rule_service

    async def run_fuzz_test(self, iterations: int = 100) -> dict[str, Any]:
        """Runs random inputs through the engine and verifies invariants."""
        results: dict[str, Any] = {"total_runs": 0, "passed": 0, "failed": 0, "failures": []}

        # Public verification must exercise shipped, verified jurisdictions.
        jurisdictions: list[tuple[str, str | None, str | None]] = [("US", "CA", None)]

        for _ in range(iterations):
            jurisdiction = random.choice(jurisdictions)
            gross = Decimal(random.uniform(0, 10_000_000)).quantize(Decimal("0.01"))

            # Fuzz demographics
            is_married = random.random() > MARRIED_FILING_THRESHOLD
            filing_status = FilingStatus.MARRIED_JOINTLY if is_married else FilingStatus.SINGLE

            results["total_runs"] += 1
            try:
                rules = await self.rule_service.get_applicable_rules(
                    country=jurisdiction[0],
                    year=2024,
                    filing_status=filing_status,
                    state=jurisdiction[1],
                    city=jurisdiction[2],
                )
                # Fuzz the calculation
                resp = self.engine.calculate(gross, rules)

                # Check Invariants
                net = Decimal(str(resp["net_income"]["annual"]))
                total_tax = Decimal(str(resp["final_tax"]["annual"]))
                eff_rate = Decimal(str(resp["effective_tax_rate"]))

                if net < 0 and gross > 0:
                    raise ValueError(f"Net pay cannot be negative. Gross: {gross}, Net: {net}")

                if total_tax < 0:
                    raise ValueError(f"Total tax cannot be negative. Tax: {total_tax}")

                if eff_rate > Decimal("100.0"):
                    raise ValueError(f"Effective rate > 100%: {eff_rate}")

                results["passed"] += 1

            except Exception as exc:
                results["failed"] += 1
                results["failures"].append(
                    {"gross": str(gross), "jurisdiction": jurisdiction, "error": str(exc)}
                )

        return results
