"""Download Engine for fetching tax data from various sources."""

from __future__ import annotations

import asyncio
import hashlib
import tempfile
import zipfile
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


@dataclass
class DownloadResult:
    """Result of a download operation."""
    url: str
    content: bytes
    checksum: str
    status_code: int
    is_archive: bool = False
    extracted_files: dict[str, bytes] | None = None


class DownloadManager:
    """Handles resilient, parallel downloading of tax datasets."""

    def __init__(self, timeout_seconds: int = 60, max_concurrent: int = 10):
        self.timeout = timeout_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download(self, url: str) -> DownloadResult:
        """Download a single URL with retries."""
        async with self.semaphore:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
                reraise=True,
            ):
                with attempt:
                    logger.info("downloading_file", url=url, attempt=attempt.retry_state.attempt_number)
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(url, follow_redirects=True)
                        response.raise_for_status()
                        content = response.content
                        
                        checksum = hashlib.sha256(content).hexdigest()
                        
                        result = DownloadResult(
                            url=url,
                            content=content,
                            checksum=checksum,
                            status_code=response.status_code,
                        )
                        
                        # Handle archives if necessary
                        if url.endswith(".zip") or response.headers.get("content-type") == "application/zip":
                            result.is_archive = True
                            result.extracted_files = self._extract_zip(content)
                        elif url.endswith((".tar.gz", ".tgz")):
                            result.is_archive = True
                            result.extracted_files = self._extract_tar(content)
                            
                        return result
        # Fallback if somehow escapes retrying
        raise RuntimeError(f"Failed to download {url}")

    async def download_many(self, urls: list[str]) -> list[DownloadResult | Exception]:
        """Download multiple URLs in parallel."""
        tasks = [self.download(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _extract_zip(self, content: bytes) -> dict[str, bytes]:
        """Extract ZIP contents in memory."""
        extracted = {}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                for file_info in zf.infolist():
                    if not file_info.is_dir():
                        extracted[file_info.filename] = zf.read(file_info.filename)
        finally:
            tmp_path.unlink(missing_ok=True)
            
        return extracted

    def _extract_tar(self, content: bytes) -> dict[str, bytes]:
        """Extract TAR.GZ contents in memory."""
        extracted = {}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            with tarfile.open(tmp_path, "r:gz") as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        f = tf.extractfile(member)
                        if f:
                            extracted[member.name] = f.read()
        finally:
            tmp_path.unlink(missing_ok=True)
            
        return extracted
