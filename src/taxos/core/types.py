"""Shared domain types and value objects."""

from __future__ import annotations

from typing import TypeVar
from uuid import UUID

# ── Identity ─────────────────────────────────────────────────────
EntityId = UUID

# ── Generics ─────────────────────────────────────────────────────
T = TypeVar("T")
