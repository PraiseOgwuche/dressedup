#!/usr/bin/env python3
"""Compare two outfit benchmark reports without requiring app dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUMMARY_METRICS = (
    "hard_constraint_pass_rate",
    "hard_constraint_violation_count",
    "selection_expectation_miss_count",
    "context_mismatch_run_count",
    "ranking_probe_pass_count",
    "worst_case_latency_p95_ms",
)

CASE_METRICS = (
    "hard_violation_count",
    "expectation_miss_count",
    "context_mismatch_run_count",
    "unique_outfit_rate",
    "consecutive_repeat_rate",
    "score_mean",
    "latency_p95_ms",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _delta(before: float | int, after: float | int) -> float:
    return round(float(after) - float(before), 6)


def compare_reports(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    if baseline["schema_version"] != candidate["schema_version"]:
        raise ValueError("Benchmark schema versions do not match")

    baseline_cases = {case["case_id"]: case for case in baseline["cases"]}
    candidate_cases = {case["case_id"]: case for case in candidate["cases"]}
    shared_case_ids = sorted(baseline_cases.keys() & candidate_cases.keys())

    return {
        "baseline_engine": baseline["engine_version"],
        "candidate_engine": candidate["engine_version"],
        "baseline_fingerprint": baseline["deterministic_fingerprint"],
        "candidate_fingerprint": candidate["deterministic_fingerprint"],
        "summary_deltas": {
            metric: _delta(
                baseline["summary"][metric],
                candidate["summary"][metric],
            )
            for metric in SUMMARY_METRICS
        },
        "case_deltas": {
            case_id: {
                metric: _delta(
                    baseline_cases[case_id]["metrics"][metric],
                    candidate_cases[case_id]["metrics"][metric],
                )
                for metric in CASE_METRICS
            }
            for case_id in shared_case_ids
        },
        "baseline_only_cases": sorted(baseline_cases.keys() - candidate_cases.keys()),
        "candidate_only_cases": sorted(candidate_cases.keys() - baseline_cases.keys()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two outfit benchmark JSON reports.")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    comparison = compare_reports(_load(args.baseline), _load(args.candidate))
    rendered = json.dumps(comparison, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
