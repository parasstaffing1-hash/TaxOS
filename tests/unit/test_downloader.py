import pytest
from taxos.application.updater.downloader import DownloadManager, DownloadResult


@pytest.mark.asyncio
async def test_download_manager_init():
    manager = DownloadManager(timeout_seconds=30, max_concurrent=5)
    assert manager.timeout == 30


@pytest.mark.asyncio
async def test_extract_zip(tmp_path):
    import zipfile
    import io
    
    # Create a dummy zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", b"hello world")
        
    zip_bytes = buf.getvalue()
    
    manager = DownloadManager()
    extracted = manager._extract_zip(zip_bytes)
    
    assert "test.txt" in extracted
    assert extracted["test.txt"] == b"hello world"
