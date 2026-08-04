"""Sitemap generator and chunker."""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxos.infrastructure.database.models.updater import TaxCity, TaxCountry, TaxState


class SitemapEngine:
    """Generates sitemap XML strings in chunks."""

    URLS_PER_CHUNK = 40000
    CALCULATOR_TYPES = [
        "after-tax-salary-calculator",
        "paycheck-calculator",
        "salary-tax-calculator",
        "take-home-pay-calculator"
    ]

    def __init__(self, db: AsyncSession, base_url: str = "https://taxos.app") -> None:
        self.db = db
        self.base_url = base_url.rstrip("/")

    async def get_total_chunks(self) -> int:
        """Estimate the total number of chunks."""
        # For simplicity in this implementation, we will fetch all combinations
        urls = await self._generate_all_urls()
        return max(1, math.ceil(len(urls) / self.URLS_PER_CHUNK))

    async def generate_chunk(self, chunk_id: int) -> str:
        """Generate a specific chunk of the sitemap."""
        all_urls = await self._generate_all_urls()

        start_idx = chunk_id * self.URLS_PER_CHUNK
        end_idx = start_idx + self.URLS_PER_CHUNK

        chunk_urls = all_urls[start_idx:end_idx]

        return self._build_xml(chunk_urls)

    async def generate_index(self, total_chunks: int) -> str:
        """Generate a sitemap index file."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for i in range(total_chunks):
            sitemap_url = f"{self.base_url}/sitemap-{i}.xml"
            lines.append(f'  <sitemap><loc>{sitemap_url}</loc></sitemap>')

        lines.append('</sitemapindex>')
        return "\n".join(lines)

    async def _generate_all_urls(self) -> list[str]:
        """Fetch all valid location combinations and multiply by calculator types."""
        # Note: In a real system with millions of rows, we'd use yield and server-side cursors.
        # For this prototype, we'll fetch them all (or assume a reasonable size).

        countries = (await self.db.execute(select(TaxCountry))).scalars().all()
        states = (await self.db.execute(select(TaxState))).scalars().all()
        cities = (await self.db.execute(select(TaxCity))).scalars().all()

        urls = []

        # 1. Country level
        for c in countries:
            for calc in self.CALCULATOR_TYPES:
                urls.append(f"{self.base_url}/{calc}/{c.code.lower()}")

        # 2. State level
        for s in states:
            country = next((c for c in countries if c.id == s.country_id), None)
            if country:
                for calc in self.CALCULATOR_TYPES:
                    urls.append(f"{self.base_url}/{calc}/{country.code.lower()}/{s.code.lower()}")

        # 3. City level
        for city in cities:
            state = next((s for s in states if s.id == city.state_id), None)
            if state:
                country = next((c for c in countries if c.id == state.country_id), None)
                if country:
                    for calc in self.CALCULATOR_TYPES:
                        city_slug = city.name.lower().replace(" ", "-")
                        urls.append(f"{self.base_url}/{calc}/{country.code.lower()}/{state.code.lower()}/{city_slug}")

        return sorted(list(set(urls)))

    def _build_xml(self, urls: list[str]) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for url in urls:
            lines.append(f'  <url><loc>{url}</loc></url>')

        lines.append('</urlset>')
        return "\n".join(lines)
