import pytest
from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation


def test_edge_case_whitespace_or_empty_ids_rejected():
    """Verify orders with whitespace-only IDs are treated as invalid and unassigned."""
    order = new_order("   ", "R-1", "Z-1", 10)
    result = assign_order(order, [new_partner("P-1", "Z-1")], {("Z-1", "R-1"): 5, ("R-1", "Z-1"): 5})
    assert result["partner_id"] is None
    assert result["reason"] == "invalid order or time data"


def test_edge_case_boolean_workload_rejected():
    """Verify boolean workload (e.g. True/False) is rejected rather than coerced to 1/0."""
    order = new_order("O-1", "R-1", "Z-1", 10)
    partner = new_partner("P-1", "Z-1")
    partner["workload_minutes"] = True
    result = estimate_eta(order, partner, {("Z-1", "R-1"): 5, ("R-1", "Z-1"): 5})
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_edge_case_negative_workload_rejected():
    """Verify negative partner workload causes candidate to be ineligible."""
    order = new_order("O-1", "R-1", "Z-1", 10)
    partner = new_partner("P-1", "Z-1")
    partner["workload_minutes"] = -15
    result = estimate_eta(order, partner, {("Z-1", "R-1"): 5, ("R-1", "Z-1"): 5})
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_edge_case_cancellation_unknown_order_and_idempotency():
    """Verify cancellation for an unassigned order records event ID once without side effects, and deduplicates replay."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["O-EXISTING"], workload_minutes=25, minutes_by_order={"O-EXISTING": 25})
    
    # Process cancellation for an unknown order
    first = process_cancellation(partner, "O-UNKNOWN", "EVENT-99")
    assert first["processed_cancellation_ids"] == ["EVENT-99"]
    assert first["active_order_ids"] == ["O-EXISTING"]
    assert first["workload_minutes"] == 25

    # Replay same event ID
    second = process_cancellation(first, "O-UNKNOWN", "EVENT-99")
    assert second["processed_cancellation_ids"] == ["EVENT-99"]
    assert second["active_order_ids"] == ["O-EXISTING"]
    assert second["workload_minutes"] == 25


def test_edge_case_capacity_saturation_boundary():
    """Verify partner is eligible at capacity-1 and strictly rejected when active orders equal capacity."""
    order = new_order("O-NEW", "R-1", "Z-1", 10)
    travel = {("Z-1", "R-1"): 5, ("R-1", "Z-1"): 5}
    partner = new_partner("P-1", "Z-1", capacity=2)
    partner["active_order_ids"] = ["O-PREV-1"]

    # 1 active order with capacity 2 -> eligible
    res1 = assign_order(order, [partner], travel)
    assert res1["partner_id"] == "P-1"

    # 2 active orders with capacity 2 -> saturated, ineligible
    partner["active_order_ids"] = ["O-PREV-1", "O-PREV-2"]
    res2 = assign_order(order, [partner], travel)
    assert res2["partner_id"] is None
    assert res2["reason"] == "no eligible partner or missing time data"


def test_edge_case_none_partners_or_travel_handled_safely():
    """Verify None passed as partners list or travel map does not throw exception."""
    order = new_order("O-1", "R-1", "Z-1", 10)
    res_none_partners = assign_order(order, None, {})
    assert res_none_partners["partner_id"] is None

    res_none_travel = assign_order(order, [new_partner("P-1", "Z-1")], None)
    assert res_none_travel["partner_id"] is None


def test_stretch_explain_candidates_reasons():
    """Verify explain_candidates provides diagnostic status and reasons for all partners."""
    from service import explain_candidates

    order = new_order("O-10", "R-1", "Z-DEST", 10)
    p_inactive = new_partner("P-INACTIVE", "Z-1")
    p_inactive["active"] = False

    p_full = new_partner("P-FULL", "Z-1", capacity=1)
    p_full["active_order_ids"] = ["OLD-1"]

    p_noroute = new_partner("P-NOROUTE", "Z-UNKNOWN")

    p_eligible1 = new_partner("P-ELIG-1", "Z-1")
    p_eligible2 = new_partner("P-ELIG-2", "Z-2")

    travel = {
        ("Z-1", "R-1"): 5,
        ("Z-2", "R-1"): 15,
        ("R-1", "Z-DEST"): 10,
    }

    partners = [p_inactive, p_full, p_noroute, p_eligible1, p_eligible2]
    exp = explain_candidates(order, partners, travel, now=0)

    assert exp["P-INACTIVE"]["eligible"] is False
    assert exp["P-INACTIVE"]["reason"] == "partner is inactive"

    assert exp["P-FULL"]["eligible"] is False
    assert "capacity reached" in exp["P-FULL"]["reason"]

    assert exp["P-NOROUTE"]["eligible"] is False
    assert "missing or invalid travel route" in exp["P-NOROUTE"]["reason"]

    assert exp["P-ELIG-1"]["eligible"] is True
    assert exp["P-ELIG-1"]["is_selected"] is True
    assert exp["P-ELIG-1"]["eta_minutes"] == 25  # 0 + 5 + 10 + 10

    assert exp["P-ELIG-2"]["eligible"] is True
    assert exp["P-ELIG-2"]["is_selected"] is False
    assert exp["P-ELIG-2"]["eta_minutes"] == 35  # 0 + 15 + 10 + 10

