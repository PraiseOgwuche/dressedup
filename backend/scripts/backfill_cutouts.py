"""Backfill background-removed cutouts for existing closet items.

Finds clothing items whose thumbnail is missing or still points at the
original photo, runs background removal on the stored image, saves the cutout,
and updates thumbnail_url. Items whose image can't be fetched or segmented are
left untouched (and reported).

Run from backend/:  python scripts/backfill_cutouts.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.clothing_item import ClothingItem  # noqa: E402
from app.services.image_processing import remove_background  # noqa: E402
from app.services.storage import get_storage_provider  # noqa: E402


def fetch_image_bytes(url: str) -> bytes | None:
    """Resolve a stored image_url to raw bytes — local media path or HTTP(S)."""
    if url.startswith(settings.MEDIA_URL_PREFIX):
        relative = url[len(settings.MEDIA_URL_PREFIX):].lstrip("/")
        path = Path(settings.MEDIA_DIR) / relative
        return path.read_bytes() if path.exists() else None
    if url.startswith("http://") or url.startswith("https://"):
        try:
            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError:
            return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report without writing anything")
    args = parser.parse_args()

    db = SessionLocal()
    storage = get_storage_provider()

    items = (
        db.query(ClothingItem)
        .filter(ClothingItem.image_url.isnot(None))
        .filter(
            (ClothingItem.thumbnail_url.is_(None))
            | (ClothingItem.thumbnail_url == ClothingItem.image_url)
        )
        .all()
    )
    print(f"{len(items)} item(s) need a cutout")

    done = skipped = 0
    for item in items:
        data = fetch_image_bytes(item.image_url)
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

    print(f"done: {done} updated, {skipped} skipped")
    db.close()


if __name__ == "__main__":
    main()
