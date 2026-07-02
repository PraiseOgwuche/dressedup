from __future__ import annotations

import logging

from app.config import settings
from app.services.stylist.base import StylistProvider
from app.services.stylist.stub_provider import StubStylistProvider

logger = logging.getLogger(__name__)


def get_stylist() -> StylistProvider:
    if settings.STYLIST_PROVIDER == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("STYLIST_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty; using stub.")
            return StubStylistProvider()
        from app.services.stylist.anthropic_provider import AnthropicStylistProvider

        return AnthropicStylistProvider()
    return StubStylistProvider()
