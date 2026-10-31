"""Regression coverage for malformed records and cancellation safety."""

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def test_malformed_order_and_partner_inputs_fail_closed():
    partner = new_partner("P", "Z")
    assert assign_order(None, [partner], {})["partner_id"] is None
    assert assign_order(new_order("O", "R", "D"), None, {})["partner_id"] is None
    assert estimate_eta([], partner, {})["eligible"] is False


def test_malformed_capacity_and_active_order_list_are_ineligible():
    order = new_order("O", "R", "D")
    travel = {("Z", "R"): 1, ("R", "D"): 1}
    partner = new_partner("P", "Z")

    partner["capacity"] = True
    assert assign_order(order, [partner], travel)["partner_id"] is None

    partner = new_partner("P", "Z")
    partner["active_order_ids"] = "not-a-list"
    assert assign_order(order, [partner], travel)["partner_id"] is None


def test_non_mapping_travel_and_invalid_workload_fail_closed():
    order = new_order("O", "R", "D")
    partner = new_partner("P", "Z")
    assert estimate_eta(order, partner, [])["eligible"] is False

    partner["workload_minutes"] = -1
    assert estimate_eta(order, partner, {("Z", "R"): 1, ("R", "D"): 1})[
        "eligible"
    ] is False


def test_cancellation_is_copy_on_write_and_unknown_order_does_not_release_work():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1"],
        workload_minutes=9,
        minutes_by_order={"O1": 9},
    )

    result = process_cancellation(partner, "UNKNOWN", "C1")
    assert result["active_order_ids"] == ["O1"]
    assert result["workload_minutes"] == 9
    assert result["processed_cancellation_ids"] == ["C1"]
    assert partner["active_order_ids"] == ["O1"]
    assert partner["processed_cancellation_ids"] == []


def test_invalid_cancellation_event_does_not_change_partner_state():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["O1"], workload_minutes=9)

    result = process_cancellation(partner, "O1", None)
    assert result["active_order_ids"] == ["O1"]
    assert result["workload_minutes"] == 9
    assert result["processed_cancellation_ids"] == []


def test_no_candidate_reason_names_capacity_and_route_problems():
    order = new_order("O", "R", "D")
    full = new_partner("P-FULL", "Z")
    full["active_order_ids"] = ["OLD-1", "OLD-2"]
    route_missing = new_partner("P-ROUTE", "X")

    result = assign_order(order, [full, route_missing], {("X", "R"): 1})
    assert result["partner_id"] is None
    assert "capacity reached" in result["reason"]
    assert "missing or invalid ETA data" in result["reason"]
