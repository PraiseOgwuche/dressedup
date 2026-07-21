import pytest

from app.evaluation.outfit_benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    ENGINE_VERSION,
    run_outfit_benchmark,
)
from app.evaluation.outfit_benchmark_fixtures import FIXTURES


@pytest.fixture(scope="module")
def report():
    return run_outfit_benchmark(seed=12345, runs_per_case=5)


def _case(report, case_id):
    return next(case for case in report["cases"] if case["case_id"] == case_id)


def test_fixture_ids_are_unique():
    ids = [case.case_id for case in FIXTURES]
    assert len(ids) == len(set(ids))


def test_benchmark_report_contract(report):
    assert report["schema_version"] == BENCHMARK_SCHEMA_VERSION
    assert report["engine_version"] == ENGINE_VERSION
    assert report["summary"]["case_count"] == len(FIXTURES)
    assert report["summary"]["total_runs"] == len(FIXTURES) * 5
    assert len(report["deterministic_fingerprint"]) == 64


def test_benchmark_is_deterministic_excluding_latency_and_timestamp(report):
    rerun = run_outfit_benchmark(seed=12345, runs_per_case=5)
    assert rerun["deterministic_fingerprint"] == report["deterministic_fingerprint"]


def test_phase_zero_hard_constraints_are_observed(report):
    assert report["summary"]["hard_constraint_violation_count"] == 0
    assert _case(report, "dirty-best-item-excluded")["hard_violation_counts"] == {}
    assert _case(report, "warm-skips-layer")["hard_violation_counts"] == {}


def test_known_v3_context_and_slot_debts_are_visible(report):
    fallback = _case(report, "soft-context-fallback")
    assert fallback["metrics"]["context_mismatch_run_count"] == 5
    assert "soft_weather_fallback" in fallback["known_debts"]

    dress = _case(report, "dress-only-unsupported")
    assert "full_body_garment_not_generated" in dress["known_debts"]
    assert set(dress["run_signatures"]) == {
        "top:-|bottom:-|shoes:-|outerwear:-"
    }


def test_ranking_probes_report_direction_and_margin(report):
    probes = [
        probe
        for case in report["cases"]
        for probe in case["ranking_probes"]
    ]
    assert probes
    assert all(isinstance(probe["passed"], bool) for probe in probes)
    assert all("margin" in probe for probe in probes)

    business = next(probe for probe in probes if probe["label"] == "business coherence")
    assert business["passed"] is True
