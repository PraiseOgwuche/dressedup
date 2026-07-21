# Outfit Engine benchmark

Phase 0 freezes an objective Outfit Engine baseline before vector retrieval
or FashionCLIP changes its behavior. Phase 10 adds ablation, latency, and
rollout gates on top of the same harness.

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

### Phase 10 — ablation + release gates

```bash
# Embeddings off (baseline) vs on
python scripts/run_outfit_ablation.py --write-reports

# Full automated gate report (hard constraints, latency, recovery, sensitivity)
python scripts/run_phase10_eval.py

# Single benchmark with embeddings on
python scripts/run_outfit_benchmark.py \
  --embeddings on \
  --output benchmarks/candidates/outfit_v4_on.json
```

Rollout stages and human gates: [`ROLLOUT.md`](./ROLLOUT.md).  
Blind pairwise template: [`blind_review_template.json`](./blind_review_template.json).

To compare two full reports:

```bash
python scripts/compare_outfit_benchmarks.py \
  benchmarks/baselines/outfit_v3.json \
  benchmarks/candidates/outfit_v4_on.json
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
  inappropriate outerwear, dress/separates exclusion
- explicit occasion/weather mismatches
- ranking direction and margin for controlled preferred/alternative outfits
- unique outfits and consecutive repetition
- selected score distribution
- p50/p95 service latency
- deterministic output for a fixed seed
- Phase 10: embeddings on/off ablation, visual-weight sensitivity, large-closet
  p95, failure recovery

## What is not measured

An automatic score cannot prove that an outfit looks good. The committed
baseline therefore does **not** claim to measure taste, beauty, fit on a body,
or subjective style quality. Stable placeholder image URLs are intentional:
scoring uses metadata (+ optional stub/FashionCLIP vectors), not live pixels.

When v4 is ready, subjective quality is measured separately through a blind
pairwise review (see `blind_review_template.json`):

1. Generate embeddings-off and embeddings-on outfits from the same closet and context.
2. Render anonymized boards using real item photos.
3. Randomize left/right ordering and hide engine labels.
4. Ask: “Which outfit better fits this context?” plus confidence.
5. Store the wardrobe snapshot, item IDs, context, choice, and timestamp.
6. Use at least 40 comparisons across the benchmark categories.

The rollout target is at least 65% preference for embeddings-on, without any
regression in hard constraints.

## Frozen baseline (v4 structure, Phase 6)

Default run (`10` cases × `20` seeds, embeddings **off**):

- hard-constraint pass rate: **100%** (now includes `dress_combined_with_separates`)
- ranking probes: **2 / 3**
- dresses/jumpsuits generate as full-body outfits (`dress-only-supported`,
  `dress-never-mixed-with-separates`)
- remaining known debts:
  - weather fallback is silent when nothing matches
  - occasion fallback is silent when nothing matches
  - workout activewear loses its controlled ranking probe by `0.0175`

The original v3 fingerprint (`b195718ca95d…`) was retired deliberately in
Phase 6 when full-body garments became supported; the schema bumped to 1.1
and engine version to `outfit-v4-structure`.

These debts are observations, not accepted long-term behavior.
