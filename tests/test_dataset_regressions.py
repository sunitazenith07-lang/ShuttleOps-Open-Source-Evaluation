"""Check the supplied synthetic records against independent reference arithmetic."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from service import assign_order, process_cancellation


DATA = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'records.json').read_text())
TRAVEL = {(row['from'], row['to']): row['minutes'] for row in DATA['travel_times']}


@pytest.mark.parametrize('order', DATA['orders'], ids=lambda order: order['order_id'])
def test_dataset_assignment_matches_reference(order):
    # Records are valid numeric examples. Invalid types are tested separately.
    expected = []
    now = 7
    for partner in DATA['partners']:
        if not partner['active'] or len(partner['active_order_ids']) >= partner['capacity']:
            continue
        inbound = (partner['zone'], order['restaurant_id'])
        outbound = (order['restaurant_id'], order['destination_zone'])
        if inbound not in TRAVEL or outbound not in TRAVEL:
            continue
        pickup = now + TRAVEL[inbound] + partner['workload_minutes']
        delivery = pickup + order['prep_minutes'] + TRAVEL[outbound]
        expected.append((delivery, partner['partner_id'], pickup))
    result = assign_order(order, DATA['partners'], TRAVEL, now=now)
    assert result == assign_order(order, list(reversed(DATA['partners'])), TRAVEL, now=now)
    if expected:
        eta, partner_id, pickup = sorted(expected)[0]
        assert (result['eta_minutes'], result['partner_id'], result['pickup_minutes']) == (eta, partner_id, pickup)
    else:
        assert result['partner_id'] is None
        assert result['eta_minutes'] is None
        assert result['reason']


def test_dataset_cancellation_stream_matches_reference():
    original = deepcopy(DATA['partners'])
    actual = {p['partner_id']: deepcopy(p) for p in original}
    expected = deepcopy(actual)
    seen = {pid: set() for pid in actual}
    for event in DATA['cancellation_events']:
        pid = event['partner_id']
        event_id = event.get('event_id')
        order_id = event['order_id']
        before = deepcopy(actual[pid])
        result = process_cancellation(actual[pid], order_id, event_id)
        assert actual[pid] == before
        actual[pid] = result
        if not event_id or event_id in seen[pid]:
            assert result == before
        else:
            seen[pid].add(event_id)
            partner = expected[pid]
            partner.setdefault('processed_cancellation_ids', []).append(event_id)
            if order_id in partner['active_order_ids']:
                partner['active_order_ids'].remove(order_id)
                released = partner['minutes_by_order'].pop(order_id)
                partner['workload_minutes'] = max(0, partner['workload_minutes'] - released)
        assert actual[pid] == expected[pid]
    assert DATA['partners'] == original
