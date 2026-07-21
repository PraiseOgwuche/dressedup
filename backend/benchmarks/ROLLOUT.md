# Outfit Engine v4 — Phase 10 rollout

## Feature flag

| Flag | Default | Role |
|------|---------|------|
| `OUTFIT_EMBEDDINGS_ENABLED` | `false` | Master kill-switch. When off, suggestion path is the Phase 6 structure engine (hybrid retrieval / visual coherence / taste off). |

Suggestions **never** call FashionCLIP live — only precomputed vectors are read.

## Automated gates (must pass before widening rollout)

Run from `backend/`:

```bash
python scripts/run_phase10_eval.py
python scripts/run_outfit_ablation.py --write-reports
```

| Gate | Target |
|------|--------|
| Hard-constraint violations | **0** (embeddings on and off) |
| Suggestion p95 (200-item closet) | **&lt; 500 ms** |
| Weight sensitivity (`_W_VISUAL` 0.05–0.15) | Hard constraints stay at 0 |
| Failure recovery | Failed embeddings + empty closet never crash |
| Ablation | Embeddings-on does not increase hard violations |

## Human / ops gates (required before 100% rollout)

| Gate | Target | How |
|------|--------|-----|
| Embedding coverage | **≥ 95%** ready | `ready / (ready+failed+pending)` after `backfill_embeddings.py` |
| Blind preference | **≥ 65%** for embeddings-on | Fill `blind_review_template.json` (≥40 pairs) |

## Rollout stages

1. **Internal** — flag on for test accounts; run Phase 10 eval + spot-check Home / Ask / Directions.
2. **Blind review** — ≥40 anonymized pairs across benchmark categories.
3. **Coverage** — backfill production closets to ≥95% ready.
4. **General availability** — set `OUTFIT_EMBEDDINGS_ENABLED=true` in production.
5. **Kill-switch** — if hard violations or latency regress, flip the flag off (no redeploy of models required).

## What Phase 10 does *not* claim

Automated scores do not prove outfits look better. Preference comes only from the blind human protocol.
