"""Deterministic SEO Application Engine."""

from __future__ import annotations

import re
from typing import Any

ISO_COUNTRY_CODE_LENGTH = 2


class URLGenerator:
    """Generates canonical slugs and paths."""

    @staticmethod
    def slugify(text: str) -> str:
        """Deterministically convert any text into a URL-friendly slug."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return text.strip("-")

    @staticmethod
    def generate_canonical(
        calculator_type: str, country: str, state: str | None = None, city: str | None = None
    ) -> str:
        """
        Creates a flat, canonical URL structure.
        E.g. /after-tax-salary-calculator/us-ca-san-francisco
        """
        parts = [URLGenerator.slugify(country)]
        if state:
            parts.append(URLGenerator.slugify(state))
        if city:
            parts.append(URLGenerator.slugify(city))

        location_slug = "-".join(parts)
        calc_slug = URLGenerator.slugify(calculator_type)
        return f"/{calc_slug}/{location_slug}"


class ContentGenerator:
    """Generates deterministic text templates."""

    @staticmethod
    def _format_location(country: str, state: str | None, city: str | None) -> str:
        parts = []
        if city:
            parts.append(city.title())
        if state:
            parts.append(state.upper() if len(state) == ISO_COUNTRY_CODE_LENGTH else state.title())
        if country:
            parts.append(
                country.upper() if len(country) == ISO_COUNTRY_CODE_LENGTH else country.title()
            )
        return ", ".join(parts)

    @staticmethod
    def generate_page_content(
        calculator_type: str, country: str, state: str | None, city: str | None, tax_year: int
    ) -> dict[str, Any]:
        """Generate static H1, Title, Meta Description and HTML Paragraphs."""
        loc_str = ContentGenerator._format_location(country, state, city)
        calc_name = calculator_type.replace("-", " ").title()

        h1 = f"{calc_name} for {loc_str} ({tax_year})"
        title = f"{h1} - TaxOS"
        meta_description = (
            f"Accurately calculate your take-home pay and tax bracket in {loc_str} for the {tax_year} tax year. "
            f"Free {calc_name} powered by TaxOS."
        )

        paragraphs = [
            f"Welcome to the official {calc_name} for {loc_str}. Using the latest {tax_year} tax brackets, "
            f"our engine accurately determines your federal, state, and local tax liabilities.",
            f"By entering your annual salary or hourly wage, you can see exactly where your money goes. "
            f"The calculator automatically factors in regional {loc_str} specific withholdings including income tax, "
            f"Medicare, Social Security, and applicable payroll taxes.",
        ]

        return {
            "h1": h1,
            "title": title,
            "meta_description": meta_description,
            "paragraphs": paragraphs,
        }


class SchemaGenerator:
    """Generates JSON-LD schema objects for SEO."""

    @staticmethod
    def generate_software_schema(name: str, url: str) -> dict[str, Any]:
        return {
            "@type": "SoftwareApplication",
            "name": name,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web",
            "url": url,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }

    @staticmethod
    def generate_faq_schema(location_str: str) -> dict[str, Any]:
        return {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f"How accurate is the tax calculator for {location_str}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Our calculator uses the official published tax brackets for {location_str} to ensure maximum accuracy.",
                    },
                }
            ],
        }
