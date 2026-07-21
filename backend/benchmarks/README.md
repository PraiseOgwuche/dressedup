# Outfit Engine benchmark

Deterministic harness for the outfit suggestion engine. The frozen baseline
captures behavior before embedding-backed retrieval; ablation and release
gates sit on the same runner.

## Run

From `backend/` with the project virtual environment active:

```bash
python scripts/run_outfit_benchmark.py
```

Default report (committed):

```text
benchmarks/baselines/outfit_v3.json
```

Runs are deterministic aside from timestamps and machine-dependent latency.
`deterministic_fingerprint` excludes those fields and should stay stable for
the same engine, fixtures, seed, and run count.

### Ablation and release gates

```bash
# Embeddings off (baseline) vs on
python scripts/run_outfit_ablation.py --write-reports

# Automated gate report (hard constraints, latency, recovery, sensitivity)
python scripts/run_phase10_eval.py

# Single benchmark with embeddings on
python scripts/run_outfit_benchmark.py \
  --embeddings on \
  --output benchmarks/candidates/outfit_v4_on.json
```

Rollout stages and human gates: [`ROLLOUT.md`](./ROLLOUT.md).  
Blind pairwise template: [`blind_review_template.json`](./blind_review_template.json).

Compare two reports:

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

- Hard constraints: required slots, clean-only selection, forbidden items,
  inappropriate outerwear, dress/separates exclusion
- Explicit occasion / weather mismatches
- Ranking direction and margin for controlled preferred / alternative outfits
- Unique outfits and consecutive repetition
- Selected score distribution
- p50 / p95 service latency
- Deterministic output for a fixed seed
- Embeddings on/off ablation, visual-weight sensitivity, large-closet p95,
  failure recovery

## What is not measured

Automated scores do not prove an outfit looks good. The committed baseline
does **not** claim to measure taste, beauty, fit, or subjective style quality.
Stable placeholder image URLs are intentional: scoring uses metadata (and
optional stub / FashionCLIP vectors), not live pixels.

Subjective quality uses a separate blind pairwise review
(`blind_review_template.json`):

1. Generate embeddings-off and embeddings-on outfits from the same closet and context.
2. Render anonymized boards using real item photos.
3. Randomize left/right ordering and hide engine labels.
4. Ask which outfit better fits the context, plus confidence.
5. Store wardrobe snapshot, item IDs, context, choice, and timestamp.
6. Use at least 40 comparisons across the benchmark categories.

Rollout target: at least 65% preference for embeddings-on, with no regression
in hard constraints.

## Frozen baseline (v4 structure)

Default run (`10` cases × `20` seeds, embeddings **off**):

- Hard-constraint pass rate: **100%** (includes `dress_combined_with_separates`)
- Ranking probes: **2 / 3**
- Dresses / jumpsuits generate as full-body outfits
- Known debts:
  - Weather fallback is silent when nothing matches
  - Occasion fallback is silent when nothing matches
  - Workout activewear loses its controlled ranking probe by `0.0175`

The original v3 fingerprint was retired when full-body garments were added;
schema bumped to 1.1 and engine version to `outfit-v4-structure`.

These debts are observations, not accepted long-term behavior.
