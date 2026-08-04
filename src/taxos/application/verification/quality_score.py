"""Aggregates verification metrics into a single Quality Score."""

from typing import Any

PRODUCTION_READY_THRESHOLD = 98.0


class QualityScoreGenerator:
    """Generates the enterprise production readiness score."""

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {
            "accuracy": 0.40,
            "rule_integrity": 0.30,
            "coverage": 0.20,
            "performance": 0.10,
        }

    def generate(
        self,
        dataset_results: dict[str, Any],
        fuzz_results: dict[str, Any],
        rule_results: dict[str, Any],
        coverage_pct: float = 95.0,
        perf_score_pct: float = 98.0,
    ) -> dict[str, Any]:
        """Calculates the unified Quality Score out of 100."""

        # 1. Calculation Accuracy (from datasets and fuzzing)
        total_calc = dataset_results.get("total_assertions", 0) + fuzz_results.get("total_runs", 0)
        passed_calc = dataset_results.get("passed", 0) + fuzz_results.get("passed", 0)
        accuracy_pct = (passed_calc / total_calc * 100.0) if total_calc > 0 else 100.0

        # 2. Rule Integrity
        total_rules = rule_results.get("total_files", 0)
        passed_rules = rule_results.get("passed", 0)
        integrity_pct = (passed_rules / total_rules * 100.0) if total_rules > 0 else 100.0

        # Calculate weighted score
        final_score = (
            (accuracy_pct * self.weights["accuracy"])
            + (integrity_pct * self.weights["rule_integrity"])
            + (coverage_pct * self.weights["coverage"])
            + (perf_score_pct * self.weights["performance"])
        )

        return {
            "overall_score": round(final_score, 2),
            "is_production_ready": final_score >= PRODUCTION_READY_THRESHOLD,
            "breakdown": {
                "calculation_accuracy_pct": round(accuracy_pct, 2),
                "rule_integrity_pct": round(integrity_pct, 2),
                "code_coverage_pct": round(coverage_pct, 2),
                "performance_pct": round(perf_score_pct, 2),
            },
            "failures": {
                "datasets": dataset_results.get("failures", []),
                "fuzzer": fuzz_results.get("failures", []),
                "rules": rule_results.get("failures", []),
            },
        }
