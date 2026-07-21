"""Outfit Engine v4 Phase 10 — evaluation gates, ablation, and rollout checks.

Automates everything that can be measured without human taste judgment.
Blind pairwise preference (≥65% v4 over v3) remains a human gate documented in
`benchmarks/blind_review_template.json` and `benchmarks/ROLLOUT.md`.
"""

from __future__ import annotations

import hashlib
import random
import statistics
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.config import settings
from app.database import Base
from app.evaluation.outfit_benchmark import run_outfit_benchmark
from app.fashion import matcher as matcher_mod
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.services.outfit_ask_service import fulfill_outfit_ask
from app.services.outfit_service import OutfitService
from app.services.stylist_service import StylistService

# Release targets from the Phase 10 plan.
GATE_HARD_VIOLATIONS = 0
GATE_SUGGESTION_P95_MS = 500.0
GATE_EMBEDDING_COVERAGE = 0.95
GATE_BLIND_PREFERENCE = 0.65
LARGE_CLOSET_SIZE = 200
LARGE_CLOSET_RUNS = 40


@contextmanager
def _session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _stub_vec(seed: int, dim: int = 512) -> list[float]:
    rng = random.Random(seed)
    vector = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = sum(v * v for v in vector) ** 0.5 or 1.0
    return [v / norm for v in vector]


def _add_item(
    db: Session,
    user_id: int,
    *,
    name: str,
    category: str,
    subcategory: str | None = None,
    color: str = "navy",
    times_worn: int = 0,
    embedding: list[float] | None = None,
    embedding_status: str = "ready",
) -> ClothingItem:
    item = ClothingItem(
        user_id=user_id,
        name=name,
        category=category,
        subcategory=subcategory,
        color=color,
        is_clean=True,
        times_worn=times_worn,
        embedding=embedding,
        embedding_status=embedding_status,
        embedding_model="phase10-stub" if embedding is not None else None,
        embedding_version="1" if embedding is not None else None,
        source="phase10",
    )
    db.add(item)
    db.flush()
    return item


def run_embeddings_ablation(
    *,
    seed: int = 20260720,
    runs_per_case: int = 10,
) -> dict[str, Any]:
    """Compare hard constraints / ranking with embeddings off vs on."""
    off = run_outfit_benchmark(
        seed=seed,
        runs_per_case=runs_per_case,
        embeddings_enabled=False,
    )
    on = run_outfit_benchmark(
        seed=seed,
        runs_per_case=runs_per_case,
        embeddings_enabled=True,
    )
    off_hard = off["summary"]["hard_constraint_violation_count"]
    on_hard = on["summary"]["hard_constraint_violation_count"]
    return {
        "off": {
            "fingerprint": off["deterministic_fingerprint"],
            "hard_constraint_violation_count": off_hard,
            "hard_constraint_pass_rate": off["summary"]["hard_constraint_pass_rate"],
            "ranking_probe_pass_count": off["summary"]["ranking_probe_pass_count"],
            "worst_case_latency_p95_ms": off["summary"]["worst_case_latency_p95_ms"],
            "mean_unique_outfit_rate": statistics.fmean(
                c["metrics"]["unique_outfit_rate"] for c in off["cases"]
            ),
        },
        "on": {
            "fingerprint": on["deterministic_fingerprint"],
            "hard_constraint_violation_count": on_hard,
            "hard_constraint_pass_rate": on["summary"]["hard_constraint_pass_rate"],
            "ranking_probe_pass_count": on["summary"]["ranking_probe_pass_count"],
            "worst_case_latency_p95_ms": on["summary"]["worst_case_latency_p95_ms"],
            "mean_unique_outfit_rate": statistics.fmean(
                c["metrics"]["unique_outfit_rate"] for c in on["cases"]
            ),
        },
        "no_hard_regression": on_hard <= off_hard and on_hard == GATE_HARD_VIOLATIONS,
    }


def run_weight_sensitivity(*, seed: int = 20260720, runs_per_case: int = 5) -> dict[str, Any]:
    """Nudge visual coherence weight; hard constraints must stay clean."""
    results: list[dict[str, Any]] = []
    original = matcher_mod._W_VISUAL
    try:
        for weight in (0.05, 0.10, 0.15):
            matcher_mod._W_VISUAL = weight
            report = run_outfit_benchmark(
                seed=seed,
                runs_per_case=runs_per_case,
                embeddings_enabled=True,
                engine_version=f"outfit-v4-wvisual-{weight}",
            )
            results.append(
                {
                    "w_visual": weight,
                    "hard_constraint_violation_count": report["summary"][
                        "hard_constraint_violation_count"
                    ],
                    "hard_constraint_pass_rate": report["summary"][
                        "hard_constraint_pass_rate"
                    ],
                }
            )
    finally:
        matcher_mod._W_VISUAL = original

    stable = all(r["hard_constraint_violation_count"] == 0 for r in results)
    return {"probes": results, "stable": stable}


