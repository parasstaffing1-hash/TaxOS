"""Normalization Engine for converting raw datasets into unified TaxRuleSet schemas."""

from __future__ import annotations

from typing import Any, Protocol

import structlog

from taxos.domain.rules import TaxRuleSet

logger = structlog.get_logger(__name__)


class AbstractNormalizer(Protocol):
    """Protocol for country-specific normalizers."""

    @property
    def country_code(self) -> str:
        """The ISO-3166 alpha-2 country code."""
        ...

    def normalize(self, raw_data: dict[str, Any] | list[Any], tax_year: int) -> TaxRuleSet:
        """Transform raw parsed data into a valid TaxRuleSet."""
        ...


class NormalizerEngine:
    """Orchestrates normalization across different jurisdictions."""

    def __init__(self) -> None:
        self._normalizers: dict[str, AbstractNormalizer] = {}

    def register(self, normalizer: AbstractNormalizer) -> None:
        """Register a new normalizer plugin."""
        self._normalizers[normalizer.country_code.upper()] = normalizer

    def get_normalizer(self, country_code: str) -> AbstractNormalizer:
        """Get the registered normalizer for a country."""
        country_code = country_code.upper()
        if country_code not in self._normalizers:
            raise ValueError(f"No normalizer registered for {country_code}")
        return self._normalizers[country_code]

    def normalize_payload(
        self, country_code: str, raw_data: dict[str, Any] | list[Any], tax_year: int
    ) -> TaxRuleSet:
        """Normalize a payload using the appropriate normalizer."""
        try:
            normalizer = self.get_normalizer(country_code)
            return normalizer.normalize(raw_data, tax_year)
        except Exception as e:
            logger.error(
                "normalization_failed", country=country_code, year=tax_year, exc_info=True
            )
            raise RuntimeError(f"Normalization failed for {country_code} ({tax_year}): {e}") from e
