# Outfit Engine v4 — embedding rollout

## Feature flag

| Flag | Default | Role |
|------|---------|------|
| `OUTFIT_EMBEDDINGS_ENABLED` | `false` | Master kill-switch. When off, suggestions use the structure engine only (no hybrid retrieval, visual coherence, or taste centroids). |

Suggestions never call FashionCLIP at request time — only precomputed vectors are read.

## Automated gates (required before widening rollout)

From `backend/`:

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

1. **Internal** — enable for test accounts; run release gates; spot-check Home / Ask / Directions.
2. **Blind review** — ≥40 anonymized pairs across benchmark categories.
3. **Coverage** — backfill production closets to ≥95% ready.
4. **General availability** — set `OUTFIT_EMBEDDINGS_ENABLED=true` in production.
5. **Kill-switch** — if hard violations or latency regress, flip the flag off (no model redeploy required).

## Scope note

Automated scores do not prove outfits look better. Preference comes only from the blind human protocol.
