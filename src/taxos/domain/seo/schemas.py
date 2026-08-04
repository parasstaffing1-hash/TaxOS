"""SEO Domain Schemas for Metadata and JSON-LD Structured Data."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BreadcrumbItem(BaseModel):
    """A single item in a breadcrumb trail."""

    name: str
    item: str


class MetaTags(BaseModel):
    """Standard SEO Meta Tags."""

    title: str
    description: str
    canonical: str
    og_title: str
    og_description: str
    og_url: str
    og_type: str = "website"
    twitter_card: str = "summary_large_image"
    twitter_title: str
    twitter_description: str


class StructuredDataFAQ(BaseModel):
    """FAQ Schema."""

    type: Literal["FAQPage"] = Field(default="FAQPage", alias="@type")
    mainEntity: list[dict[str, Any]] = Field(default_factory=list)


class StructuredDataSoftwareApp(BaseModel):
    """SoftwareApplication Schema for the Calculator."""

    type: Literal["SoftwareApplication"] = Field(default="SoftwareApplication", alias="@type")
    name: str
    applicationCategory: str = "BusinessApplication"
    operatingSystem: str = "Any"
    offers: dict[str, Any] = Field(default_factory=lambda: {"@type": "Offer", "price": "0"})


class StructuredDataBreadcrumb(BaseModel):
    """BreadcrumbList Schema."""

    type: Literal["BreadcrumbList"] = Field(default="BreadcrumbList", alias="@type")
    itemListElement: list[dict[str, Any]] = Field(default_factory=list)


class PageSEOData(BaseModel):
    """Complete payload for a single dynamically generated SEO page."""

    url: str
    h1: str
    content_paragraphs: list[str]
    meta: MetaTags
    faq_schema: StructuredDataFAQ | None = None
    software_schema: StructuredDataSoftwareApp | None = None
    breadcrumb_schema: StructuredDataBreadcrumb | None = None
    related_links: list[dict[str, str]] = Field(default_factory=list)
