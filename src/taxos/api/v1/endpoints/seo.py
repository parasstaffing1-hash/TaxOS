"""SEO Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.api.v1.deps import get_db
from taxos.application.seo.generator import SEOGenerator
from taxos.application.seo.sitemap import SitemapEngine
from taxos.domain.seo.schemas import PageSEOData

router = APIRouter(tags=["seo"])

VERIFIED_TAX_YEAR = 2024

SUPPORTED_SEO_ROUTES = {
    ("after-tax-salary-calculator", "US", "CA"),
    ("paycheck-calculator", "US", "CA"),
}


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
    year: Annotated[int, Query()] = VERIFIED_TAX_YEAR,
) -> PageSEOData:
    """Deterministically generate SEO metadata and structured data for a page."""
    normalized_country = country.upper()
    normalized_state = state.upper() if state else None
    if (
        city
        or year != VERIFIED_TAX_YEAR
        or (calculator_type, normalized_country, normalized_state) not in SUPPORTED_SEO_ROUTES
    ):
        raise HTTPException(status_code=404, detail="No verified public calculator route found")

    generator = SEOGenerator()
    return generator.generate_page_data(
        calculator_type=calculator_type,
        country=normalized_country,
        state=normalized_state,
        year=year,
    )


@router.get("/search")
async def search_seo_routes(
    q: Annotated[str, Query(min_length=2)], _db: AsyncSession = Depends(get_db)
) -> list[dict[str, str]]:
    """Autocomplete search for calculators and locations."""
    q = q.lower()
    if not any(term in q for term in ("calif", "california", "ca", "paycheck", "salary")):
        return []
    return [
        {
            "name": "After-Tax Salary Calculator California (2024)",
            "url": "/after-tax-salary-calculator/us/ca",
        },
        {
            "name": "Paycheck Calculator California (2024)",
            "url": "/paycheck-calculator/us/ca",
        },
    ]


@router.get("/top-routes")
async def get_top_routes(
    _db: AsyncSession = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    """Return verified public routes for build-time static generation."""
    return {
        "routes": [
            {"calculator_type": "after-tax-salary-calculator", "location": ["us", "ca"]},
            {"calculator_type": "paycheck-calculator", "location": ["us", "ca"]},
        ]
    }


@router.get("/sitemaps/count")
async def get_sitemap_count(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Return the number of JSON sitemap chunks for Next.js generation."""
    engine = SitemapEngine(db)
    return {"total_chunks": await engine.get_total_chunks()}


@router.get("/sitemaps/{chunk_id}")
async def get_sitemap_urls(
    chunk_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, list[dict[str, str | float]]]:
    """Return one verified public sitemap chunk as JSON."""
    engine = SitemapEngine(db)
    urls = await engine.get_chunk_urls(chunk_id)
    return {"urls": [{"loc": url, "changefreq": "weekly", "priority": 0.8} for url in urls]}
