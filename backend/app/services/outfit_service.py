"""Outfit suggestion engine (v3).

Two-layer matching:
  1. Fashion knowledge — color theory, formality, patterns, footwear rules (`app.fashion`).
  2. Personalization — learns from likes, dislikes, and wears (`PreferenceService`).

Picks a cohesive top / bottom / shoes (+ optional outerwear) by scoring combinations,
with variety among near-ties so "Generate" does not repeat the same outfit.
"""

import random
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.fashion import FashionMatcher, MatchContext
from app.fashion.style_rules import needs_outerwear, weather_seasons
from app.models.clothing_item import ClothingItem
from app.services import retrieval_service
from app.services.preference_service import PreferenceService
from app.services.style_signal_service import StyleSignalService
from app.services.stylist_service import StylistService

_SLOT_CAP = 10
_VARIETY_MARGIN = 0.12


class OutfitService:
    TOP_CATEGORIES = {"top", "shirt", "t-shirt", "blouse", "sweater"}
    BOTTOM_CATEGORIES = {"bottom", "pants", "jeans", "shorts", "skirt"}
    SHOE_CATEGORIES = {"shoes", "sneakers", "heels", "boots", "sandals", "footwear"}
    OUTERWEAR_CATEGORIES = {"jacket", "coat", "hoodie", "outerwear"}

    TOP_SUBCATEGORIES = {"sports-bra", "athletic-top", "tracksuit"}
    BOTTOM_SUBCATEGORIES = {"athletic-shorts"}

    @classmethod
    def _context(
        cls,
        weather_tag: Optional[str],
        occasion: Optional[str],
        trend: Optional[str] = None,
    ) -> MatchContext:
        return MatchContext(
            weather_tag=weather_tag,
            occasion=occasion,
            trend=trend,
            target_seasons=weather_seasons(weather_tag),
        )

    @classmethod
    def _score(
        cls,
        db: Session,
        user_id: int,
        garments: List[ClothingItem],
        context: MatchContext,
    ) -> float:
        garments = [g for g in garments if g is not None]
        personal, notes = PreferenceService.personalization_bonus(db, user_id, garments)
        breakdown = FashionMatcher.score_outfit(garments, context, personalization=personal, personal_notes=notes)
        return breakdown.total

    @classmethod
    def _rationale_for(
        cls,
        db: Session,
        user_id: int,
        garments: List[ClothingItem],
        context: MatchContext,
    ) -> Optional[str]:
        garments = [g for g in garments if g is not None]
        personal, notes = PreferenceService.personalization_bonus(db, user_id, garments)
        breakdown = FashionMatcher.score_outfit(garments, context, personalization=personal, personal_notes=notes)
        return breakdown.rationale()

    @classmethod
    def _attach_styling_note(cls, db: Session, user_id: int, payload: dict) -> dict:
        note = StylistService.enhance_outfit(
            db,
            user_id,
            top=payload.get("top"),
            bottom=payload.get("bottom"),
            shoes=payload.get("shoes"),
            outerwear=payload.get("outerwear"),
            occasion=payload.get("occasion"),
            weather_tag=payload.get("weather_tag"),
            trend=payload.get("trend"),
            rule_rationale=payload.get("rationale"),
        )
        if note:
            payload["styling_note"] = note
        return payload

    @staticmethod
    def _candidates(
        items: List[ClothingItem],
        category_set: set,
        weather_tag: Optional[str],
        occasion: Optional[str],
        exclude_ids: Optional[set] = None,
        subcategory_set: Optional[set] = None,
        query=None,
    ) -> List[ClothingItem]:
        exclude_ids = exclude_ids or set()
        subcategory_set = subcategory_set or set()
        pool = [
            i
            for i in items
            if i.id not in exclude_ids
            and i.is_clean
            and (
                i.category.lower() in category_set
                or (i.subcategory or "").lower() in subcategory_set
            )
        ]
        if weather_tag:
            matched = [i for i in pool if not i.weather_tag or weather_tag in i.weather_tag]
            if matched:
                pool = matched
        if occasion:
            matched = [i for i in pool if not i.occasion or occasion in i.occasion]
            if matched:
                pool = matched
        if settings.OUTFIT_EMBEDDINGS_ENABLED:
            # Phase 4 hybrid retrieval: freshness + visual similarity + exploration.
            return retrieval_service.hybrid_pool(pool, _SLOT_CAP, query)
        pool.sort(key=lambda x: x.times_worn or 0)
        return pool[:_SLOT_CAP]

    @staticmethod
    def _retrieval_query(items: List[ClothingItem], *anchors: Optional[ClothingItem]):
        """Vector the hybrid retriever should match against, or None when off."""
        if not settings.OUTFIT_EMBEDDINGS_ENABLED:
            return None
        return retrieval_service.anchor_query(
            anchors, retrieval_service.closet_centroid(items)
        )

    @classmethod
    def _get_owned(
        cls,
        db: Session,
        user_id: int,
        item_id: Optional[int],
    ) -> Optional[ClothingItem]:
        if item_id is None:
            return None
        return (
            db.query(ClothingItem)
            .filter(ClothingItem.id == item_id, ClothingItem.user_id == user_id)
            .first()
        )

    @classmethod
    def get_suggestion(
        cls,
        db: Session,
        user_id: int,
        weather_tag: Optional[str],
        occasion: Optional[str],
        include_alternative: bool,
        exclude_ids: Optional[set] = None,
        swap_slot: Optional[str] = None,
        top_id: Optional[int] = None,
        bottom_id: Optional[int] = None,
        shoes_id: Optional[int] = None,
        outerwear_id: Optional[int] = None,
        trend: Optional[str] = None,
    ):
        if swap_slot:
            return cls._swap_piece(
                db=db,
                user_id=user_id,
                weather_tag=weather_tag,
                occasion=occasion,
                trend=trend,
                include_alternative=include_alternative,
                swap_slot=swap_slot,
                top_id=top_id,
                bottom_id=bottom_id,
                shoes_id=shoes_id,
                outerwear_id=outerwear_id,
            )

        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        context = cls._context(weather_tag, occasion, trend)
        query = cls._retrieval_query(items)

        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, exclude_ids, cls.TOP_SUBCATEGORIES, query
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, exclude_ids, cls.BOTTOM_SUBCATEGORIES, query
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)

        best = cls._best_combo(db, user_id, tops, bottoms, shoes, context)

        chosen_top = best["top"]
        chosen_bottom = best["bottom"]
        chosen_shoes = best["shoes"]
        anchor = chosen_top or chosen_bottom or chosen_shoes

        chosen_outerwear = cls._best_outerwear(
            db, user_id, outerwear, anchor, context, weather_tag,
            ensemble=[chosen_top, chosen_bottom, chosen_shoes],
        )

        alternatives: List[ClothingItem] = []
        if include_alternative and anchor is not None:
            alternatives = cls._alternatives(
                db,
                user_id,
                anchor,
                context,
                tops=tops,
                bottoms=bottoms,
                shoes=shoes,
                chosen={chosen_top, chosen_bottom, chosen_shoes},
            )

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )

        return cls._attach_styling_note(
            db,
            user_id,
            {
            "title": "Today's outfit suggestion",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "trend": trend,
            "rationale": rationale,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": alternatives,
            },
        )

    @classmethod
    def _swap_piece(
        cls,
        db: Session,
        user_id: int,
        weather_tag: Optional[str],
        occasion: Optional[str],
        include_alternative: bool,
        swap_slot: str,
        top_id: Optional[int],
        bottom_id: Optional[int],
        shoes_id: Optional[int],
        outerwear_id: Optional[int],
        trend: Optional[str] = None,
    ):
        valid_slots = {"top", "bottom", "shoes", "outerwear"}
        if swap_slot not in valid_slots:
            raise ValueError(f"Invalid swap_slot: {swap_slot}")

        locked_top = cls._get_owned(db, user_id, top_id)
        locked_bottom = cls._get_owned(db, user_id, bottom_id)
        locked_shoes = cls._get_owned(db, user_id, shoes_id)
        locked_outerwear = cls._get_owned(db, user_id, outerwear_id)

        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        context = cls._context(weather_tag, occasion, trend)

        exclude_ids: set[int] = set()
        if swap_slot == "top" and locked_top:
            exclude_ids.add(locked_top.id)
        elif swap_slot == "bottom" and locked_bottom:
            exclude_ids.add(locked_bottom.id)
        elif swap_slot == "shoes" and locked_shoes:
            exclude_ids.add(locked_shoes.id)
        elif swap_slot == "outerwear" and locked_outerwear:
            exclude_ids.add(locked_outerwear.id)

        query = cls._retrieval_query(
            items, locked_top, locked_bottom, locked_shoes, locked_outerwear
        )
        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, exclude_ids, cls.TOP_SUBCATEGORIES, query
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, exclude_ids, cls.BOTTOM_SUBCATEGORIES, query
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)

        if swap_slot == "top":
            top_opts = tops
            bottom_opts = [locked_bottom] if locked_bottom else (bottoms or [None])
            shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])
        elif swap_slot == "bottom":
            top_opts = [locked_top] if locked_top else (tops or [None])
            bottom_opts = bottoms
            shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])
        elif swap_slot == "shoes":
            top_opts = [locked_top] if locked_top else (tops or [None])
            bottom_opts = [locked_bottom] if locked_bottom else (bottoms or [None])
            shoe_opts = shoes
        else:
            top_opts = [locked_top] if locked_top else (tops or [None])
            bottom_opts = [locked_bottom] if locked_bottom else (bottoms or [None])
            shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])

        if swap_slot == "outerwear":
            chosen_top = locked_top
            chosen_bottom = locked_bottom
            chosen_shoes = locked_shoes
            anchor = chosen_top or chosen_bottom or chosen_shoes
            pool = [o for o in outerwear if not locked_outerwear or o.id != locked_outerwear.id]
            if pool and anchor:
                if settings.OUTFIT_EMBEDDINGS_ENABLED:
                    kept = [g for g in (chosen_top, chosen_bottom, chosen_shoes) if g is not None]
                    chosen_outerwear = max(
                        pool, key=lambda ow: cls._score(db, user_id, [*kept, ow], context)
                    )
                else:
                    chosen_outerwear = max(
                        pool, key=lambda ow: cls._score(db, user_id, [anchor, ow], context)
                    )
            else:
                chosen_outerwear = pool[0] if pool else locked_outerwear
        else:
            best = cls._best_combo(db, user_id, top_opts, bottom_opts, shoe_opts, context)
            chosen_top = best["top"] if swap_slot == "top" else (locked_top or best["top"])
            chosen_bottom = best["bottom"] if swap_slot == "bottom" else (locked_bottom or best["bottom"])
            chosen_shoes = best["shoes"] if swap_slot == "shoes" else (locked_shoes or best["shoes"])
            anchor = chosen_top or chosen_bottom or chosen_shoes
            if locked_outerwear and swap_slot != "outerwear":
                chosen_outerwear = locked_outerwear
            else:
                chosen_outerwear = cls._best_outerwear(
                    db, user_id, outerwear, anchor, context, weather_tag,
                    ensemble=[chosen_top, chosen_bottom, chosen_shoes],
                )

        slot_labels = {
            "top": "top",
            "bottom": "bottom",
            "shoes": "shoes",
            "outerwear": "layer",
        }
        swapped = slot_labels[swap_slot]

        alternatives: List[ClothingItem] = []
        if include_alternative and anchor is not None:
            alternatives = cls._alternatives(
                db,
                user_id,
                anchor,
                context,
                tops=tops,
                bottoms=bottoms,
                shoes=shoes,
                chosen={chosen_top, chosen_bottom, chosen_shoes},
            )

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )
        if rationale:
            rationale = f"Swapped the {swapped} — kept the rest. {rationale}"

        replaced_item = {
            "top": locked_top,
            "bottom": locked_bottom,
            "shoes": locked_shoes,
            "outerwear": locked_outerwear,
        }[swap_slot]

        StyleSignalService.record(
            db,
            user_id,
            "swap",
            top_id=chosen_top.id if chosen_top else None,
            bottom_id=chosen_bottom.id if chosen_bottom else None,
            shoes_id=chosen_shoes.id if chosen_shoes else None,
            outerwear_id=chosen_outerwear.id if chosen_outerwear else None,
            swap_slot=swap_slot,
            replaced_item_id=replaced_item.id if replaced_item else None,
            occasion=occasion,
            weather_tag=weather_tag,
        )

        return cls._attach_styling_note(
            db,
            user_id,
            {
            "title": f"New {swapped} suggestion",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "trend": trend,
            "rationale": rationale,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": alternatives,
            },
        )

    @classmethod
    def _best_combo(
        cls,
        db: Session,
        user_id: int,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        context: MatchContext,
    ) -> dict:
        top_opts = tops or [None]
        bottom_opts = bottoms or [None]
        shoe_opts = shoes or [None]

        scored = []
        for top in top_opts:
            for bottom in bottom_opts:
                if top is None and bottom is None:
                    continue
                for shoe in shoe_opts:
                    score = cls._score(db, user_id, [top, bottom, shoe], context)
                    scored.append((score, {"top": top, "bottom": bottom, "shoes": shoe}))

        if not scored:
            return {"top": None, "bottom": None, "shoes": None}

        best_score = max(score for score, _ in scored)
        near_best = [combo for score, combo in scored if score >= best_score - _VARIETY_MARGIN]
        return random.choice(near_best)

    @classmethod
    def _best_outerwear(
        cls,
        db: Session,
        user_id: int,
        outerwear: List[ClothingItem],
        anchor: Optional[ClothingItem],
        context: MatchContext,
        weather_tag: Optional[str],
        ensemble: Optional[List[ClothingItem]] = None,
    ) -> Optional[ClothingItem]:
        if not outerwear:
            return None
        if weather_tag and not needs_outerwear(weather_tag):
            return None
        if anchor is None:
            return outerwear[0]
        if settings.OUTFIT_EMBEDDINGS_ENABLED and ensemble:
            # Phase 5: judge the layer against the complete outfit, not one anchor.
            chosen = [g for g in ensemble if g is not None]
            return max(outerwear, key=lambda ow: cls._score(db, user_id, [*chosen, ow], context))
        return max(outerwear, key=lambda ow: cls._score(db, user_id, [anchor, ow], context))

    @classmethod
    def _alternatives(
        cls,
        db: Session,
        user_id: int,
        anchor: ClothingItem,
        context: MatchContext,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        chosen: set,
    ) -> List[ClothingItem]:
        def ranked(pool: List[ClothingItem], limit: int) -> List[ClothingItem]:
            remaining = [i for i in pool if i not in chosen]
            remaining.sort(
                key=lambda i: cls._score(db, user_id, [anchor, i], context),
                reverse=True,
            )
            return remaining[:limit]

        return ranked(tops, 2) + ranked(bottoms, 1) + ranked(shoes, 1)

    @classmethod
    def slot_for_item(cls, item: ClothingItem) -> Optional[str]:
        cat = (item.category or "").lower()
        sub = (item.subcategory or "").lower()
        if cat in cls.TOP_CATEGORIES or sub in cls.TOP_SUBCATEGORIES:
            return "top"
        if cat in cls.BOTTOM_CATEGORIES or sub in cls.BOTTOM_SUBCATEGORIES:
            return "bottom"
        if cat in cls.SHOE_CATEGORIES:
            return "shoes"
        if cat in cls.OUTERWEAR_CATEGORIES:
            return "outerwear"
        if cat == "dress":
            return "top"
        return None

    @classmethod
    def suggest_around_item(
        cls,
        db: Session,
        user_id: int,
        item_id: int,
        weather_tag: Optional[str] = None,
        occasion: Optional[str] = None,
    ) -> Optional[dict]:
        """Build an outfit with this piece locked — does not record a swap signal."""
        item = cls._get_owned(db, user_id, item_id)
        if item is None:
            return None
        slot = cls.slot_for_item(item)
        if slot is None:
            return None

        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        context = cls._context(weather_tag, occasion)
        exclude_ids = {item.id}
        query = cls._retrieval_query(items, item)

        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, exclude_ids, cls.TOP_SUBCATEGORIES, query
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, exclude_ids, cls.BOTTOM_SUBCATEGORIES, query
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)

        locked_top = item if slot == "top" else None
        locked_bottom = item if slot == "bottom" else None
        locked_shoes = item if slot == "shoes" else None
        locked_outerwear = item if slot == "outerwear" else None

        top_opts = [locked_top] if locked_top else (tops or [None])
        bottom_opts = [locked_bottom] if locked_bottom else (bottoms or [None])
        shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])

        best = cls._best_combo(db, user_id, top_opts, bottom_opts, shoe_opts, context)
        chosen_top = locked_top or best["top"]
        chosen_bottom = locked_bottom or best["bottom"]
        chosen_shoes = locked_shoes or best["shoes"]
        anchor = chosen_top or chosen_bottom or chosen_shoes
        chosen_outerwear = locked_outerwear or cls._best_outerwear(
            db, user_id, outerwear, anchor, context, weather_tag,
            ensemble=[chosen_top, chosen_bottom, chosen_shoes],
        )

        if not any([chosen_top, chosen_bottom, chosen_shoes]):
            return None

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )
        if rationale:
            rationale = f"Built around your {item.name}. {rationale}"

        return cls._attach_styling_note(
            db,
            user_id,
            {
                "title": f"Pairs with {item.name}",
                "weather_tag": weather_tag,
                "occasion": occasion,
                "trend": None,
                "rationale": rationale,
                "top": chosen_top,
                "bottom": chosen_bottom,
                "shoes": chosen_shoes,
                "outerwear": chosen_outerwear,
                "alternatives": [],
            },
        )
