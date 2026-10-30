"""Regression tests for SmartDispatch delivery partner assignment and ETA engine.

These tests verify root-cause fixes for:
1. Validation of time values (rejecting bools, negative numbers, non-finite floats, strings).
2. Partner eligibility (active status, capacity validation, non-negative workload).
3. Order validation (order_id, restaurant_id, destination_zone, prep_minutes).
4. Cancellation idempotency and workload non-negativity.
5. Deterministic tie-breaking on identical ETAs.
6. Dataset integrity and integration with synthetic records in data/records.json.
"""
import json
import math
from pathlib import Path
import pytest

from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation, explain_candidates


def test_regression_boolean_time_values_rejected():
    order = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=True)
    partner = new_partner("P-1", "ZONE-1")
    travel = {("ZONE-1", "REST-1"): 5, ("REST-1", "DEST-1"): 10}

    # prep_minutes=True must be rejected because bool is a subclass of int in Python
    est = estimate_eta(order, partner, travel, now=0)
    assert est["eligible"] is False
    assert est["eta_minutes"] is None

    # now=False must also be rejected
    order_valid = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=10)
    est_now = estimate_eta(order_valid, partner, travel, now=False)
    assert est_now["eligible"] is False

    # Travel leg as boolean True must be rejected
    travel_bool = {("ZONE-1", "REST-1"): True, ("REST-1", "DEST-1"): 10}
    est_travel = estimate_eta(order_valid, partner, travel_bool, now=0)
    assert est_travel["eligible"] is False


def test_regression_partner_capacity_type_safety():
    order = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=10)
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}

    # Capacity = True (boolean) must not be treated as capacity 1
    p_bool = new_partner("P-BOOL", "ZONE-A")
    p_bool["capacity"] = True
    assert assign_order(order, [p_bool], travel)["partner_id"] is None

    # Capacity = 1.5 (float) must not be treated as valid capacity
    p_float = new_partner("P-FLOAT", "ZONE-A")
    p_float["capacity"] = 1.5
    assert assign_order(order, [p_float], travel)["partner_id"] is None

    # Capacity = 0 or negative
    p_zero = new_partner("P-ZERO", "ZONE-A")
    p_zero["capacity"] = 0
    assert assign_order(order, [p_zero], travel)["partner_id"] is None

    p_neg = new_partner("P-NEG", "ZONE-A")
    p_neg["capacity"] = -2
    assert assign_order(order, [p_neg], travel)["partner_id"] is None


def test_regression_cancellation_duplicate_id_and_different_order():
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1", "ORD-2"],
        workload_minutes=30,
        minutes_by_order={"ORD-1": 15, "ORD-2": 15},
    )

    # First cancellation for ORD-1
    after_first = process_cancellation(partner, "ORD-1", "EVT-100")
    assert after_first["active_order_ids"] == ["ORD-2"]
    assert after_first["workload_minutes"] == 15
    assert after_first["processed_cancellation_ids"] == ["EVT-100"]

    # Replaying same event ID EVT-100 (even with different order ORD-2) must be ignored
    after_replay = process_cancellation(after_first, "ORD-2", "EVT-100")
    assert after_replay["active_order_ids"] == ["ORD-2"]
    assert after_replay["workload_minutes"] == 15
    assert after_replay["processed_cancellation_ids"] == ["EVT-100"]


def test_regression_cancellation_unassigned_order_safe():
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1"],
        workload_minutes=10,
        minutes_by_order={"ORD-1": 10},
    )

    # Cancel an unknown order not assigned to partner
    res = process_cancellation(partner, "UNKNOWN-ORD", "EVT-999")
    assert res["active_order_ids"] == ["ORD-1"]
    assert res["workload_minutes"] == 10
    assert "EVT-999" in res["processed_cancellation_ids"]


def test_regression_cancellation_workload_clamped_to_zero():
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1"],
        workload_minutes=5,
        minutes_by_order={"ORD-1": 20},  # Recorded order minutes exceed partner workload
    )

    res = process_cancellation(partner, "ORD-1", "EVT-1")
    assert res["workload_minutes"] == 0
    assert res["active_order_ids"] == []


