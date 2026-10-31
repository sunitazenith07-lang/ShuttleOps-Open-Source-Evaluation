"""Regression tests for Phase 4: ETA Validation and Cancellation Handling."""
import pytest
from models import new_order, new_partner
from service import estimate_eta, process_cancellation, assign_order


# --- Task A: Travel Time Validation ---

@pytest.mark.parametrize("leg1,leg2", [
    (None, 5),
    (5, None),
    (None, None),
    (-1, 5),
    (5, -1),
    (-5, -5),
    ("10", 5),
    (5, "10"),
    (True, 5),
    (5, False),
    (float("nan"), 5),
    (5, float("inf")),
    (float("-inf"), 5),
])
def test_travel_time_validation_rejects_invalid_legs(leg1, leg2):
    """estimate_eta must mark candidate ineligible for any invalid/missing travel legs."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    travel = {}
    if leg1 is not None:
        travel[("ZONE-A", "REST-1")] = leg1
    if leg2 is not None:
        travel[("REST-1", "DEST-1")] = leg2
    result = estimate_eta(order, partner, travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


# --- Task B: Preparation Time Validation in estimate_eta ---

@pytest.mark.parametrize("prep", [
    -1,
    -5,
    -100,
    None,
    "10",
    True,
    False,
    float("inf"),
    float("-inf"),
    float("nan"),
])
def test_estimate_eta_rejects_invalid_prep_minutes(prep):
    """estimate_eta must mark candidate ineligible if prep_minutes is invalid."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=prep)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = estimate_eta(order, partner, travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("prep", [0, 0.0, 1, 1.5, 5, 10, 60])
def test_estimate_eta_accepts_valid_prep_minutes(prep):
    """estimate_eta must accept non-negative finite numeric prep_minutes."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=prep)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = estimate_eta(order, partner, travel)
    assert result["eligible"] is True
    assert result["eta_minutes"] == 5 + prep + 10


# --- Task C: Current Time (now) Validation in estimate_eta ---

@pytest.mark.parametrize("now", [
    -1,
    -10,
    -0.5,
    "5",
    "0",
    "",
    True,
    False,
    None,
    float("inf"),
    float("-inf"),
    float("nan"),
])
def test_estimate_eta_rejects_invalid_now(now):
    """estimate_eta must mark candidate ineligible if now is invalid."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = estimate_eta(order, partner, travel, now=now)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("now", [0, 0.0, 1, 5, 10, 60, 100, 1000])
def test_estimate_eta_accepts_valid_now(now):
    """estimate_eta must accept non-negative finite numeric now."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = estimate_eta(order, partner, travel, now=now)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == now + 5
    assert result["eta_minutes"] == now + 5 + 10 + 10


# --- Task D: Duplicate Cancellation Idempotency in process_cancellation ---

def test_duplicate_cancellation_same_event_id_is_idempotent():
    """Applying the same event_id multiple times must only mutate state once."""
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1", "ORD-2"],
        workload_minutes=30,
        minutes_by_order={"ORD-1": 10, "ORD-2": 20},
    )
    once = process_cancellation(partner, "ORD-1", "EVT-001")
    assert once["active_order_ids"] == ["ORD-2"]
    assert once["workload_minutes"] == 20
    assert once["processed_cancellation_ids"] == ["EVT-001"]

    twice = process_cancellation(once, "ORD-1", "EVT-001")
    assert twice["active_order_ids"] == ["ORD-2"]
    assert twice["workload_minutes"] == 20
    assert twice["processed_cancellation_ids"] == ["EVT-001"]

    thrice = process_cancellation(twice, "ORD-1", "EVT-001")
    assert thrice["active_order_ids"] == ["ORD-2"]
    assert thrice["workload_minutes"] == 20
    assert thrice["processed_cancellation_ids"] == ["EVT-001"]


def test_different_cancellation_events_processed_independently():
    """Different event IDs for different orders must both be processed."""
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1", "ORD-2"],
        workload_minutes=30,
        minutes_by_order={"ORD-1": 10, "ORD-2": 20},
    )
    first = process_cancellation(partner, "ORD-1", "EVT-001")
    second = process_cancellation(first, "ORD-2", "EVT-002")
    assert second["active_order_ids"] == []
    assert second["workload_minutes"] == 0
    assert second["processed_cancellation_ids"] == ["EVT-001", "EVT-002"]


def test_duplicate_cancellation_does_not_release_workload_twice():
    """Duplicate event must not reduce workload below post-first-cancellation level."""
    partner = new_partner("P-1", "ZONE-A")
    partner.update(
        active_order_ids=["ORD-1"],
        workload_minutes=15,
        minutes_by_order={"ORD-1": 15},
    )
    first = process_cancellation(partner, "ORD-1", "EVT-100")
    assert first["workload_minutes"] == 0
    second = process_cancellation(first, "ORD-1", "EVT-100")
    assert second["workload_minutes"] == 0
    assert second["processed_cancellation_ids"] == ["EVT-100"]


# --- Extremely Large Integer Validation (OverflowError Protection) ---

def test_large_integer_does_not_raise_overflow_error():
    """Validating extremely large integers (> 10**308) must not raise OverflowError."""
    large_int = 10**400
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=large_int)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): large_int, ("REST-1", "DEST-1"): large_int}
    result = estimate_eta(order, partner, travel, now=large_int)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == large_int * 2
    assert result["eta_minutes"] == large_int * 4


# --- Partner Workload Validation in estimate_eta ---

@pytest.mark.parametrize("workload", [
    None,
    -1,
    -10,
    True,
    False,
    "15",
    float("nan"),
    float("inf"),
    float("-inf"),
])
def test_estimate_eta_rejects_invalid_partner_workload(workload):
    """estimate_eta must mark candidate ineligible for invalid partner workload."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = {"partner_id": "P-1", "zone": "ZONE-A", "workload_minutes": workload}
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 15}
    result = estimate_eta(order, partner, travel, now=0)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None
    assert result["partner_id"] == "P-1"


