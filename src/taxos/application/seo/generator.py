"""Deterministic SEO Page Generator."""

from __future__ import annotations

from taxos.domain.seo.schemas import (
    MetaTags,
    PageSEOData,
    StructuredDataBreadcrumb,
    StructuredDataFAQ,
    StructuredDataSoftwareApp,
)


class SEOGenerator:
    """Generates deterministic SEO metadata and structured data for calculators."""

    def __init__(self, base_url: str = "https://taxos.app") -> None:
        self.base_url = base_url.rstrip("/")

    def generate_page_data(
        self,
        calculator_type: str,
        country: str,
        state: str | None = None,
        city: str | None = None,
        year: int = 2026,
    ) -> PageSEOData:
        """
        Generate complete SEO payload deterministically based on location and type.
        
        calculator_type should be something like 'after-tax-salary-calculator', 'paycheck-calculator'.
        """
        # Format names for presentation
        friendly_type = calculator_type.replace("-", " ").title()

        location_parts = []
        if city:
            location_parts.append(city.title())
        if state:
            location_parts.append(str(state).upper() if len(str(state)) == 2 else str(state).title())
        if country:
            location_parts.append(str(country).upper() if len(str(country)) == 2 else str(country).title())

        friendly_location = ", ".join(location_parts)

        # Build URL path
        path_parts = [calculator_type, country.lower()]
        if state:
            path_parts.append(state.lower())
        if city:
            path_parts.append(city.lower().replace(" ", "-"))

        path = "/" + "/".join(path_parts)
        canonical_url = f"{self.base_url}{path}"

        # Determine H1 and Title
        h1 = f"{friendly_type} {friendly_location} ({year})"
        title = f"{friendly_type} {friendly_location} - Calculate Your Net Pay"
        description = (
            f"Use our free {friendly_type} for {friendly_location} to estimate your {year} "
            f"take-home pay, taxes, and deductions. Instantly see your net income."
        )

        meta = MetaTags(
            title=title,
            description=description,
            canonical=canonical_url,
            og_title=title,
            og_description=description,
            og_url=canonical_url,
            twitter_title=title,
            twitter_description=description,
        )

        # Structured Data
        faq_schema = self._generate_faq(friendly_type, friendly_location, year)
        software_schema = self._generate_software(friendly_type, friendly_location, canonical_url)
        breadcrumb_schema = self._generate_breadcrumbs(path_parts)

        content_paragraphs = [
            f"Welcome to the {friendly_type} for {friendly_location}. Whether you are negotiating a new salary, "
            f"planning your budget, or just curious about your deductions, our {year} calculator provides "
            f"accurate estimates of your take-home pay.",
            f"Our deterministic tax engine factors in the latest {year} tax brackets, standard deductions, "
            f"and payroll taxes applicable in {friendly_location}. Enter your gross income above to see a detailed "
            f"breakdown of your net pay across annual, monthly, and biweekly periods."
        ]

        related = []
        if city:
            # Link to state
            related.append({
                "name": f"{str(state).upper()} {friendly_type}",
                "url": f"/{calculator_type}/{str(country).lower()}/{str(state).lower()}"
            })
        elif state:
            # Link to country
            related.append({
                "name": f"{str(country).upper()} {friendly_type}",
                "url": f"/{calculator_type}/{str(country).lower()}"
            })

        return PageSEOData(
            url=path,
            h1=h1,
            content_paragraphs=content_paragraphs,
            meta=meta,
            faq_schema=faq_schema,
            software_schema=software_schema,
            breadcrumb_schema=breadcrumb_schema,
            related_links=related,
        )

    def _generate_faq(self, friendly_type: str, friendly_location: str, year: int) -> StructuredDataFAQ:
        return StructuredDataFAQ(
            mainEntity=[
                {
                    "@type": "Question",
                    "name": f"How accurate is the {friendly_location} {friendly_type}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Our {year} calculator uses the latest official tax brackets and rules for {friendly_location} to provide highly accurate estimates."
                    }
                },
                {
                    "@type": "Question",
                    "name": f"Does this include local taxes for {friendly_location}?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Yes, the calculator automatically includes federal, state, and local taxes applicable in {friendly_location}."
                    }
                }
            ]
        )

    def _generate_software(self, friendly_type: str, friendly_location: str, url: str) -> StructuredDataSoftwareApp:
        return StructuredDataSoftwareApp(
            name=f"{friendly_type} {friendly_location}",
            offers={"@type": "Offer", "price": "0", "priceCurrency": "USD"}
        )

    def _generate_breadcrumbs(self, path_parts: list[str]) -> StructuredDataBreadcrumb:
        items = []
        current_path = ""
        for i, part in enumerate(path_parts, 1):
            current_path += f"/{part}"
            name = part.replace("-", " ").title()
            items.append({
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": f"{self.base_url}{current_path}"
            })

        return StructuredDataBreadcrumb(itemListElement=items)
