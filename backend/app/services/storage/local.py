import uuid
from pathlib import Path

from app.config import settings
from app.services.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Writes files under MEDIA_DIR; FastAPI serves them at MEDIA_URL_PREFIX."""

    def save(self, data: bytes, *, ext: str, subdir: str = "") -> str:
        ext = ext.lstrip(".") or "bin"
        filename = f"{uuid.uuid4().hex}.{ext}"
        directory = Path(settings.MEDIA_DIR) / subdir if subdir else Path(settings.MEDIA_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / filename).write_bytes(data)

        parts = [settings.MEDIA_URL_PREFIX.rstrip("/")]
        if subdir:
            parts.append(subdir.strip("/"))
        parts.append(filename)
        return "/".join(parts)
