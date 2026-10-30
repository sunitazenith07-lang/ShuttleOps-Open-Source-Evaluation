import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


@pytest.mark.parametrize("workload", [None, -1, True, float("nan"), float("inf")])
def test_invalid_partner_workload_makes_eta_ineligible(workload):
    partner = new_partner("P", "Z")
    partner["workload_minutes"] = workload

    result = estimate_eta(
        new_order("O", "R", "D"),
        partner,
        {("Z", "R"): 1, ("R", "D"): 1},
    )

    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_malformed_order_and_partner_collection_are_unassigned_safely():
    order = new_order("O", "R", "D")
    order["restaurant_id"] = None

    invalid_order_result = assign_order(
        order, [new_partner("P", "Z")], {("Z", "R"): 1, ("R", "D"): 1}
    )
    invalid_collection_result = assign_order(
        new_order("O", "R", "D"), None, {}
    )

    assert invalid_order_result["partner_id"] is None
    assert invalid_order_result["reason"] == "invalid order data"
    assert invalid_collection_result["partner_id"] is None
    assert "partner collection" in invalid_collection_result["reason"]


@pytest.mark.parametrize(
    ("partner", "active_order_ids", "travel", "reason_fragment"),
    [
        (
            new_partner("P", "Z", capacity=1),
            ["ACTIVE"],
            {("Z", "R"): 1, ("R", "D"): 1},
            "capacity",
        ),
        (new_partner("P", "Z"), [], {}, "travel-time"),
    ],
)
def test_unassigned_result_explains_candidate_exclusion(
    partner, active_order_ids, travel, reason_fragment
):
    partner["active_order_ids"] = active_order_ids

    result = assign_order(new_order("O", "R", "D"), [partner], travel)

    assert result["partner_id"] is None
    assert reason_fragment in result["reason"]


def test_duplicate_cancellation_event_cannot_cancel_another_order():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1", "O2"],
        workload_minutes=12,
        minutes_by_order={"O1": 5, "O2": 7},
    )

    after_first = process_cancellation(partner, "O1", "C1")
    after_duplicate = process_cancellation(after_first, "O2", "C1")

    assert after_duplicate["active_order_ids"] == ["O2"]
    assert after_duplicate["workload_minutes"] == 7
    assert after_duplicate["processed_cancellation_ids"] == ["C1"]
    assert partner["active_order_ids"] == ["O1", "O2"]
    assert partner["workload_minutes"] == 12


def test_cancellation_removes_duplicate_order_entries_but_releases_workload_once():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1", "O1"],
        workload_minutes=9,
        minutes_by_order={"O1": 9},
    )

    result = process_cancellation(partner, "O1", "C1")

    assert result["active_order_ids"] == []
    assert result["workload_minutes"] == 0
