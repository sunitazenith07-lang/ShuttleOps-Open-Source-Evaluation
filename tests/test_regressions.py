"""Regression tests for the dispatch fixes.

These complement the visible contract tests by covering malformed records,
input immutability, lexicographic tie-breaking and cancellation deduplication
cases that are easy to regress when the validation logic is changed.
"""

import json
from pathlib import Path

import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def test_invalid_order_identifiers_and_malformed_order_are_safe():
    valid_travel = {("Z", "R"): 1, ("R", "D"): 1}
    partner = new_partner("P", "Z")

    for bad_order in (None, [], "order", {"order_id": "   "}):
        result = assign_order(bad_order, [partner], valid_travel)
        assert result["partner_id"] is None
        assert result["reason"].startswith("invalid order")


def test_partner_with_negative_workload_is_not_assigned():
    order = new_order("O", "R", "D")
    broken = new_partner("A", "Z")
    broken["workload_minutes"] = -1
    healthy = new_partner("B", "Z")
    healthy["workload_minutes"] = 2

    result = assign_order(order, [broken, healthy], {("Z", "R"): 1, ("R", "D"): 1})

    assert result["partner_id"] == "B"
    assert result["pickup_minutes"] == 3


def test_missing_route_for_one_candidate_does_not_block_another():
    order = new_order("O", "R", "D")
    missing_route = new_partner("A", "X")
    complete_route = new_partner("B", "Y")

    result = assign_order(
        order,
        [missing_route, complete_route],
        {("Y", "R"): 2, ("R", "D"): 4},
    )

    assert result["partner_id"] == "B"
    assert result["eta_minutes"] == 16


def test_tie_break_is_lexicographic_not_numeric():
    order = new_order("O", "R", "D", 0)
    partners = [new_partner("P2", "Z"), new_partner("P10", "Z")]

    result = assign_order(order, partners, {("Z", "R"): 1, ("R", "D"): 1})

    assert result["partner_id"] == "P10"


def test_malformed_partner_records_are_skipped():
    order = new_order("O", "R", "D")
    valid = new_partner("P", "Z")

    result = assign_order(
        order,
        [None, "not-a-partner", {"partner_id": "X"}, valid],
        {("Z", "R"): 1, ("R", "D"): 1},
    )

    assert result["partner_id"] == "P"


def test_travel_mapping_none_is_safe_and_not_zero():
    result = estimate_eta(new_order("O", "R", "D"), new_partner("P", "Z"), None)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_assignment_does_not_mutate_inputs():
    order = new_order("O", "R", "D")
    partner = new_partner("P", "Z")
    partner["active_order_ids"] = ["OLD"]
    partners = [partner]
    travel = {("Z", "R"): 1, ("R", "D"): 1}
    before = (dict(order), [dict(partner)], dict(travel))

    assign_order(order, partners, travel, now=5)

    assert (dict(order), [dict(partner)], dict(travel)) == before


def test_same_order_with_different_event_ids_is_not_released_twice():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O"],
        workload_minutes=9,
        minutes_by_order={"O": 9},
    )

    first = process_cancellation(partner, "O", "C1")
    second = process_cancellation(first, "O", "C2")

    assert first["active_order_ids"] == []
    assert second["active_order_ids"] == []
    assert second["workload_minutes"] == 0
    assert second["processed_cancellation_ids"] == ["C1", "C2"]


def test_duplicate_event_id_for_another_order_is_ignored():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1", "O2"],
        workload_minutes=10,
        minutes_by_order={"O1": 4, "O2": 6},
    )

    once = process_cancellation(partner, "O1", "C1")
    duplicate = process_cancellation(once, "O2", "C1")

    assert duplicate["active_order_ids"] == ["O2"]
    assert duplicate["workload_minutes"] == 6
    assert duplicate["processed_cancellation_ids"] == ["C1"]


def test_cancellation_accepts_tuple_and_set_state_deterministically():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=("O1", "O2"),
        workload_minutes=10,
        minutes_by_order={"O1": 4, "O2": 6},
        processed_cancellation_ids={"C0"},
    )

    result = process_cancellation(partner, "O1", "C1")

    assert result["active_order_ids"] == ["O2"]
    assert result["workload_minutes"] == 6
    assert result["processed_cancellation_ids"] == ["C0", "C1"]
    assert partner["active_order_ids"] == ("O1", "O2")
    assert partner["processed_cancellation_ids"] == {"C0"}


def test_cancellation_with_malformed_minutes_does_not_guess_workload():
    partner = new_partner("P", "Z")
    partner["active_order_ids"] = ["O"]
    partner["workload_minutes"] = 3
    partner["minutes_by_order"] = {"O": "malformed"}

    result = process_cancellation(partner, "O", "C")

    assert result["active_order_ids"] == []
    assert result["workload_minutes"] == 3
    assert result["processed_cancellation_ids"] == ["C"]


def test_expanded_dataset_is_deterministic_and_safe():
    data_path = Path(__file__).resolve().parents[1] / "data" / "records.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    travel = {
        (row["from"], row["to"]): row["minutes"] for row in data["travel_times"]
    }

    for order in data["orders"]:
        result = assign_order(order, data["partners"], travel)
        assert result["partner_id"] is None or isinstance(result["partner_id"], str)
        assert result["eta_minutes"] is None or result["eta_minutes"] >= 0

    sample = data["orders"][0]
    forward = assign_order(sample, data["partners"], travel)
    reverse = assign_order(sample, list(reversed(data["partners"])), travel)
    assert forward == reverse
