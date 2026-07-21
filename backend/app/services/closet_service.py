from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.fashion.knowledge import gap_priorities
from app.models.clothing_item import ClothingItem
from app.models.outfit_feedback import OutfitFeedback
from app.models.social_post import SocialPost
from app.models.style_signal import StyleSignal
from app.schemas.closet import (
    ClosetGap,
    ClosetGapsResponse,
    ClosetItemContext,
    ClosetItemUsage,
    ClosetPairPreview,
    ClothingItemCreate,
    ClothingItemUpdate,
)
from app.schemas.ingestion import CutoutBackfillResult
from app.services.embedding_service import EmbeddingService
from app.services.image_processing import fetch_stored_image_bytes, remove_background
from app.services.ingestion_service import IngestionService
from app.services.outfit_service import OutfitService
from app.services.storage import get_storage_provider

# Laundry is "due" once at least this many launderable items are dirty, or when an
# essential category has run out of clean options (handled separately).
_LAUNDRY_DUE_THRESHOLD = 8
_ESSENTIAL_CATEGORIES = ("top", "bottom", "underwear")
_GAP_TITLES = {
    "bottom": "Bottoms gap",
    "footwear": "Shoes gap",
    "top": "Tops gap",
    "outerwear": "Layers gap",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ClosetService:
    @staticmethod
    def list_items(db: Session, user_id: int):
        return (
            db.query(ClothingItem)
            .filter(ClothingItem.user_id == user_id)
            .order_by(ClothingItem.created_at.desc())
            .all()
        )

    @staticmethod
    def get_item(db: Session, user_id: int, item_id: int):
        item = (
            db.query(ClothingItem)
            .filter(ClothingItem.id == item_id, ClothingItem.user_id == user_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clothing item not found",
            )
        return item

    @staticmethod
    def create_item(db: Session, user_id: int, payload: ClothingItemCreate):
        data = payload.model_dump()
        if data.get("tags") is None:
            data["tags"] = []
        item = ClothingItem(user_id=user_id, **data)
        db.add(item)
        db.commit()
        db.refresh(item)
        EmbeddingService.embed_item(db, item)
        return item

    @staticmethod
    def update_item(db: Session, user_id: int, item_id: int, payload: ClothingItemUpdate):
        item = ClosetService.get_item(db, user_id, item_id)
        update_data = payload.model_dump(exclude_unset=True)
        photo_changed = any(
            key in update_data and update_data[key] != getattr(item, key)
            for key in ("image_url", "thumbnail_url")
        )
        for key, value in update_data.items():
            setattr(item, key, value)
        if photo_changed:
            EmbeddingService.mark_stale(item)
        db.add(item)
        db.commit()
        db.refresh(item)
        if photo_changed:
            EmbeddingService.embed_item(db, item)
        return item

    @staticmethod
    def delete_item(db: Session, user_id: int, item_id: int):
        item = ClosetService.get_item(db, user_id, item_id)
        db.delete(item)
        db.commit()

    @staticmethod
    def item_context(db: Session, user_id: int, item_id: int) -> ClosetItemContext:
        item = ClosetService.get_item(db, user_id, item_id)
        slot = OutfitService.slot_for_item(item)

        feedback_count = (
            db.query(OutfitFeedback)
            .filter(OutfitFeedback.user_id == user_id)
            .filter(
                or_(
                    OutfitFeedback.top_id == item_id,
                    OutfitFeedback.bottom_id == item_id,
                    OutfitFeedback.shoes_id == item_id,
                    OutfitFeedback.outerwear_id == item_id,
                    OutfitFeedback.dress_id == item_id,
                )
            )
            .count()
        )
        signal_count = (
            db.query(StyleSignal)
            .filter(StyleSignal.user_id == user_id)
            .filter(
                or_(
                    StyleSignal.top_id == item_id,
                    StyleSignal.bottom_id == item_id,
                    StyleSignal.shoes_id == item_id,
                    StyleSignal.outerwear_id == item_id,
                    StyleSignal.dress_id == item_id,
                    StyleSignal.replaced_item_id == item_id,
                )
            )
            .count()
        )
        post_count = (
            db.query(SocialPost)
            .filter(SocialPost.user_id == user_id)
            .filter(
                or_(
                    SocialPost.top_id == item_id,
                    SocialPost.bottom_id == item_id,
                    SocialPost.shoes_id == item_id,
                    SocialPost.outerwear_id == item_id,
                )
            )
            .count()
        )
        looks_count = feedback_count + post_count

        pair_preview = None
        preview = OutfitService.suggest_around_item(db, user_id, item_id)
        if preview:
            pair_preview = ClosetPairPreview(
                title=preview.get("title") or f"Pairs with {item.name}",
                weather_tag=preview.get("weather_tag"),
                occasion=preview.get("occasion"),
                rationale=preview.get("rationale"),
                styling_note=preview.get("styling_note"),
                top=preview.get("top"),
                bottom=preview.get("bottom"),
                shoes=preview.get("shoes"),
                outerwear=preview.get("outerwear"),
            )

        return ClosetItemContext(
            item=item,
            slot=slot,
            usage=ClosetItemUsage(
                feedback_count=feedback_count,
                signal_count=signal_count,
                post_count=post_count,
                looks_count=looks_count,
            ),
            pair_preview=pair_preview,
        )

    @staticmethod
    def wardrobe_gaps(db: Session, user_id: int) -> ClosetGapsResponse:
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        by_category: Counter[str] = Counter(
            (item.category or "unknown").lower() for item in items
        )
        by_slot: Counter[str] = Counter()
        for item in items:
            slot = OutfitService.slot_for_item(item) or "other"
            by_slot[slot] += 1

        gaps: list[ClosetGap] = []
        for row in sorted(gap_priorities(), key=lambda r: -float(r.get("unlock_weight", 0))):
            category = str(row.get("category", ""))
            count = int(by_category.get(category, 0))
            target = 2
            if count < target:
                gaps.append(
                    ClosetGap(
                        category=category,
                        closet_count=count,
                        target=target,
                        title=_GAP_TITLES.get(category, f"{category.title()} gap"),
                        reason=str(
                            row.get("hint", "Add a versatile piece to unlock more outfits.")
                        ),
                    )
                )

        tops = by_slot.get("top", 0)
        bottoms = by_slot.get("bottom", 0)
        if gaps:
            summary = gaps[0].reason
        elif tops >= 3 and bottoms > 0 and tops >= bottoms * 2:
            summary = (
                f"You have {tops} tops and only {bottoms} bottoms — bottoms unlock more outfits."
            )
        elif not items:
            summary = "Your closet is empty — add a few pieces to start building looks."
        else:
            summary = f"{len(items)} pieces across your wardrobe — coverage looks solid."

        return ClosetGapsResponse(
            by_category=dict(by_category),
            by_slot=dict(by_slot),
            gaps=gaps,
            summary=summary,
            total_items=len(items),
        )

    @staticmethod
    def replace_photo(
        db: Session,
        user_id: int,
        item_id: int,
        garment_bytes: bytes,
        garment_ext: str,
    ):
        """Swap an item's photo + rembg thumbnail without re-running vision."""
        ClosetService.get_item(db, user_id, item_id)
        storage = get_storage_provider()
        image_url = storage.save(garment_bytes, ext=garment_ext, subdir="items")
        thumbnail_url = IngestionService._save_cutout(garment_bytes, storage, image_url)
        return ClosetService.update_item(
            db,
            user_id,
            item_id,
            ClothingItemUpdate(image_url=image_url, thumbnail_url=thumbnail_url),
        )

    @staticmethod
    def backfill_cutouts(
        db: Session,
        user_id: int,
        *,
        limit: int = 20,
    ) -> CutoutBackfillResult:
        """Generate rembg thumbnails for items still using the original photo."""
        candidates = (
            db.query(ClothingItem)
            .filter(ClothingItem.user_id == user_id)
            .filter(ClothingItem.image_url.isnot(None))
            .order_by(ClothingItem.created_at.desc())
            .limit(max(1, min(limit, 50)) * 3)
            .all()
        )
        items = [
            item
            for item in candidates
            if not item.thumbnail_url
            or item.thumbnail_url == item.image_url
            or "/cutouts/" not in (item.thumbnail_url or "")
        ][: max(1, min(limit, 50))]

        storage = get_storage_provider()
        updated_ids: list[int] = []
        skipped = 0

        for item in items:
            data = fetch_stored_image_bytes(item.image_url or "")
            if data is None:
                skipped += 1
                continue
            cutout = remove_background(data)
            if cutout is None:
                skipped += 1
                continue
            item.thumbnail_url = storage.save(cutout, ext="png", subdir="cutouts")
            EmbeddingService.mark_stale(item)
            EmbeddingService.embed_item(db, item, commit=False)
            db.add(item)
            updated_ids.append(item.id)

        if updated_ids:
            db.commit()

        return CutoutBackfillResult(
            updated=len(updated_ids),
            skipped=skipped,
            updated_ids=updated_ids,
        )

    # ----- wear / laundry loop ----------------------------------------------

    @staticmethod
    def mark_worn(db: Session, user_id: int, item_id: int):
        """Record a wear. Increments lifetime + since-wash counters, stamps the
        time, and auto-marks the item dirty once it reaches its wear limit. Items
        with no wear limit (jewelry, bags) are worn but never become dirty."""
        item = ClosetService.get_item(db, user_id, item_id)
        item.times_worn = (item.times_worn or 0) + 1
        item.wears_since_wash = (item.wears_since_wash or 0) + 1
        item.last_worn_at = _now()
        limit = item.effective_wear_limit
        if limit is not None and item.wears_since_wash >= limit:
            item.is_clean = False
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def mark_washed(db: Session, user_id: int, item_id: int):
        """Laundered: clean again and the since-wash counter resets."""
        item = ClosetService.get_item(db, user_id, item_id)
        item.is_clean = True
        item.wears_since_wash = 0
        item.last_washed_at = _now()
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def mark_dirty(db: Session, user_id: int, item_id: int):
        """Soiled out of cycle (a spill, etc.) regardless of wear count."""
        item = ClosetService.get_item(db, user_id, item_id)
        item.is_clean = False
        # Reflect that it needs washing even if under the wear limit.
        limit = item.effective_wear_limit
        if limit is not None and (item.wears_since_wash or 0) < limit:
            item.wears_since_wash = limit
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def do_laundry(db: Session, user_id: int, item_ids: Optional[List[int]] = None):
        """A laundry batch finished. Marks the given dirty items clean (or all dirty
        items when no ids are given) and resets their since-wash counters."""
        query = db.query(ClothingItem).filter(
            ClothingItem.user_id == user_id, ClothingItem.is_clean.is_(False)
        )
        if item_ids:
            query = query.filter(ClothingItem.id.in_(item_ids))
        washed = query.all()
        now = _now()
        for item in washed:
            item.is_clean = True
            item.wears_since_wash = 0
            item.last_washed_at = now
            db.add(item)
        db.commit()
        return len(washed)

    @staticmethod
    def laundry_summary(db: Session, user_id: int) -> dict:
        """Snapshot of the laundry state: clean/dirty counts (only for items that
        are actually laundered), which essentials are depleted, and whether a wash
        is due — with a human-readable message."""
        items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        launderable = [i for i in items if i.effective_wear_limit is not None]
        clean = [i for i in launderable if i.is_clean]
        dirty = [i for i in launderable if not i.is_clean]

        clean_by_category = dict(Counter(i.category for i in clean))
        dirty_by_category = dict(Counter(i.category for i in dirty))
        owned_categories = {i.category for i in launderable}

        depleted = [
            category
            for category in _ESSENTIAL_CATEGORIES
            if category in owned_categories and clean_by_category.get(category, 0) == 0
        ]
        laundry_due = bool(depleted) or len(dirty) >= _LAUNDRY_DUE_THRESHOLD

        if depleted:
            message = f"Out of clean {', '.join(depleted)} — laundry due."
        elif laundry_due:
            message = f"{len(dirty)} items in the hamper — time for laundry."
        elif dirty:
            message = f"{len(clean)} clean, {len(dirty)} in the hamper."
        else:
            message = "Everything's clean and ready."

        return {
            "clean_count": len(clean),
            "dirty_count": len(dirty),
            "laundry_due": laundry_due,
            "depleted_categories": depleted,
            "clean_by_category": clean_by_category,
            "dirty_by_category": dirty_by_category,
            "message": message,
        }
