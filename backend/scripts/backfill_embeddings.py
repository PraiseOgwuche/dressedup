"""Backfill FashionCLIP embeddings for existing closet items.

Picks up items that were created before Outfit Engine v4 (status "pending"),
items whose last attempt failed, and — with --refresh-stale — items embedded
by an older model version. Commits after every item, so it is safe to stop
and re-run at any point (resumable by design).

Requires OUTFIT_EMBEDDINGS_ENABLED=true (or --force to override for one run).

Run from backend/:  python scripts/backfill_embeddings.py [--dry-run] [--user-id N]
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.clothing_item import ClothingItem  # noqa: E402
from app.services.embedding import get_embedding_provider  # noqa: E402
from app.services.embedding_service import (  # noqa: E402
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_READY,
    EmbeddingService,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report without writing anything")
    parser.add_argument("--user-id", type=int, default=None, help="Limit to one user")
    parser.add_argument("--limit", type=int, default=1000, help="Max items to process")
    parser.add_argument(
        "--refresh-stale",
        action="store_true",
        help="Also re-embed items whose vector came from an older model version",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even when OUTFIT_EMBEDDINGS_ENABLED is false",
    )
    args = parser.parse_args()

    if not settings.OUTFIT_EMBEDDINGS_ENABLED:
        if not args.force:
            print("OUTFIT_EMBEDDINGS_ENABLED is false — nothing to do (use --force to override).")
            return
        settings.OUTFIT_EMBEDDINGS_ENABLED = True

    provider = get_embedding_provider()
    print(f"provider: {provider.model_name} v{provider.model_version} (dim={provider.dim})")

    db = SessionLocal()
    try:
        query = (
            db.query(ClothingItem)
            .filter(ClothingItem.embedding_status.in_([STATUS_PENDING, STATUS_FAILED]))
            .order_by(ClothingItem.created_at.desc())
        )
        if args.user_id is not None:
            query = query.filter(ClothingItem.user_id == args.user_id)
        items = query.limit(args.limit).all()

        if args.refresh_stale:
            stale_query = (
                db.query(ClothingItem)
                .filter(ClothingItem.embedding_status == STATUS_READY)
                .filter(
                    (ClothingItem.embedding_model != provider.model_name)
                    | (ClothingItem.embedding_version != provider.model_version)
                )
            )
            if args.user_id is not None:
                stale_query = stale_query.filter(ClothingItem.user_id == args.user_id)
            stale = stale_query.limit(max(0, args.limit - len(items))).all()
            items.extend(stale)
            print(f"{len(stale)} stale item(s) queued for re-embedding")

        print(f"{len(items)} item(s) to embed")

        ready = failed = skipped = 0
        started = time.monotonic()
        for i, item in enumerate(items, start=1):
            if args.dry_run:
                url = item.thumbnail_url or item.image_url or "(no image)"
                print(f"  #{item.id} {item.name!r} [{item.embedding_status}]: would embed {url}")
                continue

            if item.embedding_status == STATUS_READY:
                EmbeddingService.mark_stale(item)
            ok = EmbeddingService.embed_item(db, item)  # commits per item — resumable
            if ok:
                ready += 1
                print(f"  [{i}/{len(items)}] #{item.id} {item.name!r}: ready")
            elif item.embedding_status == STATUS_FAILED:
                failed += 1
                print(f"  [{i}/{len(items)}] #{item.id} {item.name!r}: FAILED ({item.embedding_error})")
            else:
                skipped += 1
                print(f"  [{i}/{len(items)}] #{item.id} {item.name!r}: skipped ({item.embedding_error})")

        elapsed = time.monotonic() - started
        if not args.dry_run:
            print(f"done in {elapsed:.1f}s: {ready} ready, {failed} failed, {skipped} skipped")
    finally:
        db.close()


if __name__ == "__main__":
    main()
