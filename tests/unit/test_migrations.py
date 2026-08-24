"""Unit tests for database tables and fresh metadata creation."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

import taxos.infrastructure.database.models  # noqa: F401
from taxos.infrastructure.database.base import Base


@pytest.mark.asyncio
async def test_fresh_database_table_creation():
    """Verify that all ORM models map to SQLite tables without errors."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def check_tables(connection):
            inspector = inspect(connection)
            table_names = set(inspector.get_table_names())
            expected_tables = {
                "users",
                "organizations",
                "organization_members",
                "api_keys",
                "audit_logs",
                "taxpayer_profiles",
                "saved_calculations",
                "compliance_tasks",
                "seo_routes",
                "seo_redirects",
                "seo_internal_links",
                "tax_countries",
                "tax_states",
                "tax_cities",
                "tax_rules",
                "tax_rule_versions",
                "tax_sources",
                "tax_updates",
                "tax_update_logs",
            }
            for table in expected_tables:
                msg = f"Table '{table}' missing in created tables: {table_names}"
                assert table in table_names, msg

        await conn.run_sync(check_tables)

    await engine.dispose()
