"""Regression tests for defects fixed in service.py, plus invariants checked on data/records.json."""
import json
import random
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import pytest
from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation

DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "records.json").read_text())
TRAVEL = {(row["from"], row["to"]): row["minutes"] for row in DATA["travel_times"]}
ROUTE = {("Z", "R"): 1, ("R", "D"): 1}


# --- input validation -------------------------------------------------------

@pytest.mark.parametrize("now", [float("nan"), float("inf"), -0.5, [], "0"])
def test_non_finite_or_non_numeric_now_rejected(now):
    assert estimate_eta(new_order("O", "R", "D"), new_partner("P", "Z"), ROUTE, now)["eligible"] is False
    assert assign_order(new_order("O", "R", "D"), [new_partner("P", "Z")], ROUTE, now)["partner_id"] is None


@pytest.mark.parametrize("workload", [-1, None, "5", True, float("nan"), float("inf")])
def test_invalid_partner_workload_is_not_treated_as_zero(workload):
    partner = new_partner("P", "Z")
    partner["workload_minutes"] = workload
    result = estimate_eta(new_order("O", "R", "D"), partner, ROUTE)
    assert result["eligible"] is False and result["eta_minutes"] is None


def test_missing_order_field_is_rejected_with_reason():
    order = new_order("O", "R", "D")
    del order["restaurant_id"]
    result = assign_order(order, [new_partner("P", "Z")], ROUTE)
    assert result["partner_id"] is None
    assert "restaurant_id" in result["reason"]


@pytest.mark.parametrize("travel", [None, [], "routes"])
def test_non_mapping_travel_data_is_safe(travel):
    result = assign_order(new_order("O", "R", "D"), [new_partner("P", "Z")], travel)
    assert result["partner_id"] is None and result["eta_minutes"] is None


def test_float_travel_and_prep_are_accepted():
    result = estimate_eta(new_order("O", "R", "D", 1.5), new_partner("P", "Z"), {("Z", "R"): 2.5, ("R", "D"): 3})
    assert result["eligible"] is True and result["eta_minutes"] == 7.0


# --- partner eligibility / malformed records --------------------------------

@pytest.mark.parametrize("partners", [None, [], (), "P", {}])
def test_empty_or_non_list_partners_leave_order_unassigned(partners):
    result = assign_order(new_order("O", "R", "D"), partners, ROUTE)
    assert result["partner_id"] is None and result["reason"]


def test_malformed_partner_records_are_skipped_not_fatal():
    good = new_partner("GOOD", "Z")
    no_id = new_partner("", "Z")
    no_zone = new_partner("NOZONE", None)
    bad_orders = new_partner("BADLIST", "Z")
    bad_orders["active_order_ids"] = "O1"
    result = assign_order(new_order("O", "R", "D"), [None, 42, no_id, no_zone, bad_orders, good], ROUTE)
    assert result["partner_id"] == "GOOD"
    assert len(result["rejected"]) == 5


def test_truthy_non_bool_active_flag_is_not_treated_as_active():
    partner = new_partner("P", "Z")
    partner["active"] = "yes"
    assert assign_order(new_order("O", "R", "D"), [partner], ROUTE)["partner_id"] is None


def test_unassigned_result_explains_each_rejection():
    inactive = new_partner("A", "Z")
    inactive["active"] = False
    full = new_partner("B", "Z", capacity=1)
    full["active_order_ids"] = ["X"]
    no_route = new_partner("C", "FAR")
    result = assign_order(new_order("O", "R", "D"), [inactive, full, no_route], ROUTE)
    assert result["partner_id"] is None and result["eta_minutes"] is None
    assert {r["partner_id"]: r["reason"] for r in result["rejected"]} == {
        "A": "partner is not active",
        "B": "partner at capacity",
        "C": "missing travel-time data",
    }


def test_ineligible_faster_partner_does_not_win():
    fast_but_full = new_partner("A", "NEAR", capacity=1)
    fast_but_full["active_order_ids"] = ["X"]
    slow = new_partner("B", "FARTHER")
    travel = {("NEAR", "R"): 1, ("FARTHER", "R"): 30, ("R", "D"): 5}
    result = assign_order(new_order("O", "R", "D", 0), [fast_but_full, slow], travel)
    assert result["partner_id"] == "B" and result["eta_minutes"] == 35


