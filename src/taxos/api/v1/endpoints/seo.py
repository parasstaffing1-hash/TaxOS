"""SEO Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.v1.deps import get_db
from taxos.application.seo.generator import SEOGenerator
from taxos.application.seo.sitemap import SitemapEngine
from taxos.domain.seo.schemas import PageSEOData

router = APIRouter(tags=["seo"])


@router.get("/sitemap-index.xml", response_class=Response)
async def get_sitemap_index(db: AsyncSession = Depends(get_db)) -> Response:
    """Return the sitemap index."""
    engine = SitemapEngine(db)
    total_chunks = await engine.get_total_chunks()
    xml_content = await engine.generate_index(total_chunks)

    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap-{chunk_id}.xml", response_class=Response)
async def get_sitemap_chunk(chunk_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    """Return a specific chunk of the sitemap."""
    engine = SitemapEngine(db)
    xml_content = await engine.generate_chunk(chunk_id)

    return Response(content=xml_content, media_type="application/xml")


@router.get("/page-data", response_model=PageSEOData)
async def get_page_data(
    calculator_type: Annotated[str, Query()],
    country: Annotated[str, Query()],
    state: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    year: Annotated[int, Query()] = 2026,
) -> PageSEOData:
    """Deterministically generate SEO metadata and structured data for a page."""
    generator = SEOGenerator()
    return generator.generate_page_data(
        calculator_type=calculator_type,
        country=country,
        state=state,
        city=city,
        year=year,
    )

@router.get("/search")
async def search_seo_routes(
    q: Annotated[str, Query(min_length=2)],
    db: AsyncSession = Depends(get_db)
) -> list[dict[str, str]]:
    """Autocomplete search for calculators and locations."""
    # In a full deployment, this queries the `SEORoute` table or a search index like Elastic.
    # For now, we simulate finding matches based on the query.
    q = q.lower()
    
    # We can hardcode some popular results or dynamically return based on query
    results = []
    if "calif" in q or "ca" in q:
        results.append({"name": "After Tax Salary Calculator California", "url": "/after-tax-salary-calculator/usa/ca"})
        results.append({"name": "Paycheck Calculator California", "url": "/paycheck-calculator/usa/ca"})
    elif "new york" in q or "ny" in q:
        results.append({"name": "Take Home Pay Calculator New York", "url": "/take-home-pay-calculator/usa/ny"})
    elif "london" in q:
        results.append({"name": "Net Salary Calculator London", "url": "/net-salary-calculator/uk/london"})
    else:
        results.append({"name": f"Income Tax Calculator {q.title()}", "url": f"/income-tax-calculator/usa/{q.replace(' ', '-')}"})
    
    return results

@router.get("/top-routes")
async def get_top_routes(db: AsyncSession = Depends(get_db)):
    """Return top 100 routes for build-time static generation."""
    # Stubbed top routes
    return {
        "routes": [
            {"calculator_type": "after-tax-salary-calculator", "location": ["usa", "ca"]},
            {"calculator_type": "after-tax-salary-calculator", "location": ["usa", "ny", "new-york"]},
            {"calculator_type": "paycheck-calculator", "location": ["usa", "tx"]},
        ]
    }
