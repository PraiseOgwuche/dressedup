from __future__ import annotations

from typing import Optional, Protocol


class StylistProvider(Protocol):
    def available(self) -> bool: ...

    def outfit_note(
        self,
        *,
        closet: dict,
        outfit: dict,
        context: dict,
        rule_rationale: Optional[str],
    ) -> Optional[str]: ...

    def closet_gap_insight(
        self,
        *,
        closet: dict,
        shop_summary: str,
        top_pick: Optional[dict],
    ) -> Optional[str]: ...
