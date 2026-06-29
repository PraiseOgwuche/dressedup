from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.clothing_item import ClothingItem
from app.schemas.closet import ClothingItemCreate, ClothingItemUpdate

# Laundry is "due" once at least this many launderable items are dirty, or when an
# essential category has run out of clean options (handled separately).
_LAUNDRY_DUE_THRESHOLD = 8
_ESSENTIAL_CATEGORIES = ("top", "bottom", "underwear")


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
        item = ClothingItem(user_id=user_id, **payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_item(db: Session, user_id: int, item_id: int, payload: ClothingItemUpdate):
        item = ClosetService.get_item(db, user_id, item_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_item(db: Session, user_id: int, item_id: int):
        item = ClosetService.get_item(db, user_id, item_id)
        db.delete(item)
        db.commit()

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

