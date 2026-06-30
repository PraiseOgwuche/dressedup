import uuid
from typing import Any

import boto3

from app.config import settings
from app.services.storage.base import StorageProvider

_CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "heic": "image/heic",
    "heif": "image/heif",
}


def _content_type(ext: str) -> str:
    return _CONTENT_TYPES.get(ext.lower(), "application/octet-stream")


class S3StorageProvider(StorageProvider):
    """Uploads to S3 (or S3-compatible e.g. R2) and returns a public HTTPS URL."""

    def __init__(self) -> None:
        if not settings.S3_BUCKET:
            raise ValueError("S3_BUCKET is required when STORAGE_PROVIDER=s3")

        client_kwargs: dict[str, Any] = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self._bucket = settings.S3_BUCKET
        self._client = boto3.client("s3", **client_kwargs)

    def save(self, data: bytes, *, ext: str, subdir: str = "") -> str:
        ext = ext.lstrip(".") or "bin"
        filename = f"{uuid.uuid4().hex}.{ext}"
        key_parts = [subdir.strip("/")] if subdir else []
        key_parts.append(filename)
        key = "/".join(key_parts)

        put_kwargs: dict[str, Any] = {
            "Bucket": self._bucket,
            "Key": key,
            "Body": data,
            "ContentType": _content_type(ext),
        }
        if settings.S3_OBJECT_ACL:
            put_kwargs["ACL"] = settings.S3_OBJECT_ACL

        self._client.put_object(**put_kwargs)
        return self._public_url(key)

    def _public_url(self, key: str) -> str:
        if settings.S3_PUBLIC_BASE_URL:
            return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{key}"

        region = settings.AWS_REGION
        if region == "us-east-1":
            return f"https://{self._bucket}.s3.amazonaws.com/{key}"
        return f"https://{self._bucket}.s3.{region}.amazonaws.com/{key}"
