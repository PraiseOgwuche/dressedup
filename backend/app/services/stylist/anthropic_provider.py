from __future__ import annotations

import json
import logging
from typing import Any, Optional

import anthropic

from app.config import settings
from app.services.stylist.base import StylistProvider

logger = logging.getLogger(__name__)

_OUTFIT_SYSTEM = (
    "You are DressedUp's personal stylist. Write one warm, specific sentence (max 28 words) "
    "explaining why this outfit works for the user today. Mention colors, occasion, or fit — "
    "never invent items not in the outfit. No bullet points."
)

_GAP_SYSTEM = (
    "You are DressedUp's wardrobe strategist. Write 1–2 sentences on the smartest next purchase "
    "for this closet. Be concrete (category + color), friendly, and under 45 words total."
)


class AnthropicStylistProvider(StylistProvider):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def available(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    def _complete(self, *, system: str, user_payload: dict[str, Any]) -> Optional[str]:
        try:
            response = self._client.messages.create(
                model=settings.STYLIST_MODEL,
                max_tokens=settings.STYLIST_MAX_OUTPUT_TOKENS,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=True),
                    }
                ],
            )
        except Exception:
            logger.exception("stylist LLM call failed")
            return None

        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text.strip())
        merged = " ".join(parts).strip()
        return merged or None

    def outfit_note(
        self,
        *,
        closet: dict,
        outfit: dict,
        context: dict,
        rule_rationale: Optional[str],
    ) -> Optional[str]:
        payload = {
            "closet_summary": closet,
            "outfit": outfit,
            "context": context,
            "rule_engine_hint": rule_rationale,
        }
        return self._complete(system=_OUTFIT_SYSTEM, user_payload=payload)

    def closet_gap_insight(
        self,
        *,
        closet: dict,
        shop_summary: str,
        top_pick: Optional[dict],
    ) -> Optional[str]:
        payload = {
            "closet_summary": closet,
            "shop_summary": shop_summary,
            "top_pick": top_pick,
        }
        return self._complete(system=_GAP_SYSTEM, user_payload=payload)
