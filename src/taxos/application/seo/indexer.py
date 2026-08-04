"""SEO Database Indexer."""

from __future__ import annotations

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from taxos.infrastructure.database.models.seo import SEORoute, SEOInternalLink
from taxos.infrastructure.database.models.updater import TaxCountry, TaxState, TaxCity
from taxos.application.seo.generator import SEOGenerator


class SEOIndexer:
    """Populates the database with SEO Routes based on available tax rules/locations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = SEOGenerator()

    async def index_locations(self, calculator_types: list[str], year: int = 2026) -> int:
        """
        Crawls the Tax location tables and generates SEORoutes for all known locations.
        Returns the number of pages indexed.
        """
        # Fetch all locations
        countries = (await self.db.execute(select(TaxCountry))).scalars().all()
        states = (await self.db.execute(select(TaxState))).scalars().all()
        cities = (await self.db.execute(select(TaxCity))).scalars().all()

        total_indexed = 0

        # In a true 10M page scenario, this would be chunked/batched.
        # For simplicity, we process them sequentially and commit periodically.
        
        for calc_type in calculator_types:
            routes_to_add = []

            # 1. Country Pages
            for country in countries:
                routes_to_add.append(self._build_route(calc_type, country.code, None, None, year))
                
            # 2. State Pages
            for state in states:
                # Find matching country code (assuming lazy load or mapping available)
                # This requires proper joins in production, but we stub for now
                routes_to_add.append(self._build_route(calc_type, "us", state.code, None, year))
                
            # 3. City Pages
            for city in cities:
                routes_to_add.append(self._build_route(calc_type, "us", "ca", city.name, year))

            # Batch insert
            for route in routes_to_add:
                # Avoid duplicates
                stmt = select(SEORoute).where(SEORoute.slug == route.slug)
                exists = (await self.db.execute(stmt)).scalar_one_or_none()
                if not exists:
                    self.db.add(route)
                    total_indexed += 1
            
            await self.db.commit()

        return total_indexed

    def _build_route(self, calc_type: str, country: str, state: str | None, city: str | None, year: int) -> SEORoute:
        """Helper to use the Generator to hydrate a DB model."""
        page_data = self.generator.generate_page_data(calc_type, country, state, city, year)
        
        return SEORoute(
            slug=page_data.url,
            calculator_type=calc_type,
            country=country,
            state=state,
            city=city,
            tax_year=year,
            title=page_data.meta.title,
            meta_description=page_data.meta.description,
            canonical_url=page_data.meta.canonical,
            h1=page_data.h1,
            content_paragraphs=page_data.content_paragraphs,
            faq_schema=page_data.faq_schema.model_dump() if page_data.faq_schema else None,
            software_schema=page_data.software_schema.model_dump() if page_data.software_schema else None,
            breadcrumb_schema=page_data.breadcrumb_schema.model_dump() if page_data.breadcrumb_schema else None,
            is_active=True
        )
