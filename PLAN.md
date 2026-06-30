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
| **Outfit engine v3** | ✅ | Fashion knowledge base + preference learning |
| **Fashion rulebook (YAML)** | ✅ | `app/fashion/knowledge.yaml` — colors, textures, occasions, trends |
| **Trend tags + occasion palettes** | ✅ | quiet-luxury, streetwear, etc.; per-occasion color palettes |
| Wear & laundry | ✅ | Category limits, hamper, wash-all |
| I Daily plan + push | ✅ | Routines, scheduler; push needs dev build |
| **F Receipt + label + email import** | ✅ | Photo receipt/label + Mailgun forward address |
| **J Voice / text agent** | ✅ | `POST /outfits/ask` — natural language → outfit |
| **Trip packing** | ✅ | Per-day outfits + deduplicated suitcase list + **live weather** |
| Deploy + durable media | ✅ S3 provider | Set `STORAGE_PROVIDER=s3` on Render; local disk for dev |

## Parked

3D closet view, on-device segmentation, trained recommender.
