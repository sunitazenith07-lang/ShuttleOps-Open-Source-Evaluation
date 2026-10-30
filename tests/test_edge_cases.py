"""Additional deterministic ETA formula checks across boundary values.

These cases are not tied to the example fixtures. They verify the stated ETA
formula across zeros, typical values, high workload and larger time estimates.
"""
import pytest
from models import new_order, new_partner
from service import estimate_eta


@pytest.mark.parametrize("leg1,workload,prep,leg2,now", [
    (0, 0, 0, 0, 0),
    (1, 0, 0, 1, 0),
    (1, 2, 3, 4, 5),
    (8, 5, 10, 12, 0),
    (12, 2, 10, 4, 3),
    (3, 7, 5, 9, 10),
    (20, 0, 10, 20, 0),
    (4, 4, 4, 4, 4),
    (2, 1, 1, 2, 1),
    (9, 9, 9, 9, 9),
    (60, 30, 10, 15, 5),
    (100, 0, 0, 100, 0),
    (0, 10, 0, 0, 5),
    (10, 0, 10, 0, 0),
    (0, 0, 10, 10, 0),
    (7, 3, 6, 4, 2),
    (6, 4, 5, 3, 1),
    (2, 5, 8, 4, 3),
    (13, 11, 9, 7, 6),
    (1, 1, 1, 1, 1),
    (500, 250, 90, 750, 100),
    (999, 30, 45, 1200, 60),
    (75, 120, 0, 33, 12),
    (10000, 600, 180, 5000, 360),
    (12, 0, 0, 19, 1000),
    (0, 999, 1, 0, 1),
    (35, 25, 45, 90, 15),
    (15, 60, 30, 40, 90)
])
def test_eta_formula_for_expanded_scenario_matrix(leg1, workload, prep, leg2, now):
    order = new_order("DATASET-ORDER", "REST-101", "DEST-01", prep)
    partner = new_partner("PARTNER-001", "ZONE-A")
    partner["workload_minutes"] = workload
    travel = {
        ("ZONE-A", "REST-101"): leg1,
        ("REST-101", "DEST-01"): leg2,
    }
    result = estimate_eta(order, partner, travel, now=now)
    expected_pickup = now + leg1 + workload
    expected_eta = expected_pickup + prep + leg2
    assert result["eligible"] is True
    assert result["pickup_minutes"] == expected_pickup
    assert result["eta_minutes"] == expected_eta


@pytest.mark.parametrize("travel", [
    {},
    {("ZONE-A", "REST-101"): 10},
    {("REST-101", "DEST-01"): 10},
])
def test_eta_is_ineligible_when_either_required_route_is_missing(travel):
    order = new_order("MISSING-ROUTE", "REST-101", "DEST-01", 10)
    partner = new_partner("PARTNER-001", "ZONE-A")
    result = estimate_eta(order, partner, travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_eta_rejects_invalid_workload_without_arithmetic_error():
    order = new_order("INVALID-WORKLOAD", "REST-101", "DEST-01")
    partner = new_partner("PARTNER-001", "ZONE-A")
    partner["workload_minutes"] = float("nan")
    result = estimate_eta(order, partner, {("ZONE-A", "REST-101"): 1, ("REST-101", "DEST-01"): 1})
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_eta_accepts_large_integer_time_values():
    order = new_order("LARGE-TIME", "REST-101", "DEST-01", prep_minutes=10**400)
    partner = new_partner("PARTNER-001", "ZONE-A")
    result = estimate_eta(order, partner, {("ZONE-A", "REST-101"): 10**400, ("REST-101", "DEST-01"): 10**400})
    assert result["eligible"] is True
    assert result["eta_minutes"] == 3 * 10**400
