from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve `.env` next to the backend package so Alembic/uvicorn work from any working directory.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Load `.env.example` first, then `.env` (so a real `.env` overrides). Missing files are skipped.
    model_config = SettingsConfigDict(
        env_file=(
            str(_BACKEND_ROOT / ".env.example"),
            str(_BACKEND_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENV: str = "development"

    # App Settings
    APP_NAME: str = "DressedUp API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    RUN_MIGRATIONS_ON_STARTUP: bool = False

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI closet ingestion. "stub" returns canned data (no tokens). Set to "anthropic"
    # (and provide ANTHROPIC_API_KEY) to use a real model; falls back to stub if no key.
    VISION_PROVIDER: str = "stub"
    ANTHROPIC_API_KEY: str = ""
    # Cheapest vision-capable Claude model; downscale + small output keep cost ~$0.002/scan.
    VISION_MODEL: str = "claude-haiku-4-5"
    VISION_MAX_IMAGE_PX: int = 768
    VISION_MAX_OUTPUT_TOKENS: int = 600

    # LLM stylist (Phase 4) — outfit notes + shop gap insights. Reuses ANTHROPIC_API_KEY.
    STYLIST_PROVIDER: str = "stub"
    STYLIST_MODEL: str = "claude-haiku-4-5"
    STYLIST_MAX_OUTPUT_TOKENS: int = 400
    # Bulk scan: cap items per batch (bounds token spend) and parallelism for speed.
    MAX_BATCH_ITEMS: int = 15
    INGEST_CONCURRENCY: int = 4
    # Flat-lay scan: max distinct items detected in one photo.
    MAX_MULTI_ITEMS_PER_PHOTO: int = 8
    VISION_MAX_MULTI_OUTPUT_TOKENS: int = 1200
    # Receipt scan: max clothing line items parsed from one receipt photo.
    MAX_RECEIPT_ITEMS: int = 15
    VISION_MAX_RECEIPT_OUTPUT_TOKENS: int = 1500

    # Email import (Mailgun inbound). Each user gets u-{ingest_token}@EMAIL_INGEST_DOMAIN.
    EMAIL_INGEST_ENABLED: bool = False
    EMAIL_INGEST_DOMAIN: str = ""
    MAILGUN_WEBHOOK_SIGNING_KEY: str = ""
    # Allow POST /closet/email-ingest/simulate in production (off by default).
    EMAIL_INGEST_ALLOW_SIMULATE: bool = False

    # Outfit Engine v4 — garment embeddings (FashionCLIP + pgvector).
    # Master switch: when False, no embedding is computed or used in scoring.
    OUTFIT_EMBEDDINGS_ENABLED: bool = False
    # "stub" is deterministic and free (tests/dev). "fashionclip" runs the local
    # ONNX image encoder (download weights with scripts/download_fashionclip.py).
    EMBEDDING_PROVIDER: str = "stub"
    # Where FashionCLIP ONNX weights live (~350 MB, git-ignored).
    EMBEDDING_MODEL_DIR: str = str(_BACKEND_ROOT / "models" / "fashionclip")
    # Cap ONNX intra-op threads: embedding runs at ingest, not in the hot path.
    EMBEDDING_INTRA_OP_THREADS: int = 2

    # Garment background removal (rembg/ONNX, runs locally — no API cost).
    # The cutout becomes thumbnail_url; failures silently keep the original.
    BG_REMOVAL_ENABLED: bool = True
    # u2netp is the lightweight model (~5MB weights) — fits small instances.
    BG_REMOVAL_MODEL: str = "u2netp"
    BG_REMOVAL_MAX_PX: int = 1024

    # Image storage. "local" writes under MEDIA_DIR and serves at MEDIA_URL_PREFIX.
    # "s3" uploads to S3 and returns a public HTTPS URL (see S3_* settings).
    STORAGE_PROVIDER: str = "local"
    MEDIA_DIR: str = str(_BACKEND_ROOT / "media")
    MEDIA_URL_PREFIX: str = "/media"
    MAX_UPLOAD_MB: int = 10

    # S3 object storage (production). Works with AWS S3 or S3-compatible APIs (R2, MinIO).
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    # Optional CDN or custom domain, e.g. https://cdn.example.com
    S3_PUBLIC_BASE_URL: str = ""
    # Optional custom endpoint for R2/MinIO, e.g. https://<account>.r2.cloudflarestorage.com
    S3_ENDPOINT_URL: str = ""
    # Leave empty when bucket uses a public-read bucket policy (recommended).
    # Set to "public-read" only if your bucket allows ACLs.
    S3_OBJECT_ACL: str = ""

    # Morning push notifications (Expo Push API — free). Scheduler ticks every minute.
    NOTIFICATION_SCHEDULER_ENABLED: bool = False
    EXPO_ACCESS_TOKEN: str = ""

    # Trip weather (Open-Meteo — free, no API key).
    WEATHER_API_ENABLED: bool = True
    WEATHER_API_TIMEOUT_SEC: float = 12.0

    # CORS — comma-separated in env files (List[str] would require JSON in .env)
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:8081,http://localhost:19006",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
