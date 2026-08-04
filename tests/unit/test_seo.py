"""Unit tests for the Programmatic SEO Engine."""

from taxos.application.seo.generator import SEOGenerator


def test_generator_deterministic_output() -> None:
    """Test that the SEOGenerator produces the correct deterministic output."""
    generator = SEOGenerator(base_url="https://taxos.app")

    data = generator.generate_page_data(
        calculator_type="after-tax-salary-calculator",
        country="us",
        state="ca",
        city="san francisco",
        year=2026,
    )

    # Check URLs
    assert data.url == "/after-tax-salary-calculator/us/ca/san-francisco"
    assert (
        data.meta.canonical == "https://taxos.app/after-tax-salary-calculator/us/ca/san-francisco"
    )

    # Check text
    assert data.h1 == "After Tax Salary Calculator San Francisco, CA, US (2026)"
    assert "San Francisco, CA, US" in data.meta.title
    assert "After Tax Salary Calculator" in data.meta.title

    # Check Structured Data
    assert data.faq_schema is not None
    assert data.faq_schema.type == "FAQPage"
    assert len(data.faq_schema.mainEntity) > 0

    assert data.software_schema is not None
    assert data.software_schema.type == "SoftwareApplication"
    assert data.software_schema.name == "After Tax Salary Calculator San Francisco, CA, US"

    assert data.breadcrumb_schema is not None
    assert data.breadcrumb_schema.type == "BreadcrumbList"
    assert len(data.breadcrumb_schema.itemListElement) == 4

    # Check related links
    assert len(data.related_links) == 1
    assert data.related_links[0]["url"] == "/after-tax-salary-calculator/us/ca"


def test_generator_country_level() -> None:
    """Test that the generator works correctly for top-level country pages."""
    generator = SEOGenerator(base_url="https://taxos.app")

    data = generator.generate_page_data(
        calculator_type="paycheck-calculator",
        country="uk",
        year=2026,
    )

    assert data.url == "/paycheck-calculator/uk"
    assert data.meta.canonical == "https://taxos.app/paycheck-calculator/uk"
    assert data.h1 == "Paycheck Calculator UK (2026)"
    assert len(data.related_links) == 0
