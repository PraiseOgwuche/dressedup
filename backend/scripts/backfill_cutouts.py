"""Backfill background-removed cutouts for existing closet items.

Finds clothing items whose thumbnail is missing or still points at the
original photo, runs background removal on the stored image, saves the cutout,
and updates thumbnail_url. Items whose image can't be fetched or segmented are
left untouched (and reported).

Run from backend/:  python scripts/backfill_cutouts.py [--dry-run] [--user-id N]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models.clothing_item import ClothingItem  # noqa: E402
from app.services.closet_service import ClosetService  # noqa: E402
from app.services.image_processing import fetch_stored_image_bytes, remove_background  # noqa: E402
from app.services.storage import get_storage_provider  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report without writing anything")
    parser.add_argument("--user-id", type=int, default=None, help="Limit to one user")
    parser.add_argument("--limit", type=int, default=500, help="Max items to process")
    args = parser.parse_args()

    db = SessionLocal()
    storage = get_storage_provider()

    query = (
        db.query(ClothingItem)
        .filter(ClothingItem.image_url.isnot(None))
        .filter(
            (ClothingItem.thumbnail_url.is_(None))
            | (ClothingItem.thumbnail_url == ClothingItem.image_url)
            | (~ClothingItem.thumbnail_url.contains("/cutouts/"))
        )
        .order_by(ClothingItem.created_at.desc())
    )
    if args.user_id is not None:
        query = query.filter(ClothingItem.user_id == args.user_id)
    items = query.limit(args.limit).all()
    print(f"{len(items)} item(s) need a cutout")

    done = skipped = 0
    for item in items:
        data = fetch_stored_image_bytes(item.image_url or "")
        if data is None:
            print(f"  #{item.id} {item.name!r}: image not fetchable, skipped")
            skipped += 1
            continue

        cutout = remove_background(data)
        if cutout is None:
            print(f"  #{item.id} {item.name!r}: segmentation failed, skipped")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  #{item.id} {item.name!r}: would save cutout ({len(cutout) // 1024} KB)")
            done += 1
            continue

        item.thumbnail_url = storage.save(cutout, ext="png", subdir="cutouts")
        db.commit()
        print(f"  #{item.id} {item.name!r}: -> {item.thumbnail_url}")
        done += 1

    if args.user_id is not None and not args.dry_run and done == 0:
        # Smoke the service path once for the same user.
        result = ClosetService.backfill_cutouts(db, args.user_id, limit=1)
        print(f"service path: updated={result.updated} skipped={result.skipped}")

    print(f"done: {done} updated, {skipped} skipped")
    db.close()


if __name__ == "__main__":
    main()
