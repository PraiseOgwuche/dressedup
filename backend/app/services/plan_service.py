"""Daily plan: assemble outfits for a sequence of activities (e.g. work → gym).

The first activity is what to wear now; later activities are things to pack (their
outfit becomes a packing list). Items already used earlier in the day are excluded
so the same physical garment isn't assigned twice. All picks respect the closet's
clean/laundry state via the outfit engine.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.outfit_service import OutfitService

# Map a high-level activity to the occasion the outfit engine filters on.
_ACTIVITY_OCCASION = {
    "work": "work",
    "gym": "workout",
    "everyday": "everyday",
    "date": "date",
    "party": "party",
    "travel": "travel",
    "outdoor": "outdoor",
    "loungewear": "loungewear",
}


class PlanService:
    @staticmethod
    def daily_plan(
        db: Session,
        user_id: int,
        activities: List[str],
        weather_tag: Optional[str] = None,
    ) -> dict:
        used_ids: set = set()
        planned = []

        for index, activity in enumerate(activities):
            occasion = _ACTIVITY_OCCASION.get(activity, activity)
            suggestion = OutfitService.get_suggestion(
                db=db,
                user_id=user_id,
                weather_tag=weather_tag,
                occasion=occasion,
                include_alternative=False,
                exclude_ids=used_ids,
            )

            chosen = [
                suggestion[slot]
                for slot in ("dress", "top", "bottom", "shoes", "outerwear", "bag", "accessory", "headwear")
                if suggestion.get(slot) is not None
            ]
            for item in chosen:
                used_ids.add(item.id)

            mode = "wear" if index == 0 else "pack"
            planned.append(
                {
                    "activity": activity,
                    "occasion": occasion,
                    "mode": mode,
                    "title": activity.replace("-", " ").title(),
                    "rationale": suggestion.get("rationale"),
                    "top": suggestion.get("top"),
                    "bottom": suggestion.get("bottom"),
                    "shoes": suggestion.get("shoes"),
                    "outerwear": suggestion.get("outerwear"),
                    "dress": suggestion.get("dress"),
                    "packing_list": chosen if mode == "pack" else [],
                }
            )

        return {"weather_tag": weather_tag, "activities": planned}
