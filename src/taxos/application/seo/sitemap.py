"""Sitemap generator and chunker."""

from __future__ import annotations

import math
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession


class SitemapEngine:
    """Generates sitemap XML strings in chunks."""

    URLS_PER_CHUNK: ClassVar[int] = 40000
    PUBLIC_CALCULATOR_TYPES: ClassVar[tuple[str, ...]] = (
        "after-tax-salary-calculator",
        "paycheck-calculator",
    )

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
        return self._build_xml(await self.get_chunk_urls(chunk_id))

    async def get_chunk_urls(self, chunk_id: int) -> list[str]:
        """Return the public URLs in one sitemap chunk."""
        all_urls = await self._generate_all_urls()
        start_idx = chunk_id * self.URLS_PER_CHUNK
        return all_urls[start_idx : start_idx + self.URLS_PER_CHUNK]

    async def generate_index(self, total_chunks: int) -> str:
        """Generate a sitemap index file."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        for i in range(total_chunks):
            sitemap_url = f"{self.base_url}/sitemap-{i}.xml"
            lines.append(f"  <sitemap><loc>{sitemap_url}</loc></sitemap>")

        lines.append("</sitemapindex>")
        return "\n".join(lines)

    async def _generate_all_urls(self) -> list[str]:
        """Return only jurisdictions verified for the public release.

        The updater database can contain draft and experimental jurisdictions,
        which must never be published merely because they are present there.
        """
        return [
            f"{self.base_url}/{calculator_type}/us/ca"
            for calculator_type in self.PUBLIC_CALCULATOR_TYPES
        ]

    def _build_xml(self, urls: list[str]) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        for url in urls:
            lines.append(f"  <url><loc>{url}</loc></url>")

        lines.append("</urlset>")
        return "\n".join(lines)