def test_estimate_eta_missing_workload_defaults_to_zero():
    """Missing workload key in partner dictionary defaults to 0 and computes valid ETA."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = {"partner_id": "P-1", "zone": "ZONE-A"}  # No workload_minutes key
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 15}
    result = estimate_eta(order, partner, travel, now=2)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == 2 + 5 + 0  # now + leg1 + 0
    assert result["eta_minutes"] == 7 + 10 + 15    # pickup + prep + leg2


def test_estimate_eta_valid_workload_calculates_correctly():
    """Valid non-negative integer and float workload calculate pickup and ETA correctly."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 15}

    # Integer workload
    partner_int = {"partner_id": "P-1", "zone": "ZONE-A", "workload_minutes": 12}
    res_int = estimate_eta(order, partner_int, travel, now=3)
    assert res_int["eligible"] is True
    assert res_int["pickup_minutes"] == 3 + 5 + 12  # 20
    assert res_int["eta_minutes"] == 20 + 10 + 15    # 45

    # Float workload
    partner_float = {"partner_id": "P-2", "zone": "ZONE-A", "workload_minutes": 4.5}
    res_float = estimate_eta(order, partner_float, travel, now=1)
    assert res_float["eligible"] is True
    assert res_float["pickup_minutes"] == 1 + 5 + 4.5  # 10.5
    assert res_float["eta_minutes"] == 10.5 + 10 + 15    # 35.5


# ===========================================================================
# PHASE 5 CORRECTION REGRESSIONS
# Issues 1–5: Malformed fields, overflow, invalid IDs, invalid event IDs
# ===========================================================================


# --- Issue 1: Malformed active_order_ids in assign_order ---

def test_assign_order_active_order_ids_none_skips_partner():
    """Partner with active_order_ids=None must be skipped (treated ineligible)."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = None
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None
    assert result["reason"] == "no eligible partner or missing time data"


def test_assign_order_active_order_ids_string_skips_partner():
    """Partner with active_order_ids as a string must be skipped."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = "not-a-list"
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_assign_order_active_order_ids_empty_list_is_eligible():
    """Partner with active_order_ids=[] (empty, valid) should be eligible if other criteria met."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = []
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] == "P-1"


def test_assign_order_active_order_ids_at_capacity_skips_partner():
    """Partner with active_order_ids at capacity must be skipped."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1", capacity=2)
    partner["active_order_ids"] = ["A", "B"]
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_assign_order_active_order_ids_below_capacity_is_eligible():
    """Partner with active_order_ids below capacity should be eligible."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1", capacity=3)
    partner["active_order_ids"] = ["A"]
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] == "P-1"


def test_assign_order_active_order_ids_list_with_mixed_ids_is_valid():
    """A list containing arbitrary (even malformed) string IDs is still a structurally valid list."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1", capacity=5)
    partner["active_order_ids"] = [None, 123, "valid-id"]  # structurally a list
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    # The list has 3 items, capacity=5, so partner is below capacity and eligible
    assert result["partner_id"] == "P-1"


