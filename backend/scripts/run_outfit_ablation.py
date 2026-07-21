#!/usr/bin/env python3
"""Embeddings-off vs embeddings-on ablation for Outfit Engine v4."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.evaluation.outfit_benchmark import run_outfit_benchmark  # noqa: E402
from app.evaluation.phase10_eval import run_embeddings_ablation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablate OUTFIT_EMBEDDINGS_ENABLED on vs off.")
    parser.add_argument("--seed", type=int, default=20260720)
    parser.add_argument("--runs-per-case", type=int, default=10)
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="Also write full off/on benchmark JSON reports under benchmarks/candidates/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "benchmarks" / "candidates" / "ablation.json",
    )
    args = parser.parse_args()

    ablation = run_embeddings_ablation(seed=args.seed, runs_per_case=args.runs_per_case)

    if args.write_reports:
        candidates = BACKEND_ROOT / "benchmarks" / "candidates"
        candidates.mkdir(parents=True, exist_ok=True)
        for enabled, name in ((False, "outfit_v4_off.json"), (True, "outfit_v4_on.json")):
            report = run_outfit_benchmark(
                seed=args.seed,
                runs_per_case=args.runs_per_case,
                embeddings_enabled=enabled,
            )
            path = candidates / name
            path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"Wrote {path}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ablation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(
        "hard off={off} on={on} no_regression={ok}".format(
            off=ablation["off"]["hard_constraint_violation_count"],
            on=ablation["on"]["hard_constraint_violation_count"],
            ok=ablation["no_hard_regression"],
        )
    )
    return 0 if ablation["no_hard_regression"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
