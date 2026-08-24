"""SQLAlchemy 2.0 Database Models for Taxpayers, Calculations, Documents & Compliance."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from taxos.infrastructure.database.base import Base


class TaxpayerProfileModel(Base):
    """Database model for an Indian or Global Taxpayer entity."""

    __tablename__ = "taxpayer_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    taxpayer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pan_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pan_masked: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="individual", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(8), default="IN", nullable=False)
    residential_status: Mapped[str] = mapped_column(
        String(64), default="resident_ordinarily", nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )


class SavedCalculationModel(Base):
    """Database model for saved calculations with full audit trace."""

    __tablename__ = "saved_calculations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    taxpayer_profile_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("taxpayer_profiles.id"), nullable=True
    )

    tool_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(8), default="IN", nullable=False)
    financial_year: Mapped[str] = mapped_column(String(16), nullable=False)
    assessment_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rule_version: Mapped[str] = mapped_column(String(64), nullable=False)

    inputs_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    results_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    trace_steps_json: Mapped[list[Any]] = mapped_column(JSON, default=list)

    total_tax_payable: Mapped[float] = mapped_column(Float, default=0.0)
    effective_tax_rate: Mapped[float] = mapped_column(Float, default=0.0)
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )


class ComplianceTaskModel(Base):
    """Database model for tax compliance calendar obligations and due dates."""

    __tablename__ = "compliance_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    taxpayer_profile_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("taxpayer_profiles.id"), nullable=True
    )

    obligation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_family: Mapped[str] = mapped_column(String(64), nullable=False)
    due_date: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )
