#!/usr/bin/env python3
"""Run the deterministic Outfit Engine benchmark and write a JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.evaluation.outfit_benchmark import (  # noqa: E402
    DEFAULT_RUNS_PER_CASE,
    DEFAULT_SEED,
    run_outfit_benchmark,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark the current DressedUp outfit engine.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--runs-per-case",
        type=int,
        default=DEFAULT_RUNS_PER_CASE,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "benchmarks" / "baselines" / "outfit_v3.json",
    )
    parser.add_argument(
        "--embeddings",
        choices=("off", "on"),
        default="off",
        help="Phase 10 ablation: run with OUTFIT_EMBEDDINGS_ENABLED off (baseline) or on.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    embeddings_enabled = args.embeddings == "on"
    report = run_outfit_benchmark(
        seed=args.seed,
        runs_per_case=args.runs_per_case,
        embeddings_enabled=embeddings_enabled,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = report["summary"]
    print(f"Wrote {args.output}")
    print(
        "embeddings={embeddings} cases={case_count} runs={total_runs} "
        "hard-pass={hard_constraint_pass_rate:.1%} "
        "ranking={ranking_probe_pass_count}/{ranking_probe_count} "
        "fingerprint={fingerprint}".format(
            embeddings=args.embeddings,
            **summary,
            fingerprint=report["deterministic_fingerprint"][:12],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
