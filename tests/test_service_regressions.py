from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def test_malformed_records_are_rejected_without_an_exception():
    result = assign_order(
        new_order("O", "R", "D"),
        [{"partner_id": "P", "active": True, "capacity": 1}],
        {("Z", "R"): 1, ("R", "D"): 1},
    )
    assert result["partner_id"] is None
    assert estimate_eta(None, None, None)["eligible"] is False


def test_assignment_requires_a_real_boolean_active_flag():
    partner = new_partner("P", "Z")
    partner["active"] = "yes"
    result = assign_order(new_order("O", "R", "D"), [partner], {("Z", "R"): 1, ("R", "D"): 1})
    assert result["partner_id"] is None


def test_cancellation_records_once_and_does_not_mutate_input():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["O"], workload_minutes=8, minutes_by_order={"O": 5})
    cancelled = process_cancellation(partner, "O", "cancel-1")
    duplicate = process_cancellation(cancelled, "O", "cancel-1")
    assert partner["active_order_ids"] == ["O"]
    assert duplicate["active_order_ids"] == []
    assert duplicate["workload_minutes"] == 3
    assert duplicate["processed_cancellation_ids"] == ["cancel-1"]
