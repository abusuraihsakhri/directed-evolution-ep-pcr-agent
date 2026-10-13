"""Regression coverage for numerical boundaries, HMAC integrity, and ASGI startup."""
import math

import pytest
from fastapi.testclient import TestClient

from agents.base import AuditTrail
from directed_evolution.engine import (
    PCRConditions, calculate_mutation_rate, classify_mutations,
    coverage_at_library_size, library_diversity, library_size_for_coverage,
    mutation_distribution, nk_fitness, poisson_probability,
    simulate_directed_evolution, simulate_mutations, roulette_selection,
)
from directed_evolution.server import create_app


def test_audit_checks_hmac_not_only_previous_hash():
    audit = AuditTrail(secret_key="regression-test-key")
    audit.log("engine", "test", "calculation", {"count": 1})
    assert audit.verify_integrity()
    snapshot = audit.get_trail()
    snapshot[0]["actor"] = "changed"
    assert audit.verify_integrity(), "Snapshot must not mutate the live trail"
    audit.logs[0]["actor"] = "changed"
    assert not audit.verify_integrity(), "Tampering with a signed field must fail"


def test_audit_checks_last_signature():
    audit = AuditTrail(secret_key="regression-test-key")
    audit.log("engine", "test", "calculation", {"count": 1})
    audit.logs[-1]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_poisson_lambda(value):
    with pytest.raises(ValueError):
        poisson_probability(0, value)
    with pytest.raises(ValueError):
        mutation_distribution(value)


@pytest.mark.parametrize("value", [float("nan"), -0.1])
def test_invalid_manganese(value):
    with pytest.raises(ValueError):
        calculate_mutation_rate(PCRConditions(value, 1.0, 30, 500))


def test_one_variant_library():
    assert library_diversity(0, 4) == 1
    assert library_size_for_coverage(1, 0.95) == 1
    assert coverage_at_library_size(1, 0) == 0
    assert coverage_at_library_size(1, 1) == 1


def test_coverage_is_stable_for_large_libraries():
    assert 0 < coverage_at_library_size(1000000, 1) < 1e-5
    assert coverage_at_library_size(1000000, 10000000) > 0.999


def test_mutation_simulator_rejects_unsafe_inputs():
    for seq, lam in [("", 1), ("NNN", 1), ("ATG", -1), ("ATG", math.inf)]:
        with pytest.raises(ValueError):
            simulate_mutations(seq, lam)


def test_high_mutation_count_is_bounded_and_returns_promptly():
    seq = "ATG" * 100
    mutated, events = simulate_mutations(seq, 1000000, seed=13)
    assert len(mutated) == len(seq)
    assert len(events) == len(seq)
    assert len({event.position for event in events}) == len(seq)
    assert mutated != seq


def test_seed_does_not_change_global_rng_state():
    import random
    random.seed(99)
    before = random.getstate()
    simulate_mutations("ATGGCT" * 10, 5, seed=12)
    assert random.getstate() == before


def test_multiple_substitutions_use_final_codon():
    events = classify_mutations("GCT", "TAA")
    assert len(events) == 3
    assert all(event.mutated_codon == "TAA" and event.is_nonsense for event in events)


def test_nk_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        nk_fitness([], 0, 0)
    with pytest.raises(ValueError):
        nk_fitness([0, 1], 2, -1)
    with pytest.raises(ValueError):
        simulate_directed_evolution([0, 1], population_size=0, k=1)
    with pytest.raises(ValueError):
        roulette_selection([([0], -1)])


def test_running_asgi_app_and_audit_endpoint():
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/api/audit", json={
            "task_id": "TEST-1",
            "target_identifier": "SEQ-1",
            "primary_metric": 10.0,
            "secondary_metric": 1.0,
        })
        assert response.status_code == 200
        assert response.json()["overall_urgency"] == "ROUTINE"
        assert client.post("/api/audit", json={"invalid": True}).status_code == 422