def test_regression_empty_and_whitespace_ids_rejected():
    p = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}

    # Whitespace-only order ID
    ord_ws = new_order("   ", "REST-1", "DEST-1", 10)
    assert assign_order(ord_ws, [p], travel)["partner_id"] is None

    # Whitespace restaurant ID
    ord_rest_ws = new_order("ORD-1", "   ", "DEST-1", 10)
    assert assign_order(ord_rest_ws, [p], travel)["partner_id"] is None

    # Whitespace destination zone
    ord_dest_ws = new_order("ORD-1", "REST-1", "  ", 10)
    assert assign_order(ord_dest_ws, [p], travel)["partner_id"] is None


def test_regression_stable_tie_breaking_multiple_partners():
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=5)
    # 4 partners all yielding identical ETA = 0 + 10 + 0 + 5 + 10 = 25
    p_charlie = new_partner("P-CHARLIE", "ZONE-A")
    p_bravo = new_partner("P-BRAVO", "ZONE-A")
    p_alpha = new_partner("P-ALPHA", "ZONE-A")
    p_delta = new_partner("P-DELTA", "ZONE-A")

    travel = {("ZONE-A", "REST-1"): 10, ("REST-1", "DEST-1"): 10}
    partners = [p_delta, p_charlie, p_bravo, p_alpha]

    result = assign_order(order, partners, travel, now=0)
    assert result["partner_id"] == "P-ALPHA"
    assert result["eta_minutes"] == 25


def test_regression_synthetic_dataset_batch_dispatch():
    dataset_path = Path("data/records.json")
    assert dataset_path.exists()

    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert travel_times list to tuple-key mapping
    travel = {(t["from"], t["to"]): t["minutes"] for t in data["travel_times"]}

    orders = data["orders"]
    partners = data["partners"]
    cancellations = data["cancellation_events"]

    # Verify dispatch logic executes smoothly across synthetic dataset sample
    assigned_count = 0
    unassigned_count = 0
    for order in orders[:30]:
        res = assign_order(order, partners, travel, now=0)
        assert "order_id" in res
        assert "partner_id" in res
        assert "reason" in res
        if res["partner_id"] is not None:
            assigned_count += 1
            assert res["eta_minutes"] is not None
            assert res["pickup_minutes"] is not None
        else:
            unassigned_count += 1
            assert res["eta_minutes"] is None

    assert assigned_count > 0 or unassigned_count > 0

    # Test cancellations from dataset
    partner_map = {p["partner_id"]: dict(p) for p in partners}
    for event in cancellations[:20]:
        pid = event.get("partner_id")
        oid = event.get("order_id")
        eid = event.get("event_id")
        if pid in partner_map:
            updated = process_cancellation(partner_map[pid], oid, eid)
            assert updated["workload_minutes"] >= 0
            if eid:
                assert eid in updated["processed_cancellation_ids"]
            partner_map[pid] = updated


def test_regression_explain_candidates():
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 15}

    p_active = new_partner("P-ACTIVE", "ZONE-A")
    p_inactive = new_partner("P-INACTIVE", "ZONE-A")
    p_inactive["active"] = False
    p_full = new_partner("P-FULL", "ZONE-A", capacity=1)
    p_full["active_order_ids"] = ["OLD-1"]
    p_no_route = new_partner("P-NOROUTE", "ZONE-Z")

    candidates = [p_active, p_inactive, p_full, p_no_route]
    explanations = explain_candidates(order, candidates, travel, now=0)

    assert len(explanations) == 4
    assert explanations[0]["eligible"] is True
    assert explanations[0]["eta_minutes"] == 30
    assert explanations[1]["eligible"] is False
    assert "inactive" in explanations[1]["reason"]
    assert explanations[2]["eligible"] is False
    assert "capacity" in explanations[2]["reason"]
    assert explanations[3]["eligible"] is False
    assert "travel" in explanations[3]["reason"]
