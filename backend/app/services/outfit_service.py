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
from app.fashion.direction_profiles import DIRECTION_META, DIRECTIONS
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
    # Full-body garments replace top+bottom — never combined with either.
    DRESS_CATEGORIES = {"dress", "jumpsuit"}
    # Optional finishing slots — attached only when they don't hurt the look.
    BAG_CATEGORIES = {"bag"}
    ACCESSORY_CATEGORIES = {"accessory", "jewelry"}
    HEADWEAR_CATEGORIES = {"headwear", "hat"}

    TOP_SUBCATEGORIES = {"sports-bra", "athletic-top", "tracksuit"}
    BOTTOM_SUBCATEGORIES = {"athletic-shorts"}
    ACCESSORY_SLOTS = ("bag", "accessory", "headwear")

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
            dress=payload.get("dress"),
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
        dress_id: Optional[int] = None,
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
                dress_id=dress_id,
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
        dresses = cls._candidates(items, cls.DRESS_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)

        best = cls._best_combo(db, user_id, tops, bottoms, shoes, context, dresses=dresses)

        chosen_dress = best["dress"]
        chosen_top = best["top"]
        chosen_bottom = best["bottom"]
        chosen_shoes = best["shoes"]
        anchor = chosen_dress or chosen_top or chosen_bottom or chosen_shoes

        chosen_outerwear = cls._best_outerwear(
            db, user_id, outerwear, anchor, context, weather_tag,
            ensemble=[chosen_dress, chosen_top, chosen_bottom, chosen_shoes],
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
                chosen={chosen_dress, chosen_top, chosen_bottom, chosen_shoes},
            )

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_dress, chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )

        payload = {
            "title": "Today's outfit suggestion",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "trend": trend,
            "rationale": rationale,
            "dress": chosen_dress,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": alternatives,
        }
        payload = cls._attach_accessories(
            db,
            user_id,
            payload,
            cls._accessory_pools(items, weather_tag, occasion, exclude_ids, query),
            context,
        )
        return cls._attach_styling_note(db, user_id, payload)

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
        dress_id: Optional[int] = None,
        trend: Optional[str] = None,
    ):
        valid_slots = {"top", "bottom", "shoes", "outerwear", "dress"}
        if swap_slot not in valid_slots:
            raise ValueError(f"Invalid swap_slot: {swap_slot}")

        locked_top = cls._get_owned(db, user_id, top_id)
        locked_bottom = cls._get_owned(db, user_id, bottom_id)
        locked_shoes = cls._get_owned(db, user_id, shoes_id)
        locked_outerwear = cls._get_owned(db, user_id, outerwear_id)
        locked_dress = cls._get_owned(db, user_id, dress_id)

        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        context = cls._context(weather_tag, occasion, trend)

        locked_for_slot = {
            "top": locked_top,
            "bottom": locked_bottom,
            "shoes": locked_shoes,
            "outerwear": locked_outerwear,
            "dress": locked_dress,
        }
        exclude_ids: set[int] = set()
        if locked_for_slot.get(swap_slot):
            exclude_ids.add(locked_for_slot[swap_slot].id)

        query = cls._retrieval_query(
            items, locked_top, locked_bottom, locked_shoes, locked_outerwear, locked_dress
        )
        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, exclude_ids, cls.TOP_SUBCATEGORIES, query
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, exclude_ids, cls.BOTTOM_SUBCATEGORIES, query
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)
        dresses = cls._candidates(items, cls.DRESS_CATEGORIES, weather_tag, occasion, exclude_ids, query=query)

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

        chosen_dress: Optional[ClothingItem] = None
        if swap_slot == "outerwear":
            chosen_top = locked_top
            chosen_bottom = locked_bottom
            chosen_shoes = locked_shoes
            chosen_dress = locked_dress
            anchor = chosen_dress or chosen_top or chosen_bottom or chosen_shoes
            pool = [o for o in outerwear if not locked_outerwear or o.id != locked_outerwear.id]
            if pool and anchor:
                if settings.OUTFIT_EMBEDDINGS_ENABLED:
                    kept = [
                        g
                        for g in (chosen_dress, chosen_top, chosen_bottom, chosen_shoes)
                        if g is not None
                    ]
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
            if swap_slot == "dress":
                # Swapping the dress: other dresses compete with separates.
                dress_opts = dresses
                top_opts = tops or [None]
                bottom_opts = bottoms or [None]
                shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])
            elif locked_dress:
                # A dress anchors the look — only the swapped slot may change.
                dress_opts = [locked_dress]
                top_opts = [None]
                bottom_opts = [None]
            else:
                dress_opts = []

            best = cls._best_combo(
                db, user_id, top_opts, bottom_opts, shoe_opts, context, dresses=dress_opts
            )
            chosen_dress = best["dress"]
            if chosen_dress is not None:
                chosen_top = None
                chosen_bottom = None
            else:
                chosen_top = best["top"] if swap_slot == "top" else (locked_top or best["top"])
                chosen_bottom = best["bottom"] if swap_slot == "bottom" else (locked_bottom or best["bottom"])
            chosen_shoes = best["shoes"] if swap_slot == "shoes" else (locked_shoes or best["shoes"])
            anchor = chosen_dress or chosen_top or chosen_bottom or chosen_shoes
            if locked_outerwear and swap_slot != "outerwear":
                chosen_outerwear = locked_outerwear
            else:
                chosen_outerwear = cls._best_outerwear(
                    db, user_id, outerwear, anchor, context, weather_tag,
                    ensemble=[chosen_dress, chosen_top, chosen_bottom, chosen_shoes],
                )

        slot_labels = {
            "top": "top",
            "bottom": "bottom",
            "shoes": "shoes",
            "outerwear": "layer",
            "dress": "dress",
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
                chosen={chosen_dress, chosen_top, chosen_bottom, chosen_shoes},
            )

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_dress, chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )
        if rationale:
            rationale = f"Swapped the {swapped} — kept the rest. {rationale}"

        replaced_item = locked_for_slot[swap_slot]

        StyleSignalService.record(
            db,
            user_id,
            "swap",
            top_id=chosen_top.id if chosen_top else None,
            bottom_id=chosen_bottom.id if chosen_bottom else None,
            shoes_id=chosen_shoes.id if chosen_shoes else None,
            outerwear_id=chosen_outerwear.id if chosen_outerwear else None,
            dress_id=chosen_dress.id if chosen_dress else None,
            swap_slot=swap_slot,
            replaced_item_id=replaced_item.id if replaced_item else None,
            occasion=occasion,
            weather_tag=weather_tag,
        )

        payload = {
            "title": f"New {swapped} suggestion",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "trend": trend,
            "rationale": rationale,
            "dress": chosen_dress,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": alternatives,
        }
        payload = cls._attach_accessories(
            db,
            user_id,
            payload,
            cls._accessory_pools(items, weather_tag, occasion, exclude_ids, query),
            context,
        )
        return cls._attach_styling_note(db, user_id, payload)

    @classmethod
    def _best_combo(
        cls,
        db: Session,
        user_id: int,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        context: MatchContext,
        dresses: Optional[List[ClothingItem]] = None,
    ) -> dict:
        top_opts = tops or [None]
        bottom_opts = bottoms or [None]
        shoe_opts = shoes or [None]
        empty = {"top": None, "bottom": None, "shoes": None, "dress": None}

        scored = []
        for top in top_opts:
            for bottom in bottom_opts:
                if top is None and bottom is None:
                    continue
                for shoe in shoe_opts:
                    score = cls._score(db, user_id, [top, bottom, shoe], context)
                    scored.append(
                        (score, {**empty, "top": top, "bottom": bottom, "shoes": shoe})
                    )

        # Full-body garments compete as an alternative combo family: a dress
        # replaces top+bottom, never mixes with either (slot exclusion rule).
        for dress in dresses or []:
            for shoe in shoe_opts:
                score = cls._score(db, user_id, [dress, shoe], context)
                scored.append((score, {**empty, "dress": dress, "shoes": shoe}))

        if not scored:
            return dict(empty)

        best_score = max(score for score, _ in scored)
        near_best = [combo for score, combo in scored if score >= best_score - _VARIETY_MARGIN]
        return random.choice(near_best)

    @classmethod
    def _scored_combos(
        cls,
        db: Session,
        user_id: int,
        tops: List[ClothingItem],
        bottoms: List[ClothingItem],
        shoes: List[ClothingItem],
        dresses: List[ClothingItem],
        context: MatchContext,
    ) -> list[tuple[float, dict]]:
        """Every candidate combo with its score, best first. Deterministic."""
        empty = {"top": None, "bottom": None, "shoes": None, "dress": None}
        scored: list[tuple[float, dict]] = []
        for top in tops or [None]:
            for bottom in bottoms or [None]:
                if top is None and bottom is None:
                    continue
                for shoe in shoes or [None]:
                    score = cls._score(db, user_id, [top, bottom, shoe], context)
                    scored.append((score, {**empty, "top": top, "bottom": bottom, "shoes": shoe}))
        for dress in dresses:
            for shoe in shoes or [None]:
                score = cls._score(db, user_id, [dress, shoe], context)
                scored.append((score, {**empty, "dress": dress, "shoes": shoe}))
        scored.sort(key=lambda pair: -pair[0])
        return scored

    @staticmethod
    def _combo_ids(combo: dict) -> set[int]:
        return {g.id for g in combo.values() if g is not None}

    @classmethod
    def get_directions(
        cls,
        db: Session,
        user_id: int,
        weather_tag: Optional[str],
        occasion: Optional[str],
    ) -> dict:
        """Three intentionally different looks — one per styling direction.

        Each direction rescores the same candidate pools with its own profile,
        and later directions avoid combos that overlap an earlier pick by more
        than one piece (so results are never one-item substitutions unless the
        closet is too small to do better).
        """
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        query = cls._retrieval_query(items)

        tops = cls._candidates(
            items, cls.TOP_CATEGORIES, weather_tag, occasion, None, cls.TOP_SUBCATEGORIES, query
        )
        bottoms = cls._candidates(
            items, cls.BOTTOM_CATEGORIES, weather_tag, occasion, None, cls.BOTTOM_SUBCATEGORIES, query
        )
        shoes = cls._candidates(items, cls.SHOE_CATEGORIES, weather_tag, occasion, None, query=query)
        outerwear = cls._candidates(items, cls.OUTERWEAR_CATEGORIES, weather_tag, occasion, None, query=query)
        dresses = cls._candidates(items, cls.DRESS_CATEGORIES, weather_tag, occasion, None, query=query)
        accessory_pools = cls._accessory_pools(items, weather_tag, occasion, None, query)

        directions: list[dict] = []
        prior_picks: list[set[int]] = []

        for direction in DIRECTIONS:
            context = cls._context(weather_tag, occasion)
            context.direction = direction

            scored = cls._scored_combos(db, user_id, tops, bottoms, shoes, dresses, context)
            if not scored:
                continue

            # Strictest overlap bar first (≤1 shared piece with every earlier
            # direction), relaxing only when the closet leaves no choice.
            chosen_combo = None
            for max_shared in (1, 2, 99):
                for _, combo in scored:
                    ids = cls._combo_ids(combo)
                    if all(len(ids & prior) <= max_shared for prior in prior_picks):
                        chosen_combo = combo
                        break
                if chosen_combo is not None:
                    break

            chosen_dress = chosen_combo["dress"]
            chosen_top = chosen_combo["top"]
            chosen_bottom = chosen_combo["bottom"]
            chosen_shoes = chosen_combo["shoes"]
            anchor = chosen_dress or chosen_top or chosen_bottom or chosen_shoes
            chosen_outerwear = cls._best_outerwear(
                db, user_id, outerwear, anchor, context, weather_tag,
                ensemble=[chosen_dress, chosen_top, chosen_bottom, chosen_shoes],
            )

            rationale = cls._rationale_for(
                db,
                user_id,
                [chosen_dress, chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
                context,
            )

            payload = {
                "direction": direction,
                "label": DIRECTION_META[direction]["label"],
                "tagline": DIRECTION_META[direction]["tagline"],
                "title": f"{DIRECTION_META[direction]['label']} look",
                "weather_tag": weather_tag,
                "occasion": occasion,
                "trend": None,
                "rationale": rationale,
                "dress": chosen_dress,
                "top": chosen_top,
                "bottom": chosen_bottom,
                "shoes": chosen_shoes,
                "outerwear": chosen_outerwear,
                "alternatives": [],
            }
            payload = cls._attach_accessories(db, user_id, payload, accessory_pools, context)
            directions.append(payload)
            prior_picks.append(cls._combo_ids(chosen_combo))

        return {"weather_tag": weather_tag, "occasion": occasion, "directions": directions}

    @classmethod
    def _accessory_pools(
        cls,
        items: List[ClothingItem],
        weather_tag: Optional[str],
        occasion: Optional[str],
        exclude_ids: Optional[set],
        query,
    ) -> dict[str, List[ClothingItem]]:
        return {
            "bag": cls._candidates(items, cls.BAG_CATEGORIES, weather_tag, occasion, exclude_ids, query=query),
            "accessory": cls._candidates(items, cls.ACCESSORY_CATEGORIES, weather_tag, occasion, exclude_ids, query=query),
            "headwear": cls._candidates(items, cls.HEADWEAR_CATEGORIES, weather_tag, occasion, exclude_ids, query=query),
        }

    @classmethod
    def _attach_accessories(
        cls,
        db: Session,
        user_id: int,
        payload: dict,
        pools: dict[str, List[ClothingItem]],
        context: MatchContext,
    ) -> dict:
        """Add each finishing piece only when it improves the scored look —
        a complete outfit never *requires* accessories."""
        ensemble = [
            payload.get(slot)
            for slot in ("dress", "top", "bottom", "shoes", "outerwear")
            if payload.get(slot) is not None
        ]
        if not ensemble:
            for slot in cls.ACCESSORY_SLOTS:
                payload[slot] = None
            return payload

        base_score = cls._score(db, user_id, ensemble, context)
        for slot in cls.ACCESSORY_SLOTS:
            chosen = None
            pool = pools.get(slot) or []
            if pool:
                best = max(pool, key=lambda a: cls._score(db, user_id, [*ensemble, a], context))
                if cls._score(db, user_id, [*ensemble, best], context) > base_score:
                    chosen = best
                    ensemble.append(best)
                    base_score = cls._score(db, user_id, ensemble, context)
            payload[slot] = chosen
        return payload

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
        if cat in cls.DRESS_CATEGORIES or sub == "jumpsuit":
            return "dress"
        if cat in cls.BAG_CATEGORIES:
            return "bag"
        if cat in cls.ACCESSORY_CATEGORIES:
            return "accessory"
        if cat in cls.HEADWEAR_CATEGORIES:
            return "headwear"
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
        locked_dress = item if slot == "dress" else None
        locked_accessory = item if slot in cls.ACCESSORY_SLOTS else None

        if locked_dress:
            top_opts, bottom_opts = [None], [None]
            dress_opts: List[ClothingItem] = [locked_dress]
        else:
            top_opts = [locked_top] if locked_top else (tops or [None])
            bottom_opts = [locked_bottom] if locked_bottom else (bottoms or [None])
            dress_opts = []
        shoe_opts = [locked_shoes] if locked_shoes else (shoes or [None])

        best = cls._best_combo(
            db, user_id, top_opts, bottom_opts, shoe_opts, context, dresses=dress_opts
        )
        chosen_dress = locked_dress or best["dress"]
        chosen_top = None if chosen_dress else (locked_top or best["top"])
        chosen_bottom = None if chosen_dress else (locked_bottom or best["bottom"])
        chosen_shoes = locked_shoes or best["shoes"]
        anchor = chosen_dress or chosen_top or chosen_bottom or chosen_shoes
        chosen_outerwear = locked_outerwear or cls._best_outerwear(
            db, user_id, outerwear, anchor, context, weather_tag,
            ensemble=[chosen_dress, chosen_top, chosen_bottom, chosen_shoes],
        )

        if not any([chosen_dress, chosen_top, chosen_bottom, chosen_shoes]):
            return None

        rationale = cls._rationale_for(
            db,
            user_id,
            [chosen_dress, chosen_top, chosen_bottom, chosen_shoes, chosen_outerwear],
            context,
        )
        if rationale:
            rationale = f"Built around your {item.name}. {rationale}"

        payload = {
            "title": f"Pairs with {item.name}",
            "weather_tag": weather_tag,
            "occasion": occasion,
            "trend": None,
            "rationale": rationale,
            "dress": chosen_dress,
            "top": chosen_top,
            "bottom": chosen_bottom,
            "shoes": chosen_shoes,
            "outerwear": chosen_outerwear,
            "alternatives": [],
        }
        payload = cls._attach_accessories(
            db,
            user_id,
            payload,
            cls._accessory_pools(items, weather_tag, occasion, exclude_ids, query),
            context,
        )
        if locked_accessory is not None:
            payload[slot] = locked_accessory
        return cls._attach_styling_note(db, user_id, payload)
