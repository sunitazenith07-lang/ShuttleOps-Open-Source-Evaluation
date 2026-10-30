"""Dataset regression tests built on data/records.json.

The 387 JSON travel rows are converted into the (from, to) -> minutes tuple-key
mapping the service expects, then the full order/cancellation streams are
replayed to verify determinism, eligibility and idempotency at dataset scale.
"""
import json
from pathlib import Path

import pytest
from service import assign_order, process_cancellation

DATA = Path(__file__).resolve().parent.parent / 'data' / 'records.json'


@pytest.fixture(scope='module')
def dataset():
    with open(DATA) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def travel_map(dataset):
    return {(row['from'], row['to']): row['minutes'] for row in dataset['travel_times']}


def test_travel_rows_convert_to_tuple_key_map(dataset, travel_map):
    assert len(travel_map) == len(dataset['travel_times'])
    assert all(isinstance(k, tuple) and len(k) == 2 for k in travel_map)


def test_all_dataset_orders_assign_deterministically(dataset, travel_map):
    partners = dataset['partners']
    first = [assign_order(o, partners, travel_map) for o in dataset['orders']]
    second = [assign_order(o, partners, travel_map) for o in dataset['orders']]
    assert first == second
    for order, result in zip(dataset['orders'], first):
        assert result['order_id'] == order['order_id']
        assert 'reason' in result
        if result['partner_id'] is None:
            assert result['eta_minutes'] is None
        else:
            assert result['eta_minutes'] >= 0


def test_assignment_never_chooses_ineligible_dataset_partner(dataset, travel_map):
    partners_by_id = {p['partner_id']: p for p in dataset['partners']}
    for order in dataset['orders']:
        result = assign_order(order, dataset['partners'], travel_map)
        if result['partner_id'] is None:
            continue
        chosen = partners_by_id[result['partner_id']]
        assert chosen['active'] is True
        assert len(chosen['active_order_ids']) < chosen['capacity']
        assert (chosen['zone'], order['restaurant_id']) in travel_map
        assert (order['restaurant_id'], order['destination_zone']) in travel_map


def test_full_cancellation_stream_replay_is_idempotent(dataset):
    partners = {p['partner_id']: dict(p) for p in dataset['partners']}
    events = dataset['cancellation_events']

    def replay(state):
        for event in events:
            pid = event.get('partner_id')
            if pid in state:
                state[pid] = process_cancellation(
                    state[pid], event.get('order_id'), event.get('event_id'))
        return state

    once = replay({k: dict(v) for k, v in partners.items()})
    twice = replay({k: dict(v) for k, v in once.items()})
    assert once == twice
    for partner in once.values():
        assert partner['workload_minutes'] >= 0


def test_duplicate_event_ids_in_dataset_do_not_double_release(dataset):
    partners = {p['partner_id']: dict(p) for p in dataset['partners']}
    seen = set()
    for event in dataset['cancellation_events']:
        pid = event.get('partner_id')
        if pid not in partners:
            continue
        before = partners[pid]['workload_minutes']
        partners[pid] = process_cancellation(
            partners[pid], event.get('order_id'), event.get('event_id'))
        # event IDs are deduplicated per partner record, matching the service.
        key = (pid, event.get('event_id'))
        if key in seen:
            assert partners[pid]['workload_minutes'] == before
        seen.add(key)
