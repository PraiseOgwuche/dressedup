# DressedUp — Roadmap

**Goal:** A complete digital closet with minimal user effort, then outfits, laundry, and daily automation.

**Ingestion strategy:** AI reads photos (visual attrs); brand/material come from care labels, receipts, or email import — never guessed from fabric alone. User confirms drafts; low-confidence fields are flagged.

**Principles:** Swappable `VisionProvider` (stub by default), taxonomy-first (`app/taxonomy.py`), cloud AI, Expo mobile.

## Phases

| Phase | Status | Notes |
|-------|--------|-------|
| A–C Foundation + ingest UX | ✅ | Rich items, stub vision, confirm flow |
| D+E AI bridge | ✅ | Claude Haiku, optional, cost-capped |
| G Bulk scan | ✅ | Many photos, review queue |
| H Flat-lay multi-item | ✅ | `POST /closet/ingest/multi` |
| Outfit engine v2 | ✅ | Scoring, variety, rationale |
| Wear & laundry | ✅ | Category limits, hamper, wash-all |
| I Daily plan + push | ✅ | Routines, scheduler; push needs dev build |
| **F Email/receipt import** | — | Zero-effort brand + SKU |
| **J Voice agent** | — | “Dress me for…” → outfit |
| Deploy + durable media | — | Render/Neon done; S3 for images next |

## Parked

3D closet view, on-device segmentation, trained recommender.
