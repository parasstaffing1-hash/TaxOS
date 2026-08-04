import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.domain.rules import FilingStatus
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository


class DatasetVerifier:
    """Verifies calculations using versioned tax-rule regression datasets."""

    def __init__(
        self,
        rule_service: RuleEngineService | None = None,
        data_dir: str | Path | None = None,
    ) -> None:
        self.engine = UniversalTaxEngine()
        if rule_service is None:
            project_root = Path(__file__).resolve().parents[4]
            repo = FileBasedRuleRepository(base_dir=project_root / "rules")
            self.rule_service = RuleEngineService(repo)
        else:
            self.rule_service = rule_service
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).resolve().parents[4] / "tests" / "verification_data"
        )

    async def verify_all(self, tolerance: float = 0.02) -> dict[str, Any]:
        """Runs through all dataset JSONs and asserts expected outputs."""
        results: dict[str, Any] = {
            "total_datasets": 0,
            "total_assertions": 0,
            "passed": 0,
            "failed": 0,
            "failures": [],
        }

        if not self.data_dir.exists():
            return results

        for path in self.data_dir.rglob("*.json"):
            results["total_datasets"] += 1
            with open(path, encoding="utf-8") as f:
                dataset = json.load(f)

            for case in dataset.get("test_cases", []):
                if not isinstance(case, dict):
                    results["failed"] += 1
                    results["failures"].append(
                        {
                            "file": str(path.relative_to(self.data_dir)),
                            "case_name": "Unknown",
                            "error": "Test case must be an object.",
                        }
                    )
                    continue
                results["total_assertions"] += 1
                try:
                    await self._run_test_case(case, tolerance)
                    results["passed"] += 1
                except Exception as exc:
                    results["failed"] += 1
                    results["failures"].append(
                        {
                            "file": str(path.relative_to(self.data_dir)),
                            "case_name": case.get("name", "Unknown"),
                            "error": str(exc),
                        }
                    )

        return results

    async def _run_test_case(self, case: dict[str, Any], tolerance: float) -> None:
        """Executes a single test case and verifies expected results."""
        inputs = case.get("inputs", {})
        expected = case.get("expected", {})
        if not isinstance(inputs, dict) or not isinstance(expected, dict):
            raise TypeError("Verification case inputs and expected values must be objects.")

        gross_amount = Decimal(str(inputs.get("gross_amount", 0)))
        country = str(inputs.get("country", "US"))
        tax_year = int(inputs.get("tax_year", 2024))
        filing_status = FilingStatus(str(inputs.get("filing_status", "single")))
        state_value = inputs.get("state")
        city_value = inputs.get("city")
        state = state_value if isinstance(state_value, str) else None
        city = city_value if isinstance(city_value, str) else None

        try:
            rules = await self.rule_service.get_applicable_rules(
                country=country,
                year=tax_year,
                filing_status=filing_status,
                state=state,
                city=city,
            )
        except Exception as exc:
            raise ValueError(f"Could not load rules for {inputs}: {exc}") from exc

        resp = self.engine.calculate(gross_amount, rules)

        # Assert Expected Outputs
        for key, expected_value in expected.items():
            if key not in resp:
                raise ValueError(f"Expected key '{key}' not in response.")

            raw_value = resp[key]
            if isinstance(raw_value, dict):
                raw_value = raw_value["annual"]
            calc_val = Decimal(str(raw_value))
            if key == "effective_tax_rate" and calc_val > 1:
                calc_val /= Decimal("100")
            expected_decimal = Decimal(str(expected_value))

            if abs(calc_val - expected_decimal) > Decimal(str(tolerance)):
                raise ValueError(
                    f"Mismatch for '{key}': Expected {expected_decimal}, Got {calc_val}"
                )
