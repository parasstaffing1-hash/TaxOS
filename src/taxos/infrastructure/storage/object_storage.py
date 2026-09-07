"""Portable object storage for uploaded documents and generated reports.

The production adapter uses Cloudflare R2 through its S3-compatible API. A
small local adapter keeps development and tests self-contained without
requiring cloud credentials.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from taxos.core.config import Settings, get_settings

MAX_OBJECT_KEY_BYTES = 1024
NOT_FOUND_ERROR_CODES = {"404", "NoSuchKey", "NotFound"}


class ObjectStorageError(RuntimeError):
    """Raised when an object-storage operation cannot be completed."""


@dataclass(frozen=True)
class StoredObject:
    """Metadata returned after storing an object."""

    key: str
    size: int
    content_type: str
    etag: str
    backend: str


class ObjectStorage(Protocol):
    """Async interface shared by local and R2 object storage."""

    async def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str,
        content_disposition: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject:
        """Store bytes under a validated object key."""

    async def get_bytes(self, key: str) -> bytes | None:
        """Read an object, returning ``None`` when it does not exist."""

    async def delete(self, key: str) -> None:
        """Delete an object if it exists."""


def _validate_key(key: str) -> str:
    """Reject absolute, traversal, and malformed object keys."""
    normalized = key.strip()
    if not normalized or len(normalized.encode("utf-8")) > MAX_OBJECT_KEY_BYTES:
        raise ValueError("Object key is empty or exceeds the maximum length")
    if "\x00" in normalized or normalized.startswith("/"):
        raise ValueError("Object key contains an invalid character")
    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ValueError("Object key contains an invalid path segment")
    return normalized


def _etag(payload: bytes) -> str:
    """Return a deterministic local ETag for parity with cloud metadata."""
    return hashlib.md5(payload, usedforsecurity=False).hexdigest()


class LocalObjectStorage:
    """Filesystem-backed adapter for development and single-host fallback."""

    backend = "local"

    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def _path_for_key(self, key: str) -> Path:
        normalized = _validate_key(key)
        candidate = (self.root / PurePosixPath(normalized)).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("Object key escapes the local storage root")
        return candidate

    async def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str,
        content_disposition: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject:
        del content_disposition, metadata
        path = self._path_for_key(key)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        try:
            await asyncio.to_thread(write)
        except OSError as exc:
            raise ObjectStorageError("Local object storage write failed") from exc
        return StoredObject(
            key=_validate_key(key),
            size=len(payload),
            content_type=content_type,
            etag=_etag(payload),
            backend=self.backend,
        )

    async def get_bytes(self, key: str) -> bytes | None:
        path = self._path_for_key(key)
        if not path.is_file():
            return None
        try:
            return await asyncio.to_thread(path.read_bytes)
        except OSError as exc:
            raise ObjectStorageError("Local object storage read failed") from exc

    async def delete(self, key: str) -> None:
        path = self._path_for_key(key)

        def remove() -> None:
            try:
                path.unlink()
            except FileNotFoundError:
                return

        try:
            await asyncio.to_thread(remove)
        except OSError as exc:
            raise ObjectStorageError("Local object storage delete failed") from exc


class R2ObjectStorage:
    """Cloudflare R2 adapter using the S3-compatible API."""

    backend = "r2"

    def __init__(self, settings: Settings) -> None:
        if not settings.R2_ENDPOINT or not settings.R2_BUCKET:
            raise ObjectStorageError("R2 endpoint and bucket must be configured")
        if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
            raise ObjectStorageError("R2 access credentials must be configured")

        self.bucket = settings.R2_BUCKET
        self.client = boto3.client(
            service_name="s3",
            endpoint_url=settings.R2_ENDPOINT.rstrip("/"),
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    async def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str,
        content_disposition: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject:
        normalized = _validate_key(key)
        kwargs: dict[str, object] = {
            "Bucket": self.bucket,
            "Key": normalized,
            "Body": payload,
            "ContentType": content_type,
        }
        if content_disposition:
            kwargs["ContentDisposition"] = content_disposition
        if metadata:
            kwargs["Metadata"] = dict(metadata)

        try:
            response = await asyncio.to_thread(self.client.put_object, **kwargs)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("R2 object upload failed") from exc

        raw_etag = str(response.get("ETag", "")).strip('"')
        return StoredObject(
            key=normalized,
            size=len(payload),
            content_type=content_type,
            etag=raw_etag,
            backend=self.backend,
        )

    async def get_bytes(self, key: str) -> bytes | None:
        normalized = _validate_key(key)

        def read() -> bytes | None:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=normalized)
            except ClientError as exc:
                error_code = str(exc.response.get("Error", {}).get("Code", ""))
                if error_code in NOT_FOUND_ERROR_CODES:
                    return None
                raise
            body = response["Body"]
            try:
                return cast("bytes", body.read())
            finally:
                body.close()

        try:
            return await asyncio.to_thread(read)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("R2 object read failed") from exc

    async def delete(self, key: str) -> None:
        normalized = _validate_key(key)
        try:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=self.bucket,
                Key=normalized,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("R2 object delete failed") from exc


def get_object_storage(settings: Settings | None = None) -> ObjectStorage:
    """Build the configured storage adapter for the current process."""
    active_settings = settings or get_settings()
    if active_settings.STORAGE_BACKEND == "r2":
        return R2ObjectStorage(active_settings)
    return LocalObjectStorage(active_settings.STORAGE_LOCAL_ROOT)
