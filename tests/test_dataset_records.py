import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from service import assign_order, process_cancellation


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "records.json"


def load_dataset():
    with DATASET_PATH.open(encoding="utf-8") as dataset_file:
        return json.load(dataset_file)


def test_dataset_orders_are_handled_with_converted_travel_times():
    dataset = load_dataset()
    assert len(dataset["orders"]) == 180
    travel = {
        (record["from"], record["to"]): record["minutes"]
        for record in dataset["travel_times"]
    }
    partner_ids = {partner["partner_id"] for partner in dataset["partners"]}
    statuses = Counter()
    assigned = 0

    for order in dataset["orders"]:
        result = assign_order(order, dataset["partners"], travel)
        statuses[order["status"]] += 1

        assert result["order_id"] == order["order_id"]
        if order["status"] == "CANCELLED":
            assert result["partner_id"] is None
            assert result["eta_minutes"] is None
            assert result["reason"] == "order is cancelled"
            continue

        if result["partner_id"] is not None:
            assigned += 1
            assert result["partner_id"] in partner_ids
            assert result["eta_minutes"] >= 0
        else:
            assert result["eta_minutes"] is None

    assert statuses == {
        "CREATED": 60,
        "READY_FOR_ASSIGNMENT": 60,
        "CANCELLED": 60,
    }
    assert assigned == 115


def test_dataset_cancellation_events_handle_missing_and_duplicate_ids():
    dataset = load_dataset()
    assert len(dataset["cancellation_events"]) == 177
    partners = {
        partner["partner_id"]: deepcopy(partner)
        for partner in dataset["partners"]
    }
    events_without_ids = 0

    for event in dataset["cancellation_events"]:
        partner_id = event["partner_id"]
        partner = partners[partner_id]
        updated = process_cancellation(
            partner,
            event.get("order_id"),
            event.get("event_id"),
        )

        if not event.get("event_id"):
            events_without_ids += 1
            assert updated == partner
        else:
            partners[partner_id] = updated

    processed_ids = [
        event_id
        for partner in partners.values()
        for event_id in partner["processed_cancellation_ids"]
    ]
    assert events_without_ids == 7
    assert len(processed_ids) == 161
    assert len(processed_ids) == len(set(processed_ids))
    assert all(partner["workload_minutes"] >= 0 for partner in partners.values())
