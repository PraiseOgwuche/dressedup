from app.config import settings
from app.services.storage.base import StorageProvider
from app.services.storage.local import LocalStorageProvider

_PROVIDERS = {
    "local": LocalStorageProvider,
}


def get_storage_provider() -> StorageProvider:
    provider_cls = _PROVIDERS.get(settings.STORAGE_PROVIDER, LocalStorageProvider)
    return provider_cls()


__all__ = ["StorageProvider", "get_storage_provider"]