def test_tie_break_is_lexicographic_not_numeric():
    partners = [new_partner(pid, "Z") for pid in ["P10", "P9", "P2"]]
    assert assign_order(new_order("O", "R", "D"), partners, ROUTE)["partner_id"] == "P10"


def test_assign_order_does_not_mutate_inputs():
    order, partners = new_order("O", "R", "D"), [new_partner("A", "Z"), new_partner("B", "Z")]
    before = deepcopy((order, partners, ROUTE))
    assign_order(order, partners, ROUTE)
    assert (order, partners, ROUTE) == before


# --- cancellation -----------------------------------------------------------

def _loaded_partner():
    partner = new_partner("P", "Z", capacity=2)
    partner.update(active_order_ids=["O1", "O2"], workload_minutes=25, minutes_by_order={"O1": 10, "O2": 15})
    return partner


def test_reused_event_id_with_different_payload_is_ignored():
    once = process_cancellation(_loaded_partner(), "O1", "C1")
    again = process_cancellation(once, "O2", "C1")
    assert again["active_order_ids"] == ["O2"]
    assert again["workload_minutes"] == 15
    assert again["processed_cancellation_ids"] == ["C1"]


@pytest.mark.parametrize("event_id", [None, ""])
def test_cancellation_without_event_id_is_not_applied(event_id):
    result = process_cancellation(_loaded_partner(), "O1", event_id)
    assert result["active_order_ids"] == ["O1", "O2"]
    assert result["workload_minutes"] == 25
    assert result["processed_cancellation_ids"] == []


def test_cancellation_frees_capacity_and_drops_order_minutes():
    partner = _loaded_partner()
    order = new_order("NEW", "R", "D")
    assert assign_order(order, [partner], ROUTE)["partner_id"] is None
    freed = process_cancellation(partner, "O1", "C1")
    assert "O1" not in freed["minutes_by_order"]
    assert assign_order(order, [freed], ROUTE)["partner_id"] == "P"


def test_cancellation_returns_copy_and_rejects_non_mapping():
    partner = _loaded_partner()
    process_cancellation(partner, "O1", "C1")
    assert partner == _loaded_partner()
    with pytest.raises(TypeError):
        process_cancellation(None, "O1", "C1")


# --- dataset-wide invariants ------------------------------------------------

@pytest.mark.parametrize("order", DATA["orders"], ids=lambda o: o["order_id"])
def test_dataset_assignment_respects_all_rules(order):
    result = assign_order(order, DATA["partners"], TRAVEL)
    by_id = {p["partner_id"]: p for p in DATA["partners"]}
    eligible = []
    for p in DATA["partners"]:
        leg1 = TRAVEL.get((p["zone"], order["restaurant_id"]))
        leg2 = TRAVEL.get((order["restaurant_id"], order["destination_zone"]))
        if p["active"] is True and len(p["active_order_ids"]) < p["capacity"] and None not in (leg1, leg2):
            eligible.append((leg1 + p["workload_minutes"] + order["prep_minutes"] + leg2, p["partner_id"]))
    if not eligible:
        assert result["partner_id"] is None and result["eta_minutes"] is None
        return
    best_eta, best_id = min(eligible)
    assert (result["eta_minutes"], result["partner_id"]) == (best_eta, best_id)
    assert by_id[best_id]["active"] is True


def test_dataset_assignment_is_independent_of_partner_order():
    shuffled = list(DATA["partners"])
    random.Random(7).shuffle(shuffled)
    for order in DATA["orders"]:
        a = assign_order(order, DATA["partners"], TRAVEL)
        b = assign_order(order, shuffled, TRAVEL)
        assert (a["partner_id"], a["eta_minutes"]) == (b["partner_id"], b["eta_minutes"])


def test_dataset_cancellation_stream_never_double_releases():
    partners = {p["partner_id"]: deepcopy(p) for p in DATA["partners"]}
    applied = defaultdict(set)
    for event in DATA["cancellation_events"]:
        pid = event["partner_id"]
        before = partners[pid]
        after = process_cancellation(before, event["order_id"], event.get("event_id"))
        changed = after["active_order_ids"] != before.get("active_order_ids", [])
        if changed:
            assert (pid, event["order_id"]) not in applied[pid]
            applied[pid].add((pid, event["order_id"]))
        assert after["workload_minutes"] >= 0
        assert len(after["processed_cancellation_ids"]) == len(set(after["processed_cancellation_ids"]))
        partners[pid] = after
