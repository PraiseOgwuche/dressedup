#!/usr/bin/env python3
"""Run Outfit Engine v4 Phase 10 evaluation gates and write a JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.evaluation.phase10_eval import evaluate_gates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 10 outfit engine release gates.")
    parser.add_argument("--seed", type=int, default=20260720)
    parser.add_argument("--runs-per-case", type=int, default=10)
    parser.add_argument(
        "--skip-large-closet",
        action="store_true",
        help="Skip the 200-item latency probe (faster CI).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "benchmarks" / "candidates" / "phase10_gates.json",
    )
    args = parser.parse_args()

    report = evaluate_gates(
        seed=args.seed,
        runs_per_case=args.runs_per_case,
        skip_large_closet=args.skip_large_closet,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote {args.output}")
    print(f"automated_gates_pass={report['automated_gates_pass']}")
    for name, gate in report["gates"].items():
        status = gate.get("pass")
        label = {True: "PASS", False: "FAIL", None: "PENDING"}.get(status, str(status))
        print(f"  {name}: {label}")
    return 0 if report["automated_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
