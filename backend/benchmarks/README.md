# Outfit Engine benchmark

Phase 0 freezes an objective Outfit Engine v3 baseline before vector retrieval
or FashionCLIP changes its behavior.

## Run

From `backend/` with the project virtual environment active:

```bash
python scripts/run_outfit_benchmark.py
```

The default report is committed at:

```text
benchmarks/baselines/outfit_v3.json
```

The run is deterministic apart from timestamps and machine-dependent latency.
`deterministic_fingerprint` excludes those values and should remain stable for
the same engine, fixtures, seed, and run count.

To compare v3 with a future candidate:

```bash
python scripts/compare_outfit_benchmarks.py \
  benchmarks/baselines/outfit_v3.json \
  benchmarks/candidates/outfit_v4.json
```

Useful options:

```bash
python scripts/run_outfit_benchmark.py \
  --seed 20260720 \
  --runs-per-case 50 \
  --output benchmarks/candidates/outfit_v4.json
```

## What is measured

- hard constraints: required slots, clean-only selection, forbidden items,
  inappropriate outerwear
- explicit occasion/weather mismatches
- ranking direction and margin for controlled preferred/alternative outfits
- unique outfits and consecutive repetition
- selected score distribution
- p50/p95 service latency
- deterministic output for a fixed seed

The fixtures cover a tiny closet, work formality, cold/warm layering,
cleanliness, workout activewear, color/pattern clashes, context fallback, and
full-body garments.

## What is not measured

An automatic score cannot prove that an outfit looks good. The committed
baseline therefore does **not** claim to measure taste, beauty, fit on a body,
or subjective style quality. Stable placeholder image URLs are intentional:
v3 does not inspect image pixels during recommendation.

When v4 is ready, subjective quality is measured separately through a blind
pairwise review:

1. Generate v3 and v4 outfits from the same closet and context.
2. Render anonymized boards using real item photos.
3. Randomize left/right ordering and hide engine labels.
4. Ask: “Which outfit better fits this context?” plus confidence.
5. Store the wardrobe snapshot, item IDs, context, choice, and timestamp.
6. Use at least 40 comparisons across the benchmark categories.

The rollout target is at least 65% preference for v4 over v3, without any
regression in hard constraints.

## Frozen v3 baseline

Default run (`9` cases × `20` seeds):

- hard-constraint pass rate: **100%**
- ranking probes: **2 / 3**
- explicit context-mismatch runs: **20 / 180**
- known debts:
  - dress/full-body garments are not generated
  - weather fallback is silent when nothing matches
  - occasion fallback is silent when nothing matches
  - workout activewear loses its controlled ranking probe by `0.0175`

These debts are observations, not accepted v4 behavior.
