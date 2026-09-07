"""Object-storage adapters used by document and report workflows."""

from taxos.infrastructure.storage.object_storage import (
    ObjectStorage,
    ObjectStorageError,
    StoredObject,
    get_object_storage,
)

__all__ = [
    "ObjectStorage",
    "ObjectStorageError",
    "StoredObject",
    "get_object_storage",
]