# --- Issue 2: Malformed cancellation records in process_cancellation ---

def test_process_cancellation_workload_none_no_type_error():
    """workload_minutes=None must not raise TypeError; state handled safely."""
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = ["ORD-1"]
    partner["workload_minutes"] = None
    partner["minutes_by_order"] = {"ORD-1": 10}
    result = process_cancellation(partner, "ORD-1", "EVT-1")
    # Should not raise; workload_minutes treated as 0, result is max(0, 0-10) = 0
    assert result["workload_minutes"] == 0
    assert "ORD-1" not in result["active_order_ids"]
    assert "EVT-1" in result["processed_cancellation_ids"]


def test_process_cancellation_active_order_ids_none_no_attribute_error():
    """active_order_ids=None must not raise AttributeError; mutation skipped safely."""
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = None
    partner["workload_minutes"] = 20
    result = process_cancellation(partner, "ORD-1", "EVT-2")
    # Should not raise; mutation skipped, event still recorded
    assert "EVT-2" in result["processed_cancellation_ids"]
    # active_order_ids remains None (no mutation attempted)
    assert result.get("active_order_ids") is None


def test_process_cancellation_minutes_by_order_none_releases_zero():
    """minutes_by_order=None must not raise AttributeError; released minutes default to 0."""
    partner = new_partner("P-1", "Z-1")
    partner["active_order_ids"] = ["ORD-1"]
    partner["workload_minutes"] = 15
    partner["minutes_by_order"] = None
    result = process_cancellation(partner, "ORD-1", "EVT-3")
    # Released minutes = 0; workload stays at 15 (max(0, 15-0))
    assert result["workload_minutes"] == 15
    assert "ORD-1" not in result["active_order_ids"]
    assert "EVT-3" in result["processed_cancellation_ids"]


def test_process_cancellation_valid_record_correct():
    """Valid cancellation correctly removes order and releases workload."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-A", "ORD-B"], workload_minutes=25,
                   minutes_by_order={"ORD-A": 10, "ORD-B": 15})
    result = process_cancellation(partner, "ORD-A", "EVT-10")
    assert result["workload_minutes"] == 15
    assert "ORD-A" not in result["active_order_ids"]
    assert "ORD-B" in result["active_order_ids"]
    assert result["processed_cancellation_ids"] == ["EVT-10"]


# --- Issue 3: Missing or invalid partner IDs in assign_order ---

def test_assign_order_partner_id_none_not_assigned():
    """Partner with partner_id=None must not be assigned."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["partner_id"] = None
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_assign_order_partner_id_empty_string_not_assigned():
    """Partner with partner_id="" must not be assigned."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["partner_id"] = ""
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_assign_order_partner_id_whitespace_not_assigned():
    """Partner with partner_id="  " (whitespace) must not be assigned."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-1", "Z-1")
    partner["partner_id"] = "   "
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_assign_order_valid_partner_id_assigned():
    """Partner with a valid partner_id is correctly assigned."""
    order = new_order("O-1", "R-1", "D-1")
    partner = new_partner("P-VALID", "Z-1")
    travel = {("Z-1", "R-1"): 5, ("R-1", "D-1"): 5}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] == "P-VALID"
    assert result["reason"] == "assigned"


# --- Issue 4: Arithmetic overflow in estimate_eta ---

def test_estimate_eta_large_int_plus_float_no_overflow_error():
    """Very large int now + float leg1 must not raise OverflowError; returns ineligible if not finite."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    large_int = 10 ** 400
    # leg1 is a float (finite), now is a huge int; pickup = large_int + 1.0 + 0 overflows to inf
    travel = {("ZONE-A", "REST-1"): 1.0, ("REST-1", "DEST-1"): 1.0}
    # Should not raise OverflowError; result is ineligible because pickup/eta overflow to inf
    result = estimate_eta(order, partner, travel, now=large_int)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_estimate_eta_very_large_float_overflow_ineligible():
    """Very large float values that overflow must return ineligible."""
    import sys
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    # Use float max; adding two float-max values produces inf
    max_float = sys.float_info.max
    travel = {("ZONE-A", "REST-1"): max_float, ("REST-1", "DEST-1"): max_float}
    result = estimate_eta(order, partner, travel, now=0)
    # pickup = 0 + max_float + 0 = max_float (finite), but eta = max_float + 10 + max_float = inf
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_estimate_eta_normal_int_arithmetic_eligible():
    """Normal integer arithmetic must still yield a valid eligible result."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=10)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = estimate_eta(order, partner, travel, now=2)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == 7
    assert result["eta_minutes"] == 27


