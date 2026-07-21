"""Reproducible Phase 0 benchmark for Outfit Engine v3.

This harness exercises the real OutfitService against an isolated SQLite
database. It measures objective behavior only: constraints, context coverage,
ranking direction, diversity, determinism, score distributions, and latency.
Subjective fashion quality requires the separate blind-review protocol.
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register all model tables and relationships
from app.config import settings
from app.database import Base
from app.evaluation.outfit_benchmark_fixtures import (
    FIXTURES,
    BenchmarkCase,
    ItemSpec,
    fixture_manifest,
)
from app.fashion import FashionMatcher
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_service import OutfitService
from app.services.preference_service import PreferenceService
from app.services.stylist_service import StylistService

BENCHMARK_SCHEMA_VERSION = "1.1"
ENGINE_VERSION = "outfit-v4-structure"
DEFAULT_SEED = 20260720
DEFAULT_RUNS_PER_CASE = 20
SLOTS = ("top", "bottom", "shoes", "outerwear", "dress", "bag", "accessory", "headwear")


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile))))
    return ordered[index]


def _round(value: float) -> float:
    return round(float(value), 6)


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


@contextmanager
def _isolated_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _create_user(db: Session, case_id: str) -> User:
    user = User(
        email=f"benchmark-{case_id}@example.invalid",
        full_name=f"Benchmark {case_id}",
        hashed_password="not-a-real-password",
    )
    db.add(user)
    db.flush()
    return user


def _create_item(db: Session, user_id: int, spec: ItemSpec) -> ClothingItem:
    item = ClothingItem(
        user_id=user_id,
        name=spec.name,
        category=spec.category,
        subcategory=spec.subcategory,
        color=spec.color,
        color_hex=spec.color_hex,
        pattern=spec.pattern,
        material=spec.material,
        formality=spec.formality,
        occasion=spec.occasion,
        weather_tag=spec.weather_tag,
        seasons=spec.seasons,
        is_clean=spec.is_clean,
        times_worn=spec.times_worn,
        image_url=f"benchmark://garments/{_slug(spec.name)}.jpg",
        source="benchmark",
    )
    db.add(item)
    db.flush()
    return item


def _selected(payload: dict[str, Any]) -> list[ClothingItem]:
    return [payload[slot] for slot in SLOTS if payload.get(slot) is not None]


def _signature(payload: dict[str, Any]) -> str:
    return "|".join(
        f"{slot}:{payload[slot].name if payload.get(slot) is not None else '-'}"
        for slot in SLOTS
    )


def _context_mismatches(
    selected: list[ClothingItem],
    weather_tag: str | None,
    occasion: str | None,
) -> list[str]:
    mismatches: list[str] = []
    for item in selected:
        if weather_tag and item.weather_tag and weather_tag not in item.weather_tag:
            mismatches.append(f"{item.name}:weather")
        if occasion and item.occasion and occasion not in item.occasion:
            mismatches.append(f"{item.name}:occasion")
    return mismatches


def _hard_violations(case: BenchmarkCase, payload: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    selected = _selected(payload)
    selected_names = {item.name for item in selected}

    for slot in case.required_slots:
        if payload.get(slot) is None:
            violations.append(f"missing_required_slot:{slot}")
    for item in selected:
        if not item.is_clean:
            violations.append(f"dirty_item_selected:{item.name}")
    for name in case.forbidden_names:
        if name in selected_names:
            violations.append(f"forbidden_item_selected:{name}")
    if case.outerwear == "forbidden" and payload.get("outerwear") is not None:
        violations.append("outerwear_selected_when_forbidden")
    if payload.get("dress") is not None and (
        payload.get("top") is not None or payload.get("bottom") is not None
    ):
        violations.append("dress_combined_with_separates")
    return violations


def _expectation_misses(case: BenchmarkCase, payload: dict[str, Any]) -> list[str]:
    misses: list[str] = []
    selected_names = {item.name for item in _selected(payload)}
    for name in case.required_names:
        if name not in selected_names:
            misses.append(f"expected_item_not_selected:{name}")
    if case.outerwear == "required" and payload.get("outerwear") is None:
        misses.append("expected_outerwear_missing")
    return misses


def _score_selected(
    db: Session,
    user_id: int,
    case: BenchmarkCase,
    selected: list[ClothingItem],
) -> dict[str, float]:
    context = OutfitService._context(case.weather_tag, case.occasion, case.trend)
    personalization, notes = PreferenceService.personalization_bonus(db, user_id, selected)
    breakdown = FashionMatcher.score_outfit(
        selected,
        context,
        personalization=personalization,
        personal_notes=notes,
    )
    return {
        "total": _round(breakdown.total),
        "color": _round(breakdown.color),
        "formality": _round(breakdown.formality),
        "pattern": _round(breakdown.pattern),
        "footwear": _round(breakdown.footwear),
        "occasion": _round(breakdown.occasion),
        "season": _round(breakdown.season),
        "personalization": _round(breakdown.personalization),
    }


def _ranking_results(
    db: Session,
    user_id: int,
    case: BenchmarkCase,
    items_by_name: dict[str, ClothingItem],
) -> list[dict[str, Any]]:
    context = OutfitService._context(case.weather_tag, case.occasion, case.trend)
    results: list[dict[str, Any]] = []
    for probe in case.ranking_probes:
        preferred = [items_by_name[name] for name in probe.preferred]
        alternative = [items_by_name[name] for name in probe.alternative]
        preferred_score = FashionMatcher.score_outfit(preferred, context).total
        alternative_score = FashionMatcher.score_outfit(alternative, context).total
        results.append(
            {
                "label": probe.label,
                "preferred": list(probe.preferred),
                "alternative": list(probe.alternative),
                "preferred_score": _round(preferred_score),
                "alternative_score": _round(alternative_score),
                "margin": _round(preferred_score - alternative_score),
                "passed": preferred_score > alternative_score,
            }
        )
    return results


def _case_report(
    db: Session,
    case: BenchmarkCase,
    case_index: int,
    seed: int,
    runs_per_case: int,
) -> dict[str, Any]:
    user = _create_user(db, case.case_id)
    items = [_create_item(db, user.id, spec) for spec in case.items]
    db.commit()
    items_by_name = {item.name: item for item in items}

    runs: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    # Pin the v3 engine: the baseline must not depend on the developer's .env
    # enabling v4 hybrid retrieval (Phase 10 ablation flips this deliberately).
    with (
        patch.object(StylistService, "enhance_outfit", return_value=None),
        patch.object(settings, "OUTFIT_EMBEDDINGS_ENABLED", False),
    ):
        for run_index in range(runs_per_case):
            run_seed = seed + case_index * 10_000 + run_index
            random.seed(run_seed)
            started = time.perf_counter()
            payload = OutfitService.get_suggestion(
                db=db,
                user_id=user.id,
                weather_tag=case.weather_tag,
                occasion=case.occasion,
                include_alternative=False,
                trend=case.trend,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            latencies_ms.append(latency_ms)
            selected = _selected(payload)
            runs.append(
                {
                    "run": run_index,
                    "seed": run_seed,
                    "signature": _signature(payload),
                    "selected": {
                        slot: payload[slot].name if payload.get(slot) is not None else None
                        for slot in SLOTS
                    },
                    "hard_violations": _hard_violations(case, payload),
                    "expectation_misses": _expectation_misses(case, payload),
                    "context_mismatches": _context_mismatches(
                        selected,
                        case.weather_tag,
                        case.occasion,
                    ),
                    "score": _score_selected(db, user.id, case, selected),
                }
            )

    signatures = [run["signature"] for run in runs]
    unique_signatures = set(signatures)
    consecutive_repeats = sum(
        current == previous
        for previous, current in zip(signatures, signatures[1:])
    )
    hard_count = sum(len(run["hard_violations"]) for run in runs)
    expectation_count = sum(len(run["expectation_misses"]) for run in runs)
    mismatch_runs = sum(bool(run["context_mismatches"]) for run in runs)
    scores = [run["score"]["total"] for run in runs]
    ranking = _ranking_results(db, user.id, case, items_by_name)
    hard_violation_counts = Counter(
        violation
        for run in runs
        for violation in run["hard_violations"]
    )
    expectation_miss_counts = Counter(
        miss
        for run in runs
        for miss in run["expectation_misses"]
    )
    selected_item_counts = Counter(
        name
        for run in runs
        for name in run["selected"].values()
        if name is not None
    )

    return {
        "case_id": case.case_id,
        "description": case.description,
        "tags": list(case.tags),
        "known_debts": list(case.known_debts),
        "context": {
            "weather_tag": case.weather_tag,
            "occasion": case.occasion,
            "trend": case.trend,
        },
        "item_count": len(items),
        "run_signatures": signatures,
        "outfit_counts": dict(sorted(Counter(signatures).items())),
        "selected_item_counts": dict(sorted(selected_item_counts.items())),
        "hard_violation_counts": dict(sorted(hard_violation_counts.items())),
        "expectation_miss_counts": dict(sorted(expectation_miss_counts.items())),
        "sample_runs": runs[:3],
        "metrics": {
            "run_count": runs_per_case,
            "hard_violation_count": hard_count,
            "expectation_miss_count": expectation_count,
            "context_mismatch_run_count": mismatch_runs,
            "unique_outfit_count": len(unique_signatures),
            "unique_outfit_rate": _round(len(unique_signatures) / runs_per_case),
            "consecutive_repeat_rate": _round(
                consecutive_repeats / max(1, runs_per_case - 1)
            ),
            "score_mean": _round(statistics.fmean(scores)),
            "score_min": _round(min(scores)),
            "score_max": _round(max(scores)),
            "latency_p50_ms": _round(_percentile(latencies_ms, 0.50)),
            "latency_p95_ms": _round(_percentile(latencies_ms, 0.95)),
        },
        "ranking_probes": ranking,
    }


def _stable_fingerprint(report: dict[str, Any]) -> str:
    stable = {
        "schema_version": report["schema_version"],
        "engine_version": report["engine_version"],
        "seed": report["seed"],
        "runs_per_case": report["runs_per_case"],
        "cases": [
            {
                "case_id": case["case_id"],
                "run_signatures": case["run_signatures"],
                "hard_violation_counts": case["hard_violation_counts"],
                "expectation_miss_counts": case["expectation_miss_counts"],
                "context_mismatch_run_count": case["metrics"][
                    "context_mismatch_run_count"
                ],
                "score_mean": case["metrics"]["score_mean"],
                "ranking_probes": case["ranking_probes"],
            }
            for case in report["cases"]
        ],
    }
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def run_outfit_benchmark(
    *,
    seed: int = DEFAULT_SEED,
    runs_per_case: int = DEFAULT_RUNS_PER_CASE,
) -> dict[str, Any]:
    if runs_per_case < 1:
        raise ValueError("runs_per_case must be at least 1")

    with _isolated_session() as db:
        cases = [
            _case_report(db, case, index, seed, runs_per_case)
            for index, case in enumerate(FIXTURES)
        ]

    total_runs = sum(case["metrics"]["run_count"] for case in cases)
    hard_violations = sum(case["metrics"]["hard_violation_count"] for case in cases)
    expectation_misses = sum(case["metrics"]["expectation_miss_count"] for case in cases)
    context_mismatch_runs = sum(
        case["metrics"]["context_mismatch_run_count"] for case in cases
    )
    ranking_probes = [
        probe for case in cases for probe in case["ranking_probes"]
    ]
    p95_values = [case["metrics"]["latency_p95_ms"] for case in cases]

    report: dict[str, Any] = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "engine_version": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "runs_per_case": runs_per_case,
        "fixture_manifest": fixture_manifest(),
        "summary": {
            "case_count": len(cases),
            "total_runs": total_runs,
            "hard_constraint_violation_count": hard_violations,
            "hard_constraint_pass_rate": _round(
                1 - hard_violations / max(1, total_runs)
            ),
            "selection_expectation_miss_count": expectation_misses,
            "context_mismatch_run_count": context_mismatch_runs,
            "ranking_probe_count": len(ranking_probes),
            "ranking_probe_pass_count": sum(probe["passed"] for probe in ranking_probes),
            "worst_case_latency_p95_ms": _round(max(p95_values, default=0.0)),
            "known_debts": sorted(
                {
                    debt
                    for case in cases
                    for debt in case["known_debts"]
                }
            ),
        },
        "limitations": [
            "Automated metrics do not measure subjective fashion quality.",
            "Fixture image URLs are stable placeholders because v3 does not inspect pixels at suggestion time.",
            "Latency is machine-dependent and excluded from the deterministic fingerprint.",
            "Known-debt cases document existing v3 behavior; they do not make that behavior acceptable for v4.",
        ],
        "cases": cases,
    }
    report["deterministic_fingerprint"] = _stable_fingerprint(report)
    return report
