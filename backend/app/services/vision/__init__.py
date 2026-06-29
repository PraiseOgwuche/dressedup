import logging

from app.config import settings
from app.services.vision.base import VisionProvider
from app.services.vision.stub import StubVisionProvider

logger = logging.getLogger(__name__)


def get_vision_provider() -> VisionProvider:
    """Resolve the configured provider.

    Defaults to the free stub. "anthropic" is used only when an API key is present;
    otherwise we fall back to the stub so a misconfiguration never spends money or
    crashes ingestion. Real providers are imported lazily to keep their heavier
    dependencies off the default (free) path.
    """
    if settings.VISION_PROVIDER == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("VISION_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty; using stub.")
            return StubVisionProvider()
        from app.services.vision.anthropic_provider import AnthropicVisionProvider

        return AnthropicVisionProvider()

    return StubVisionProvider()


__all__ = ["VisionProvider", "get_vision_provider"]
