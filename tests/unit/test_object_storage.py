"""Tests for local object storage and R2 configuration validation."""

import pytest

from taxos.core.config import Settings
from taxos.infrastructure.storage.object_storage import LocalObjectStorage


@pytest.mark.asyncio
async def test_local_object_storage_roundtrip_and_delete(tmp_path) -> None:
    storage = LocalObjectStorage(str(tmp_path))

    stored = await storage.put_bytes(
        "documents/doc_123/form16.pdf",
        b"tax document",
        content_type="application/pdf",
    )

    assert stored.backend == "local"
    assert stored.size == 12
    assert await storage.get_bytes(stored.key) == b"tax document"

    await storage.delete(stored.key)
    assert await storage.get_bytes(stored.key) is None


@pytest.mark.asyncio
async def test_local_object_storage_rejects_traversal(tmp_path) -> None:
    storage = LocalObjectStorage(str(tmp_path))

    with pytest.raises(ValueError, match="invalid path segment"):
        await storage.put_bytes("documents/../secret.txt", b"secret", content_type="text/plain")


def test_r2_settings_require_all_connection_values() -> None:
    with pytest.raises(ValueError, match="R2 storage requires"):
        Settings(STORAGE_BACKEND="r2")


def test_r2_settings_accept_connection_values() -> None:
    settings = Settings(
        STORAGE_BACKEND="r2",
        R2_ENDPOINT="https://account.r2.cloudflarestorage.com",
        R2_BUCKET="taxos-documents",
        R2_ACCESS_KEY_ID="access-key",
        R2_SECRET_ACCESS_KEY="secret-key",
    )

    assert settings.STORAGE_BACKEND == "r2"
