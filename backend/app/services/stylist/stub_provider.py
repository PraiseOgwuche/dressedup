from __future__ import annotations

from typing import Optional

from app.services.stylist.base import StylistProvider


class StubStylistProvider(StylistProvider):
    def available(self) -> bool:
        return False

    def outfit_note(
        self,
        *,
        closet: dict,
        outfit: dict,
        context: dict,
        rule_rationale: Optional[str],
    ) -> Optional[str]:
        return None

    def closet_gap_insight(
        self,
        *,
        closet: dict,
        shop_summary: str,
        top_pick: Optional[dict],
    ) -> Optional[str]:
        return None
