
"""Regression tests for edge cases discovered while fixing dispatch logic."""

import pytest

from models import new_order, new_partner
from service import estimate_eta, process_cancellation


# 1. Invalid workload values must make a partner ineligible.
@pytest.mark.parametrize("workload", [
    -1,
    True,
    float("nan"),
    float("inf")
])
def test_invalid_partner_workload_makes_eta_ineligible(workload):
    order = new_order("O-1", "R-1", "D-1", prep_minutes=5)
    partner = new_partner("P-1", "Z-1")
    partner["workload_minutes"] = workload

    travel = {
        ("Z-1", "R-1"): 4,
        ("R-1", "D-1"): 6
    }

    result = estimate_eta(order, partner, travel)

    assert result["eligible"] is False
    assert result["eta_minutes"] is None


# 2. Non-finite current time must be rejected.
@pytest.mark.parametrize("now", [
    float("nan"),
    float("inf"),
    float("-inf")
])
def test_non_finite_current_time_makes_eta_ineligible(now):
    order = new_order("O-1", "R-1", "D-1", prep_minutes=5)
    partner = new_partner("P-1", "Z-1")

    travel = {
        ("Z-1", "R-1"): 4,
        ("R-1", "D-1"): 6
    }

    result = estimate_eta(order, partner, travel, now=now)

    assert result["eligible"] is False
    assert result["eta_minutes"] is None


# 3. Required order fields containing only spaces must be rejected.
@pytest.mark.parametrize("field", [
    "order_id",
    "restaurant_id",
    "destination_zone"
])
def test_whitespace_only_required_order_fields_are_rejected(field):
    order = new_order("O-1", "R-1", "D-1", prep_minutes=5)
    order[field] = "   "

    partner = new_partner("P-1", "Z-1")

    travel = {
        ("Z-1", "R-1"): 4,
        ("R-1", "D-1"): 6
    }

    result = estimate_eta(order, partner, travel)

    assert result["eligible"] is False
    assert result["eta_minutes"] is None


# 4. Cancellation must not modify the original partner dictionary.
def test_cancellation_does_not_mutate_original_partner():
    partner = new_partner("P-1", "Z-1")

    partner.update(
        active_order_ids=["O-1"],
        workload_minutes=12,
        minutes_by_order={"O-1": 12},
        processed_cancellation_ids=[]
    )

    original = {
        **partner,
        "active_order_ids": partner["active_order_ids"].copy(),
        "minutes_by_order": partner["minutes_by_order"].copy(),
        "processed_cancellation_ids":
            partner["processed_cancellation_ids"].copy()
    }

    result = process_cancellation(partner, "O-1", "C-1")

    assert result["active_order_ids"] == []
    assert result["workload_minutes"] == 0
    assert partner == original


# 5. A duplicate cancellation ID must not cancel another order.
def test_duplicate_cancellation_id_does_not_cancel_a_different_order():
    partner = new_partner("P-1", "Z-1")

    partner.update(
        active_order_ids=["O-1", "O-2"],
        workload_minutes=19,
        minutes_by_order={"O-1": 8, "O-2": 11},
        processed_cancellation_ids=["C-1"]
    )

    result = process_cancellation(partner, "O-2", "C-1")

    assert result["active_order_ids"] == ["O-1", "O-2"]
    assert result["workload_minutes"] == 19
    assert result["minutes_by_order"] == {
        "O-1": 8,
        "O-2": 11
    }
    assert result["processed_cancellation_ids"] == ["C-1"]
