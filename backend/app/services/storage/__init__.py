from app.config import settings
from app.services.storage.base import StorageProvider
from app.services.storage.local import LocalStorageProvider
from app.services.storage.s3 import S3StorageProvider

_PROVIDERS: dict[str, type[StorageProvider]] = {
    "local": LocalStorageProvider,
    "s3": S3StorageProvider,
}


def get_storage_provider() -> StorageProvider:
    provider_cls = _PROVIDERS.get(settings.STORAGE_PROVIDER, LocalStorageProvider)
    return provider_cls()


__all__ = ["StorageProvider", "get_storage_provider"]