def test_estimate_eta_normal_float_arithmetic_eligible():
    """Normal float arithmetic must still yield a valid eligible result."""
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=5.5)
    partner = new_partner("P-1", "ZONE-A")
    partner["workload_minutes"] = 2.5
    travel = {("ZONE-A", "REST-1"): 3.0, ("REST-1", "DEST-1"): 4.0}
    result = estimate_eta(order, partner, travel, now=1.0)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == 1.0 + 3.0 + 2.5  # 6.5
    assert result["eta_minutes"] == 6.5 + 5.5 + 4.0    # 16.0


def test_large_integer_only_still_passes():
    """Existing large-int-only test (10**400 with all-int inputs) must still pass."""
    large_int = 10 ** 400
    order = new_order("O-1", "REST-1", "DEST-1", prep_minutes=large_int)
    partner = new_partner("P-1", "ZONE-A")
    travel = {("ZONE-A", "REST-1"): large_int, ("REST-1", "DEST-1"): large_int}
    result = estimate_eta(order, partner, travel, now=large_int)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == large_int * 2
    assert result["eta_minutes"] == large_int * 4


# --- Issue 5: Invalid cancellation event IDs ---

def test_process_cancellation_event_id_none_no_mutation():
    """event_id=None must not mutate partner state; return dict unchanged."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-1"], workload_minutes=10,
                   minutes_by_order={"ORD-1": 10})
    result = process_cancellation(partner, "ORD-1", None)
    # No mutation: order still active, workload unchanged, no event recorded
    assert "ORD-1" in result["active_order_ids"]
    assert result["workload_minutes"] == 10
    assert result["processed_cancellation_ids"] == []


def test_process_cancellation_event_id_empty_string_no_mutation():
    """event_id="" must not mutate partner state."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-1"], workload_minutes=10,
                   minutes_by_order={"ORD-1": 10})
    result = process_cancellation(partner, "ORD-1", "")
    assert "ORD-1" in result["active_order_ids"]
    assert result["workload_minutes"] == 10
    assert result["processed_cancellation_ids"] == []


def test_process_cancellation_event_id_whitespace_no_mutation():
    """event_id="  " (whitespace only) must not mutate partner state."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-1"], workload_minutes=10,
                   minutes_by_order={"ORD-1": 10})
    result = process_cancellation(partner, "ORD-1", "   ")
    assert "ORD-1" in result["active_order_ids"]
    assert result["workload_minutes"] == 10
    assert result["processed_cancellation_ids"] == []


def test_process_cancellation_duplicate_valid_event_id_idempotent():
    """Duplicate valid event ID must be idempotent (processed once only)."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-1"], workload_minutes=10,
                   minutes_by_order={"ORD-1": 10})
    once = process_cancellation(partner, "ORD-1", "EVT-DUP")
    twice = process_cancellation(once, "ORD-1", "EVT-DUP")
    assert twice["workload_minutes"] == 0
    assert "ORD-1" not in twice["active_order_ids"]
    assert twice["processed_cancellation_ids"] == ["EVT-DUP"]


def test_process_cancellation_two_distinct_valid_event_ids_both_processed():
    """Two distinct valid event IDs must both be processed independently."""
    partner = new_partner("P-1", "Z-1")
    partner.update(active_order_ids=["ORD-1", "ORD-2"], workload_minutes=20,
                   minutes_by_order={"ORD-1": 8, "ORD-2": 12})
    first = process_cancellation(partner, "ORD-1", "EVT-A")
    second = process_cancellation(first, "ORD-2", "EVT-B")
    assert second["active_order_ids"] == []
    assert second["workload_minutes"] == 0
    assert second["processed_cancellation_ids"] == ["EVT-A", "EVT-B"]

