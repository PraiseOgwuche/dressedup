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
| **Shop v1** | ✅ | Curated catalog + virtual outfit-count scoring (`app/shop/catalog.yaml`) |

## Outfit Engine v4

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Baseline benchmark | ✅ | Deterministic v3 fixtures, constraints/ranking/diversity/latency metrics, frozen JSON report |
| 1 Vector foundation | ✅ | `0017` migration: pgvector `vector(512)` + status metadata; `EmbeddingProvider` stub; `OUTFIT_EMBEDDINGS_ENABLED` flag (off) |
| 2 Self-hosted FashionCLIP | ✅ | ONNX vision encoder (`EMBEDDING_PROVIDER=fashionclip`); ~455 MB RSS, ~120 ms/img warm; validated on real cutouts |
| 3 Ingestion + backfill | Planned | Embed new and existing garment cutouts |
| 4 Hybrid retrieval | Planned | Context filters + pgvector candidate retrieval |
| 5 Hybrid scoring | Planned | Visual coherence as a calibrated signal, joint outerwear scoring |
| 6 Rich outfit structure | Planned | Dresses, jumpsuits, bags, accessories |
| 7 Distinct directions | Planned | Multiple intentionally different styling profiles |
| 8 Vector personalization | Planned | Taste centroids from wears/likes/dislikes/swaps |
| 9 Language styling | Planned | Structured prompt interpretation, real closet IDs only |
| 10 Evaluation + rollout | Planned | v3/v4 ablation, blind review, feature-flag rollout |

## Parked

3D closet view, on-device segmentation, trained recommender.
