"""SEO Database Models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxos.infrastructure.database.base import Base


class SEORoute(Base):
    """Maps a programmatic URL slug to its SEO metadata."""

    __tablename__ = "seo_routes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    calculator_type: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(3), index=True)
    state: Mapped[str | None] = mapped_column(String(3), index=True, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    tax_year: Mapped[int] = mapped_column(Integer, index=True)

    # Generated Metadata
    title: Mapped[str] = mapped_column(String(255))
    meta_description: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str] = mapped_column(String(500))
    h1: Mapped[str] = mapped_column(String(255))
    content_paragraphs: Mapped[list[str]] = mapped_column(JSON)

    # JSON-LD Schemas
    faq_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    software_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    breadcrumb_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    internal_links: Mapped[list[SEOInternalLink]] = relationship(
        "SEOInternalLink",
        foreign_keys="SEOInternalLink.source_route_id",
        back_populates="source_route",
    )

    __table_args__ = (Index("idx_seo_location", "country", "state", "city"),)


class SEORedirect(Base):
    """Stores redirects to prevent 404s and handle canonical updates."""

    __tablename__ = "seo_redirects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    destination_url: Mapped[str] = mapped_column(String(500))
    status_code: Mapped[int] = mapped_column(Integer, default=301)


class SEOInternalLink(Base):
    """Pre-computed internal links graph."""

    __tablename__ = "seo_internal_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_route_id: Mapped[int] = mapped_column(
        ForeignKey("seo_routes.id", ondelete="CASCADE"), index=True
    )
    destination_slug: Mapped[str] = mapped_column(String(255))
    link_text: Mapped[str] = mapped_column(String(255))
    relationship_type: Mapped[str] = mapped_column(
        String(50)
    )  # e.g. "sibling_city", "parent_state", "related_calculator"

    source_route: Mapped[SEORoute] = relationship(
        "SEORoute", back_populates="internal_links", foreign_keys=[source_route_id]
    )
