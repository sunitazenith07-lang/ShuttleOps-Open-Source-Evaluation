import pytest
from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation

TRAVEL = {("Z", "R"): 1, ("R", "D"): 1}


def test_tie_broken_by_partner_id_regardless_of_input_order():
    a, b = new_partner("P-A", "Z"), new_partner("P-B", "Z")
    order = new_order("O", "R", "D")
    for partners in ([a, b], [b, a]):
        assert assign_order(order, partners, TRAVEL)["partner_id"] == "P-A"


def test_missing_travel_is_not_treated_as_zero():
    result = assign_order(new_order("O", "R", "D"), [new_partner("P", "Z")], {("Z", "R"): 1})
    assert result["partner_id"] is None
    assert "P: missing travel-time entry" in result["details"]


def test_fast_partner_with_missing_route_loses_to_slower_complete_partner():
    fast = new_partner("P-FAST", "Z-NOROUTE")
    slow = new_partner("P-SLOW", "Z"); slow["workload_minutes"] = 50
    result = assign_order(new_order("O", "R", "D"), [fast, slow], TRAVEL)
    assert result["partner_id"] == "P-SLOW"


@pytest.mark.parametrize("workload", [-1, None, "3", True, float("nan")])
def test_invalid_partner_workload_is_ineligible(workload):
    p = new_partner("P", "Z"); p["workload_minutes"] = workload
    assert estimate_eta(new_order("O", "R", "D"), p, TRAVEL)["eligible"] is False


@pytest.mark.parametrize("partners", [[], None, ["junk", 5, None]])
def test_empty_or_malformed_partner_lists_do_not_raise(partners):
    result = assign_order(new_order("O", "R", "D"), partners, TRAVEL)
    assert result["partner_id"] is None and result["reason"]


@pytest.mark.parametrize("order", [None, {}, "x", 5])
def test_malformed_order_does_not_raise(order):
    assert assign_order(order, [new_partner("P", "Z")], TRAVEL)["partner_id"] is None


def test_unknown_restaurant_and_zone_leave_order_unassigned():
    p = new_partner("P", "Z")
    assert assign_order(new_order("O", "R-X", "D"), [p], TRAVEL)["partner_id"] is None
    assert assign_order(new_order("O", "R", "D-X"), [p], TRAVEL)["partner_id"] is None


def test_inputs_are_not_mutated_and_results_are_deterministic():
    order = new_order("O", "R", "D")
    partners = [new_partner("P-B", "Z"), new_partner("P-A", "Z")]
    snapshot = ([dict(p) for p in partners], dict(order), dict(TRAVEL))
    r1 = assign_order(order, partners, TRAVEL)
    r2 = assign_order(order, partners, TRAVEL)
    assert r1 == r2
    assert ([dict(p) for p in partners], dict(order), dict(TRAVEL)) == snapshot


def test_cancellation_releases_once_and_never_below_zero():
    p = new_partner("P", "Z")
    p.update(active_order_ids=["O1", "O2"], workload_minutes=12,
             minutes_by_order={"O1": 5, "O2": 7})
    once = process_cancellation(p, "O1", "C1")
    replay = process_cancellation(once, "O1", "C1")
    other_id = process_cancellation(replay, "O1", "C2")   # order already released
    assert once["workload_minutes"] == 7 and once["active_order_ids"] == ["O2"]
    assert replay == once
    assert other_id["workload_minutes"] == 7 and other_id["active_order_ids"] == ["O2"]
    final = process_cancellation(other_id, "O2", "C3")
    assert final["workload_minutes"] == 0 and final["active_order_ids"] == []


def test_cancellation_of_unknown_order_is_a_safe_noop():
    p = new_partner("P", "Z"); p.update(active_order_ids=["O1"], workload_minutes=5,
                                        minutes_by_order={"O1": 5})
    out = process_cancellation(p, "NOPE", "C1")
    assert out["active_order_ids"] == ["O1"] and out["workload_minutes"] == 5


def test_cancellation_does_not_mutate_input():
    p = new_partner("P", "Z"); p.update(active_order_ids=["O1"], workload_minutes=5,
                                        minutes_by_order={"O1": 5})
    process_cancellation(p, "O1", "C1")
    assert p["active_order_ids"] == ["O1"] and p["workload_minutes"] == 5


def test_capacity_freed_exactly_once_by_duplicate_cancellation():
    p = new_partner("P", "Z", capacity=1)
    p.update(active_order_ids=["O1"], workload_minutes=5, minutes_by_order={"O1": 5})
    assert assign_order(new_order("N", "R", "D"), [p], TRAVEL)["partner_id"] is None
    freed = process_cancellation(process_cancellation(p, "O1", "C1"), "O1", "C1")
    assert assign_order(new_order("N", "R", "D"), [freed], TRAVEL)["partner_id"] == "P"