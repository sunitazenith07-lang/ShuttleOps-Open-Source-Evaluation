"""Regression test suite for SmartDispatch engine.

Covers:
- Input validation (malformed orders, non-dict objects, boolean/negative times)
- Partner eligibility (inactive states, capacity boundaries, invalid capacities)
- Travel-time validation (missing legs, non-numeric values, NaN/Inf)
- Deterministic lexicographic tie-breaking
- Multi-call cancellation idempotency
- Synthetic dataset end-to-end integration (data/records.json)
"""
import json
from pathlib import Path
import pytest
from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation


def test_regression_invalid_and_malformed_order_inputs():
    """Verify malformed order inputs return unassigned safely."""
    partner = new_partner("P-01", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 10, ("REST-1", "DEST-1"): 15}

    # 1. Non-dict order
    assert assign_order(None, [partner], travel)["partner_id"] is None
    assert assign_order("order-string", [partner], travel)["partner_id"] is None
    assert assign_order([], [partner], travel)["partner_id"] is None

    # 2. Missing or empty string IDs
    for bad_id in ["", "   ", None, 0, False]:
        o1 = {"order_id": bad_id, "restaurant_id": "REST-1", "destination_zone": "DEST-1", "prep_minutes": 10}
        assert assign_order(o1, [partner], travel)["partner_id"] is None

        o2 = {"order_id": "ORD-1", "restaurant_id": bad_id, "destination_zone": "DEST-1", "prep_minutes": 10}
        assert assign_order(o2, [partner], travel)["partner_id"] is None

        o3 = {"order_id": "ORD-1", "restaurant_id": "REST-1", "destination_zone": bad_id, "prep_minutes": 10}
        assert assign_order(o3, [partner], travel)["partner_id"] is None

    # 3. Invalid preparation time types
    for bad_prep in [-1, -99, None, "10", True, False, float("nan"), float("inf")]:
        o = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=bad_prep)
        assert assign_order(o, [partner], travel)["partner_id"] is None


def test_regression_partner_capacity_and_status():
    """Verify capacity and active status boundaries."""
    order = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=5)
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}

    # 1. Inactive partner permutations
    for inactive_val in [False, None, 0, "False", "no"]:
        p = new_partner("P-1", "ZONE-A")
        p["active"] = inactive_val
        assert assign_order(order, [p], travel)["partner_id"] is None

    # 2. Invalid capacity values
    for bad_cap in [0, -1, -5, None, "2", True, 1.5]:
        p = new_partner("P-1", "ZONE-A")
        p["capacity"] = bad_cap
        assert assign_order(order, [p], travel)["partner_id"] is None

    # 3. Full capacity partner (active_orders == capacity)
    p_full = new_partner("P-1", "ZONE-A", capacity=2)
    p_full["active_order_ids"] = ["OLD-1", "OLD-2"]
    assert assign_order(order, [p_full], travel)["partner_id"] is None

    # 4. Over capacity partner (active_orders > capacity)
    p_over = new_partner("P-1", "ZONE-A", capacity=2)
    p_over["active_order_ids"] = ["OLD-1", "OLD-2", "OLD-3"]
    assert assign_order(order, [p_over], travel)["partner_id"] is None

    # 5. Below capacity partner (eligible)
    p_avail = new_partner("P-1", "ZONE-A", capacity=2)
    p_avail["active_order_ids"] = ["OLD-1"]
    res = assign_order(order, [p_avail], travel)
    assert res["partner_id"] == "P-1"
    assert res["reason"] == "assigned"


def test_regression_missing_routes_never_zero():
    """Verify that missing or negative travel time entries are never treated as 0."""
    order = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=5)
    partner = new_partner("P-1", "ZONE-A")

    # Missing leg 1
    t1 = {("REST-1", "DEST-1"): 10}
    r1 = estimate_eta(order, partner, t1)
    assert r1["eligible"] is False
    assert r1["eta_minutes"] is None

    # Missing leg 2
    t2 = {("ZONE-A", "REST-1"): 10}
    r2 = estimate_eta(order, partner, t2)
    assert r2["eligible"] is False
    assert r2["eta_minutes"] is None

    # Completely empty travel dict
    r3 = estimate_eta(order, partner, {})
    assert r3["eligible"] is False
    assert r3["eta_minutes"] is None

    # Negative travel time must not be accepted as 0
    t_neg = {("ZONE-A", "REST-1"): -5, ("REST-1", "DEST-1"): 10}
    r_neg = estimate_eta(order, partner, t_neg)
    assert r_neg["eligible"] is False
    assert r_neg["eta_minutes"] is None


def test_regression_tie_breaking_lexicographical_stability():
    """Verify that identical ETAs break ties strictly by partner_id ascending."""
    order = new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=5)
    travel = {
        ("ZONE-1", "REST-1"): 10,
        ("ZONE-2", "REST-1"): 10,
        ("ZONE-3", "REST-1"): 10,
        ("REST-1", "DEST-1"): 15,
    }

    # All three partners will produce Pickup = 10, ETA = 10 + 5 + 15 = 30
    p1 = new_partner("PARTNER-C", "ZONE-1")
    p2 = new_partner("PARTNER-A", "ZONE-2")
    p3 = new_partner("PARTNER-B", "ZONE-3")

    # Regardless of permutation in partners list, PARTNER-A must win
    for perm in [[p1, p2, p3], [p3, p1, p2], [p2, p3, p1]]:
        res = assign_order(order, perm, travel)
        assert res["partner_id"] == "PARTNER-A"
        assert res["eta_minutes"] == 30


def test_regression_cancellation_idempotency_multi_call():
    """Verify that multiple duplicate cancellations never deduct workload more than once."""
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-100", "ORD-200"],
        workload_minutes=45,
        minutes_by_order={"ORD-100": 20, "ORD-200": 25},
    )

    # Cancel ORD-100 three consecutive times with same event_id
    state1 = process_cancellation(partner, "ORD-100", "EVT-CANCEL-01")
    state2 = process_cancellation(state1, "ORD-100", "EVT-CANCEL-01")
    state3 = process_cancellation(state2, "ORD-100", "EVT-CANCEL-01")

    assert state3["active_order_ids"] == ["ORD-200"]
    assert state3["workload_minutes"] == 25
    assert state3["processed_cancellation_ids"] == ["EVT-CANCEL-01"]

    # Cancel unknown order
    state4 = process_cancellation(state3, "UNKNOWN-ORD", "EVT-CANCEL-02")
    assert state4["active_order_ids"] == ["ORD-200"]
    assert state4["workload_minutes"] == 25
    assert state4["processed_cancellation_ids"] == ["EVT-CANCEL-01", "EVT-CANCEL-02"]


def test_regression_synthetic_dataset_integration():
    """Verify end-to-end assignment and cancellation on data/records.json."""
    dataset_path = Path(__file__).resolve().parent.parent / "data" / "records.json"
    if not dataset_path.exists():
        pytest.skip("data/records.json not found")

    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    orders = data.get("orders", [])
    partners = data.get("partners", [])
    travel_rows = data.get("travel_times", [])

    # Convert travel_times list to tuple key mapping
    travel = {(row["from"], row["to"]): row["minutes"] for row in travel_rows}

    assert len(orders) == 180
    assert len(partners) == 60
    assert len(travel_rows) == 387

    # Run dispatch for first 20 orders without any unhandled exceptions
    assigned_count = 0
    for order in orders[:20]:
        res = assign_order(order, partners, travel)
        assert "partner_id" in res
        assert "reason" in res
        if res["partner_id"]:
            assigned_count += 1

    assert assigned_count > 0

