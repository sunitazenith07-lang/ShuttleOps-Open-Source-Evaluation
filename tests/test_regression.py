import json
from pathlib import Path
import pytest
from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation, batch_assign_orders


def test_regression_travel_time_non_numeric_and_special_floats():
    """Verify that boolean, string, inf, and nan travel times are safely rejected."""
    order = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=15)
    partner = new_partner("PARTNER-1", "ZONE-B")

    # String travel time
    res_str = estimate_eta(order, partner, {("ZONE-B", "REST-1"): "10", ("REST-1", "ZONE-A"): 10})
    assert res_str["eligible"] is False
    assert res_str["eta_minutes"] is None

    # Boolean travel time (True/False should not be treated as 1/0)
    res_bool = estimate_eta(order, partner, {("ZONE-B", "REST-1"): True, ("REST-1", "ZONE-A"): 10})
    assert res_bool["eligible"] is False
    assert res_bool["eta_minutes"] is None

    # NaN and Inf travel time
    res_nan = estimate_eta(order, partner, {("ZONE-B", "REST-1"): float("nan"), ("REST-1", "ZONE-A"): 10})
    assert res_nan["eligible"] is False
    assert res_nan["eta_minutes"] is None

    res_inf = estimate_eta(order, partner, {("ZONE-B", "REST-1"): float("inf"), ("REST-1", "ZONE-A"): 10})
    assert res_inf["eligible"] is False
    assert res_inf["eta_minutes"] is None


def test_regression_negative_travel_and_prep_times():
    """Verify that negative travel times and prep times are rejected."""
    order_neg_prep = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=-10)
    partner = new_partner("PARTNER-1", "ZONE-B")
    travel = {("ZONE-B", "REST-1"): 5, ("REST-1", "ZONE-A"): 5}

    res_prep = estimate_eta(order_neg_prep, partner, travel)
    assert res_prep["eligible"] is False
    assert res_prep["eta_minutes"] is None

    # Negative leg 1
    order_valid = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=10)
    res_leg1 = estimate_eta(order_valid, partner, {("ZONE-B", "REST-1"): -5, ("REST-1", "ZONE-A"): 5})
    assert res_leg1["eligible"] is False

    # Negative leg 2
    res_leg2 = estimate_eta(order_valid, partner, {("ZONE-B", "REST-1"): 5, ("REST-1", "ZONE-A"): -5})
    assert res_leg2["eligible"] is False


def test_regression_inactive_partner_filtering():
    """Inactive partners must never receive assignments."""
    order = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=10)
    travel = {("ZONE-B", "REST-1"): 5, ("REST-1", "ZONE-A"): 5}

    p_false = new_partner("P-FALSE", "ZONE-B")
    p_false["active"] = False

    p_none = new_partner("P-NONE", "ZONE-B")
    p_none["active"] = None

    p_zero = new_partner("P-ZERO", "ZONE-B")
    p_zero["active"] = 0

    p_str = new_partner("P-STR", "ZONE-B")
    p_str["active"] = "active"

    res = assign_order(order, [p_false, p_none, p_zero, p_str], travel)
    assert res["partner_id"] is None
    assert "no eligible partner" in res["reason"]


def test_regression_capacity_boundary_and_validation():
    """Partner capacity must be an integer >= 1, and active orders must be strictly < capacity."""
    order = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=10)
    travel = {("ZONE-B", "REST-1"): 5, ("REST-1", "ZONE-A"): 5}

    # At full capacity (2 active orders, capacity 2)
    p_full = new_partner("P-FULL", "ZONE-B", capacity=2)
    p_full["active_order_ids"] = ["O1", "O2"]
    assert assign_order(order, [p_full], travel)["partner_id"] is None

    # Invalid capacity types (0, negative, float, bool, None)
    for invalid_cap in [0, -1, 1.5, True, False, None, "2"]:
        p_invalid = new_partner("P-INV", "ZONE-B", capacity=2)
        p_invalid["capacity"] = invalid_cap
        assert assign_order(order, [p_invalid], travel)["partner_id"] is None


def test_regression_lexicographic_tie_breaking():
    """When multiple partners yield the exact same ETA, break ties lexicographically by partner ID."""
    order = new_order("ORD-1", "REST-1", "ZONE-A", prep_minutes=10)
    travel = {
        ("ZONE-1", "REST-1"): 5,
        ("ZONE-2", "REST-1"): 5,
        ("ZONE-3", "REST-1"): 5,
        ("REST-1", "ZONE-A"): 10,
    }

    # All produce ETA = 0 + 5 + 0 + 10 + 10 = 25
    p_c = new_partner("PARTNER-C", "ZONE-3")
    p_a = new_partner("PARTNER-A", "ZONE-1")
    p_b = new_partner("PARTNER-B", "ZONE-2")

    # Pass in reverse order to ensure input order does not dictate the outcome
    result = assign_order(order, [p_c, p_b, p_a], travel)
    assert result["partner_id"] == "PARTNER-A"
    assert result["eta_minutes"] == 25
    assert result["pickup_minutes"] == 5


