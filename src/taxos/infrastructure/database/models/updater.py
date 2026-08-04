"""Database models for the Automatic Tax Update Engine."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from taxos.infrastructure.database.base import Base


class TaxCountry(Base):
    __tablename__ = "tax_countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(2), unique=True, index=True)  # ISO 3166-1 alpha-2
    name: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(3))


class TaxState(Base):
    __tablename__ = "tax_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("tax_countries.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(255))

    __table_args__ = (UniqueConstraint("country_id", "code", name="uix_country_state_code"),)


class TaxCity(Base):
    __tablename__ = "tax_cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("tax_states.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), index=True)


class TaxSource(Base):
    __tablename__ = "tax_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    format: Mapped[str] = mapped_column(String(50))  # JSON, XML, PDF, HTML
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TaxUpdateJob(Base):
    """Tracks a run of the updater scheduler."""

    __tablename__ = "tax_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # RUNNING, SUCCESS, FAILED
    total_rules_updated: Mapped[int] = mapped_column(Integer, default=0)


class TaxUpdateLog(Base):
    """Detailed logs for history tracking of specific source scraping."""

    __tablename__ = "tax_update_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("tax_updates.id", ondelete="CASCADE"))
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("tax_sources.id", ondelete="SET NULL"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaxRuleVersion(Base):
    """Tracks version history of rules."""

    __tablename__ = "tax_rule_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction: Mapped[str] = mapped_column(String(255), index=True)
    level: Mapped[str] = mapped_column(String(50))  # country, state, city
    tax_year: Mapped[int] = mapped_column(Integer, index=True)
    version_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    effective_from: Mapped[date | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("tax_sources.id", ondelete="SET NULL"), nullable=True
    )


class TaxRuleData(Base):
    """The actual JSON payload representing the RuleSet."""

    __tablename__ = "tax_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("tax_rule_versions.id", ondelete="CASCADE"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
