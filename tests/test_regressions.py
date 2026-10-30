"""Regression tests for service behavior and the expanded synthetic dataset."""

import json
from pathlib import Path

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def test_cancellation_duplicate_event_with_different_payload_is_ignored():
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["O-1", "O-2"],
        workload_minutes=15,
        minutes_by_order={"O-1": 6, "O-2": 9},
    )

    after_first = process_cancellation(partner, "O-1", "C-1")
    after_duplicate = process_cancellation(after_first, "O-2", "C-1")

    assert partner["active_order_ids"] == ["O-1", "O-2"]
    assert partner["workload_minutes"] == 15
    assert after_first["active_order_ids"] == ["O-2"]
    assert after_first["workload_minutes"] == 9
    assert after_duplicate == after_first
    assert after_duplicate["processed_cancellation_ids"] == ["C-1"]


def test_huge_integer_time_is_rejected_without_raising():
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "R-1"): 1, ("R-1", "D-1"): 1}

    result = estimate_eta(order, partner, travel, now=10**10000)

    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_malformed_assignment_and_travel_inputs_are_safe():
    unassigned = assign_order(None, [None, "not-a-partner", {}], None)
    estimate = estimate_eta(
        new_order("O-1", "R-1", "D-1"),
        new_partner("P-1", "ZONE-A"),
        "not-a-travel-mapping",
    )

    assert unassigned["partner_id"] is None
    assert unassigned["eta_minutes"] is None
    assert estimate["eligible"] is False
    assert estimate["eta_minutes"] is None


def test_expanded_dataset_routes_work_with_service_tuple_keys():
    repo_root = Path(__file__).resolve().parents[1]
    dataset = json.loads(
        (repo_root / "data" / "records.json").read_text(encoding="utf-8")
    )
    travel = {
        (record["from"], record["to"]): record["minutes"]
        for record in dataset["travel_times"]
    }

    eligible_pair = None
    for order in dataset["orders"]:
        for partner in dataset["partners"]:
            capacity = partner.get("capacity")
            active_orders = partner.get("active_order_ids")
            if (
                partner.get("active") is not True
                or type(capacity) is not int
                or capacity <= 0
                or not isinstance(active_orders, list)
                or len(active_orders) >= capacity
            ):
                continue

            pickup_route = (partner.get("zone"), order.get("restaurant_id"))
            delivery_route = (
                order.get("restaurant_id"),
                order.get("destination_zone"),
            )
            if pickup_route in travel and delivery_route in travel:
                eligible_pair = (order, partner, pickup_route, delivery_route)
                break
        if eligible_pair is not None:
            break

    assert eligible_pair is not None, "Dataset should contain a complete eligible route"
    order, partner, pickup_route, delivery_route = eligible_pair

    result = assign_order(order, [partner], travel)

    expected_pickup = (
        travel[pickup_route] + partner.get("workload_minutes", 0)
    )
    expected_eta = (
        expected_pickup
        + order["prep_minutes"]
        + travel[delivery_route]
    )
    assert result["partner_id"] == partner["partner_id"]
    assert result["pickup_minutes"] == expected_pickup
    assert result["eta_minutes"] == expected_eta
