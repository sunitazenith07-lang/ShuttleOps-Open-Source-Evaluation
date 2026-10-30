"""Regression tests for cancellation idempotency and malformed state."""

from models import new_partner
from service import process_cancellation


def test_reused_event_id_with_different_order_payload_is_ignored():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1", "O2"],
        workload_minutes=15,
        minutes_by_order={"O1": 5, "O2": 10},
    )

    once = process_cancellation(partner, "O1", "C-1")
    replayed_with_different_order = process_cancellation(once, "O2", "C-1")

    assert replayed_with_different_order["active_order_ids"] == ["O2"]
    assert replayed_with_different_order["workload_minutes"] == 10
    assert replayed_with_different_order["processed_cancellation_ids"] == ["C-1"]


def test_unknown_order_event_is_recorded_once_and_replay_is_ignored():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["O1"], workload_minutes=7)

    once = process_cancellation(partner, "UNKNOWN", "C-2")
    replayed = process_cancellation(once, "O1", "C-2")

    assert replayed["active_order_ids"] == ["O1"]
    assert replayed["workload_minutes"] == 7
    assert replayed["processed_cancellation_ids"] == ["C-2"]


def test_invalid_event_id_is_a_safe_no_op():
    partner = new_partner("P", "Z")
    partner.update(active_order_ids=["O1"], workload_minutes=7)

    result = process_cancellation(partner, "O1", " ")

    assert result["active_order_ids"] == ["O1"]
    assert result["workload_minutes"] == 7
    assert result["processed_cancellation_ids"] == []


def test_invalid_workload_values_do_not_produce_negative_or_invalid_workload():
    partner = new_partner("P", "Z")
    partner.update(
        active_order_ids=["O1"],
        workload_minutes=-3,
        minutes_by_order={"O1": 8},
    )

    result = process_cancellation(partner, "O1", "C-3")

    assert result["active_order_ids"] == []
    assert result["workload_minutes"] == 0
    assert result["processed_cancellation_ids"] == ["C-3"]


def test_non_dictionary_partner_is_returned_without_crashing():
    assert process_cancellation(None, "O1", "C-4") is None
