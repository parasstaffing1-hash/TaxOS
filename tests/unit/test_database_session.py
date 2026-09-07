"""Tests for database URL normalization."""

from taxos.infrastructure.database.session import normalize_database_url


def test_plain_postgres_url_uses_asyncpg_driver() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@host:1234/db?sslmode=require")
        == "postgresql+asyncpg://user:pass@host:1234/db?sslmode=require"
    )


def test_postgres_shorthand_url_uses_asyncpg_driver() -> None:
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )


def test_non_postgres_urls_are_unchanged() -> None:
    assert normalize_database_url("sqlite+aiosqlite:///taxos.db") == "sqlite+aiosqlite:///taxos.db"
