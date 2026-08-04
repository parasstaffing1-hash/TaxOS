import json
import asyncio
from pathlib import Path
from decimal import Decimal
from typing import Any

from taxos.application.calculations.engine import UniversalTaxEngine
from taxos.application.services.rule_engine import RuleEngineService
from taxos.infrastructure.rules.file_repository import FileBasedRuleRepository

class DatasetVerifier:
    """Verifies calculations using official pre-calculated JSON datasets."""

    def __init__(self, rule_service: RuleEngineService = None, data_dir: str = "c:/Users/HP/Desktop/Tax/tests/verification_data"):
        self.engine = UniversalTaxEngine()
        if rule_service is None:
            repo = FileBasedRuleRepository(base_dir="c:/Users/HP/Desktop/Tax/rules")
            self.rule_service = RuleEngineService(repo)
        else:
            self.rule_service = rule_service
        self.data_dir = Path(data_dir)

    async def verify_all(self, tolerance: float = 0.02) -> dict[str, Any]:
        """Runs through all dataset JSONs and asserts expected outputs."""
        results = {
            "total_datasets": 0,
            "total_assertions": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        if not self.data_dir.exists():
            return results

        for path in self.data_dir.rglob("*.json"):
            results["total_datasets"] += 1
            with open(path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                
            for case in dataset.get("test_cases", []):
                results["total_assertions"] += 1
                try:
                    await self._run_test_case(case, tolerance)
                    results["passed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["failures"].append({
                        "file": str(path.relative_to(self.data_dir)),
                        "case_name": case.get("name", "Unknown"),
                        "error": str(e)
                    })

        return results

    async def _run_test_case(self, case: dict[str, Any], tolerance: float) -> None:
        """Executes a single test case and verifies expected results."""
        inputs = case.get("inputs", {})
        expected = case.get("expected", {})

        gross_amount = Decimal(str(inputs.get("gross_amount", 0)))
        
        try:
            rules = await self.rule_service.get_applicable_rules(
                country=inputs.get("country", "US"),
                year=inputs.get("tax_year", 2026),
                filing_status=inputs.get("filing_status", "single"),
                state=inputs.get("state"),
                city=inputs.get("city"),
            )
        except Exception as e:
            raise ValueError(f"Could not load rules for {inputs}: {e}")

        resp = self.engine.calculate(gross_amount, rules)

        # Assert Expected Outputs
        for key, exp_val in expected.items():
            if key not in resp:
                raise ValueError(f"Expected key '{key}' not in response.")
            
            calc_val = Decimal(str(resp[key]))
            exp_val = Decimal(str(exp_val))
            
            if abs(calc_val - exp_val) > Decimal(str(tolerance)):
                raise ValueError(f"Mismatch for '{key}': Expected {exp_val}, Got {calc_val}")
