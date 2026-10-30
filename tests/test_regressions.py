"""Regression tests for the SmartDispatch dispatch-logic fixes.

These tests lock in the root-cause fixes made to service.py:
  * estimate_eta rejects invalid/missing now, preparation and travel times
    (negative, non-numeric, boolean, NaN, infinity) instead of computing or
    crashing.
  * assign_order only considers active partners below capacity and rejects
    malformed order fields.
  * process_cancellation is idempotent: a duplicate event_id never releases
    workload/capacity twice.

The synthetic dataset in data/records.json is also exercised to confirm the
service handles the real (deliberately incomplete) travel data without crashing.
"""
import json

import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def _load_dataset():
    with open('data/records.json', encoding='utf-8') as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# estimate_eta: invalid time inputs are never treated as zero or valid
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("now", [-1, -10, "5", True, None, float("nan"), float("inf")])
def test_estimate_eta_rejects_invalid_now(now):
    result = estimate_eta(
        new_order("O", "R", "D"),
        new_partner("P", "Z"),
        {("Z", "R"): 1, ("R", "D"): 1},
        now=now,
    )
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("leg1,leg2", [
    (-1, 1), (1, -1), (-1, -1),
    ("2", 1), (1, "2"),
    (True, 1), (1, False),
    (float("nan"), 1), (1, float("inf")),
])
def test_estimate_eta_rejects_invalid_travel_times(leg1, leg2):
    travel = {}
    if leg1 is not None:
        travel[("Z", "R")] = leg1
    if leg2 is not None:
        travel[("R", "D")] = leg2
    result = estimate_eta(new_order("O", "R", "D"), new_partner("P", "Z"), travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("prep", [-1, -5, None, "2", True, float("nan"), float("inf")])
def test_estimate_eta_rejects_invalid_prep_time(prep):
    result = estimate_eta(
        new_order("O", "R", "D", prep),
        new_partner("P", "Z"),
        {("Z", "R"): 2, ("R", "D"): 3},
    )
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


# ---------------------------------------------------------------------------
# assign_order: eligibility, capacity and malformed orders
# ---------------------------------------------------------------------------

def test_assign_order_skips_inactive_partner():
    order = new_order("O", "R", "D")
    partner = new_partner("P", "Z")
    partner["active"] = False
    assert assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})["partner_id"] is None


def test_assign_order_skips_full_capacity_partner():
    order = new_order("O", "R", "D")
    partner = new_partner("P", "Z", 1)
    partner["active_order_ids"] = ["EXISTING"]
    assert assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})["partner_id"] is None


def test_assign_order_rejects_invalid_capacity():
    order = new_order("O", "R", "D")
    partner = new_partner("P", "Z", 2)
    partner["capacity"] = 0  # invalid capacity
    assert assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})["partner_id"] is None


@pytest.mark.parametrize("field,value", [
    ("order_id", ""), ("order_id", None), ("order_id", 0),
    ("restaurant_id", ""), ("restaurant_id", None),
    ("destination_zone", ""), ("destination_zone", None),
])
def test_assign_order_rejects_malformed_order_identifiers(field, value):
    order = new_order("O", "R", "D")
    order[field] = value
    assert assign_order(order, [new_partner("P", "Z")], {("Z", "R"): 1, ("R", "D"): 1})["partner_id"] is None


def test_assign_order_breaks_eta_ties_by_partner_id_ascending():
    order = new_order("O", "R", "D", 0)
    partners = [new_partner(pid, "Z") for pid in ("P9", "P0", "P5")]
    result = assign_order(order, partners, {("Z", "R"): 1, ("R", "D"): 1})
    assert result["partner_id"] == "P0"


# ---------------------------------------------------------------------------
# process_cancellation: idempotency and safe workload accounting
# ---------------------------------------------------------------------------

def test_duplicate_cancellation_does_not_release_twice():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["O1"], workload_minutes=18, minutes_by_order={"O1": 18})
    first = process_cancellation(partner, "O1", "C1")
    second = process_cancellation(first, "O1", "C1")
    assert second["workload_minutes"] == 0
    assert second["active_order_ids"] == []
    assert second["processed_cancellation_ids"] == ["C1"]


def test_cancellation_of_unknown_order_releases_nothing():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["ACTIVE"], workload_minutes=20, minutes_by_order={"ACTIVE": 20})
    result = process_cancellation(partner, "UNKNOWN", "C1")
    assert result["workload_minutes"] == 20
    assert result["active_order_ids"] == ["ACTIVE"]


# ---------------------------------------------------------------------------
# Synthetic dataset: service must not crash on the real incomplete data
# ---------------------------------------------------------------------------

def test_dataset_travel_conversion_and_dispatch_is_safe():
    data = _load_dataset()
    travel = {
        (row["from"], row["to"]): row["minutes"]
        for row in data["travel_times"]
    }
    partners = data["partners"]
    orders = data["orders"]

    results = []
    for order in orders[:25]:  # bounded sample for a fast, deterministic check
        result = assign_order(order, partners, travel, now=0)
        results.append(result)
        assert "partner_id" in result and "eta_minutes" in result and "reason" in result
        if result["partner_id"] is not None:
            assert result["eta_minutes"] is not None
            assert result["reason"] == "assigned"
        else:
            assert result["reason"]  # unassigned orders always carry a reason

    # Determinism: running again yields identical results.
    results_again = [assign_order(o, partners, travel, now=0) for o in orders[:25]]
    assert results == results_again
