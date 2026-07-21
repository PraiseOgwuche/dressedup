"""Phase 10 — automated release gates for Outfit Engine v4."""

from __future__ import annotations

from app.evaluation.phase10_eval import (
    evaluate_gates,
    run_embeddings_ablation,
    run_failure_recovery,
    run_weight_sensitivity,
)
from app.evaluation.outfit_benchmark import run_outfit_benchmark


def test_baseline_fingerprint_stable_when_embeddings_off():
    report = run_outfit_benchmark(seed=20260720, runs_per_case=5, embeddings_enabled=False)
    assert report["summary"]["hard_constraint_violation_count"] == 0
    assert report["embeddings_enabled"] is False
    # Same seed/runs → same fingerprint across calls.
    again = run_outfit_benchmark(seed=20260720, runs_per_case=5, embeddings_enabled=False)
    assert report["deterministic_fingerprint"] == again["deterministic_fingerprint"]


def test_embeddings_on_keeps_hard_constraints():
    report = run_outfit_benchmark(seed=20260720, runs_per_case=5, embeddings_enabled=True)
    assert report["summary"]["hard_constraint_violation_count"] == 0
    assert report["embeddings_enabled"] is True
    assert report["engine_version"] == "outfit-v4-embeddings"


def test_ablation_no_hard_regression():
    ablation = run_embeddings_ablation(seed=20260720, runs_per_case=5)
    assert ablation["no_hard_regression"] is True
    assert ablation["off"]["hard_constraint_violation_count"] == 0
    assert ablation["on"]["hard_constraint_violation_count"] == 0


def test_weight_sensitivity_stable():
    result = run_weight_sensitivity(seed=20260720, runs_per_case=3)
    assert result["stable"] is True


def test_failure_recovery():
    result = run_failure_recovery()
    assert result["pass"] is True
    assert result["checks"]["failed_embedding_still_suggests"]
    assert result["checks"]["empty_closet_no_crash"]
    assert result["checks"]["empty_closet_ask_parses"]


def test_evaluate_gates_automated_pass():
    report = evaluate_gates(seed=20260720, runs_per_case=5, skip_large_closet=True)
    assert report["automated_gates_pass"] is True
    assert report["gates"]["hard_constraint_violations"]["pass"] is True
    assert report["gates"]["failure_recovery"]["pass"] is True
    assert report["gates"]["blind_human_preference"]["status"] == "pending_human"
    assert "OUTFIT_EMBEDDINGS_ENABLED" in report["feature_flag"]["name"]