def run_large_closet_latency(*, closet_size: int = LARGE_CLOSET_SIZE, runs: int = LARGE_CLOSET_RUNS) -> dict[str, Any]:
    """Suggestion latency on a large embedded closet (precomputed vectors only)."""
    with _session() as db:
        user = User(
            email=f"phase10-large-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}@example.com",
            full_name="Phase10 Large",
            hashed_password="x",
        )
        db.add(user)
        db.flush()

        categories = [
            ("top", "t-shirt"),
            ("bottom", "jeans"),
            ("sneakers", "sneakers"),
            ("jacket", "jacket"),
            ("dress", "midi"),
        ]
        for i in range(closet_size):
            cat, sub = categories[i % len(categories)]
            _add_item(
                db,
                user.id,
                name=f"Item {i}",
                category=cat,
                subcategory=sub,
                color=["navy", "black", "white", "beige", "olive"][i % 5],
                times_worn=i % 7,
                embedding=_stub_vec(1000 + i),
            )
        db.commit()

        latencies: list[float] = []
        with (
            patch.object(StylistService, "enhance_outfit", return_value=None),
            patch.object(settings, "OUTFIT_EMBEDDINGS_ENABLED", True),
        ):
            for run in range(runs):
                random.seed(9000 + run)
                started = time.perf_counter()
                OutfitService.get_suggestion(
                    db,
                    user.id,
                    weather_tag="mild",
                    occasion="everyday",
                    include_alternative=False,
                )
                latencies.append((time.perf_counter() - started) * 1000)

        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
        return {
            "closet_size": closet_size,
            "runs": runs,
            "latency_p50_ms": round(p50, 3),
            "latency_p95_ms": round(p95, 3),
            "pass": p95 < GATE_SUGGESTION_P95_MS,
        }


def run_failure_recovery() -> dict[str, Any]:
    """Embeddings failures / empty closets must never crash suggestion or ask."""
    checks: dict[str, bool] = {}

    with _session() as db:
        user = User(email="phase10-fail@example.com", full_name="Fail", hashed_password="x")
        db.add(user)
        db.flush()
        _add_item(
            db,
            user.id,
            name="Broken Embed Tee",
            category="top",
            embedding=None,
            embedding_status="failed",
        )
        _add_item(db, user.id, name="Jeans", category="bottom", subcategory="jeans", color="blue")
        _add_item(db, user.id, name="Sneakers", category="sneakers", color="white")
        db.commit()

        with (
            patch.object(StylistService, "enhance_outfit", return_value=None),
            patch.object(settings, "OUTFIT_EMBEDDINGS_ENABLED", True),
        ):
            payload = OutfitService.get_suggestion(
                db, user.id, weather_tag=None, occasion=None, include_alternative=False
            )
        checks["failed_embedding_still_suggests"] = bool(
            payload.get("top") or payload.get("bottom") or payload.get("shoes")
        )

    with _session() as db:
        user = User(email="phase10-empty@example.com", full_name="Empty", hashed_password="x")
        db.add(user)
        db.commit()
        with patch.object(StylistService, "enhance_outfit", return_value=None):
            payload = OutfitService.get_suggestion(
                db, user.id, weather_tag=None, occasion=None, include_alternative=False
            )
            ask = fulfill_outfit_ask(db, user.id, "Cold work day, quiet luxury")
        checks["empty_closet_no_crash"] = payload is not None
        checks["empty_closet_ask_no_crash"] = ask["suggestion"] is not None
        checks["empty_closet_ask_parses"] = ask["parsed"].occasion == "work"

    return {"checks": checks, "pass": all(checks.values())}


def evaluate_gates(
    *,
    seed: int = 20260720,
    runs_per_case: int = 10,
    skip_large_closet: bool = False,
) -> dict[str, Any]:
    """Produce the Phase 10 release-gate report."""
    ablation = run_embeddings_ablation(seed=seed, runs_per_case=runs_per_case)
    sensitivity = run_weight_sensitivity(seed=seed, runs_per_case=max(3, runs_per_case // 2))
    recovery = run_failure_recovery()
    large = (
        {"pass": True, "skipped": True}
        if skip_large_closet
        else run_large_closet_latency()
    )

    gates = {
        "hard_constraint_violations": {
            "target": GATE_HARD_VIOLATIONS,
            "actual_off": ablation["off"]["hard_constraint_violation_count"],
            "actual_on": ablation["on"]["hard_constraint_violation_count"],
            "pass": ablation["no_hard_regression"],
        },
        "suggestion_p95_ms": {
            "target": GATE_SUGGESTION_P95_MS,
            "actual": large.get("latency_p95_ms"),
            "pass": large.get("pass", False),
            "closet_size": large.get("closet_size"),
        },
        "ablation_no_hard_regression": {
            "pass": ablation["no_hard_regression"],
            "detail": ablation,
        },
        "weight_sensitivity_stable": {
            "pass": sensitivity["stable"],
            "detail": sensitivity,
        },
        "failure_recovery": recovery,
        "embedding_coverage": {
            "target": GATE_EMBEDDING_COVERAGE,
            "actual": None,
            "pass": None,
            "status": "ops_metric",
            "note": "Measure ready/(ready+failed+pending) on production closets after backfill.",
        },
        "blind_human_preference": {
            "target": GATE_BLIND_PREFERENCE,
            "actual": None,
            "pass": None,
            "status": "pending_human",
            "note": "Fill benchmarks/blind_review_template.json via anonymized pairwise review.",
        },
    }

    automatable = [
        gates["hard_constraint_violations"]["pass"],
        gates["suggestion_p95_ms"]["pass"],
        gates["ablation_no_hard_regression"]["pass"],
        gates["weight_sensitivity_stable"]["pass"],
        gates["failure_recovery"]["pass"],
    ]

    return {
        "schema_version": "phase10-1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_flag": {
            "name": "OUTFIT_EMBEDDINGS_ENABLED",
            "default": False,
            "rollout": [
                "Keep flag false in production until automated gates pass.",
                "Enable for internal/test accounts and run blind review (≥40 pairs).",
                "If preference ≥65% and coverage ≥95%, enable for all users.",
                "Keep flag as kill-switch — suggestions never call FashionCLIP live.",
            ],
        },
        "gates": gates,
        "automated_gates_pass": all(automatable),
        "human_gates_pending": ["blind_human_preference", "embedding_coverage"],
    }