def test_regression_cancellation_idempotency_and_clamping():
    """Cancellation events must be strictly idempotent and never reduce workload below zero."""
    partner = new_partner("P-1", "ZONE-A")
    partner.update({
        "active_order_ids": ["ORD-100"],
        "workload_minutes": 15,
        "minutes_by_order": {"ORD-100": 20},  # minutes > workload to test floor clamping
    })

    # First cancellation
    p_after_1 = process_cancellation(partner, "ORD-100", "EV-100")
    assert p_after_1["active_order_ids"] == []
    assert p_after_1["workload_minutes"] == 0  # clamped at 0
    assert p_after_1["processed_cancellation_ids"] == ["EV-100"]

    # Duplicate cancellation with identical event ID
    p_after_2 = process_cancellation(p_after_1, "ORD-100", "EV-100")
    assert p_after_2["active_order_ids"] == []
    assert p_after_2["workload_minutes"] == 0
    assert p_after_2["processed_cancellation_ids"] == ["EV-100"]  # Not added twice


def test_regression_malformed_inputs_gracefully_handled():
    """Empty inputs, None, and unknown IDs should be handled gracefully without crashing."""
    valid_order = new_order("ORD-1", "REST-1", "DEST-1")
    valid_partner = new_partner("P-1", "ZONE-1")
    valid_travel = {("ZONE-1", "REST-1"): 5, ("REST-1", "DEST-1"): 5}

    # Empty/None partners list
    res1 = assign_order(valid_order, [], valid_travel)
    assert res1["partner_id"] is None

    res2 = assign_order(valid_order, None, valid_travel)
    assert res2["partner_id"] is None

    # Empty/None travel mapping
    res3 = assign_order(valid_order, [valid_partner], {})
    assert res3["partner_id"] is None

    res4 = assign_order(valid_order, [valid_partner], None)
    assert res4["partner_id"] is None

    # Malformed/None order
    res5 = assign_order(None, [valid_partner], valid_travel)
    assert res5["partner_id"] is None
    assert res5["order_id"] is None


def test_regression_synthetic_records_dataset_integration():
    """Integration test loading records.json and validating the whole dataset behavior."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "records.json"
    if not data_path.exists():
        pytest.skip("data/records.json not found")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    travel_map = {(row["from"], row["to"]): row["minutes"] for row in data["travel_times"]}
    partners = data["partners"]
    orders = data["orders"]

    # Verify that assignment runs over all 180 orders deterministically
    assigned_count = 0
    unassigned_count = 0
    for order in orders:
        res = assign_order(order, partners, travel_map)
        assert "order_id" in res
        assert "reason" in res
        if res["partner_id"] is not None:
            assigned_count += 1
            assert res["eta_minutes"] is not None
            assert res["pickup_minutes"] is not None
        else:
            unassigned_count += 1
            assert res["eta_minutes"] is None

    assert assigned_count == 170
    assert unassigned_count == 10

    # Specifically verify the 10 known unassigned orders due to missing travel routes
    unassigned_order_ids = [
        "DSP-ORD-0001", "DSP-ORD-0012", "DSP-ORD-0037", "DSP-ORD-0048",
        "DSP-ORD-0073", "DSP-ORD-0084", "DSP-ORD-0109", "DSP-ORD-0120",
        "DSP-ORD-0145", "DSP-ORD-0156"
    ]
    for oid in unassigned_order_ids:
        target_order = next(o for o in orders if o["order_id"] == oid)
        res = assign_order(target_order, partners, travel_map)
        assert res["partner_id"] is None
        assert res["reason"] == "no eligible partner or missing time data"


def test_regression_batch_assignment_stretch_feature():
    """Verify batch assignment processes orders sequentially and updates partner capacity."""
    o1 = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=5)
    o2 = new_order("ORD-2", "REST-1", "DEST-1", prep_minutes=5)
    o3 = new_order("ORD-3", "REST-1", "DEST-1", prep_minutes=5)

    # Partner with capacity 2
    partner = new_partner("P-SOLO", "ZONE-1", capacity=2)
    travel = {("ZONE-1", "REST-1"): 4, ("REST-1", "DEST-1"): 6}

    results = batch_assign_orders([o1, o2, o3], [partner], travel, now=0)
    assert len(results) == 3

    # First order assigned
    assert results[0]["partner_id"] == "P-SOLO"
    assert results[0]["reason"] == "assigned"

    # Second order assigned (capacity now reached: 2 active orders)
    assert results[1]["partner_id"] == "P-SOLO"
    assert results[1]["reason"] == "assigned"

    # Third order cannot be assigned because partner capacity is full
    assert results[2]["partner_id"] is None
    assert results[2]["reason"] == "no eligible partner or missing time data"

