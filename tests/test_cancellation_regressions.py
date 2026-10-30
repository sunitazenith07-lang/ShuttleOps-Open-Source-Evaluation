"""A replay must never release another order or damage the caller's state."""

from copy import deepcopy

import pytest

from models import new_partner
from service import process_cancellation


def loaded_partner():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['A', 'B'], workload_minutes=10,
                   minutes_by_order={'A': 4, 'B': 6})
    return partner


def test_same_event_with_different_payload_is_ignored():
    partner = loaded_partner()
    once = process_cancellation(partner, 'A', 'C')
    assert process_cancellation(once, 'B', 'C') == once
    assert once['active_order_ids'] == ['B']
    assert once['workload_minutes'] == 6
    assert once['minutes_by_order'] == {'B': 6}
    assert partner == loaded_partner()


@pytest.mark.parametrize('event_id', [None, '', ' ', [], 1, True])
def test_invalid_event_id_does_not_release_capacity(event_id):
    partner = loaded_partner()
    assert process_cancellation(partner, 'A', event_id) == partner


@pytest.mark.parametrize('field,value', [
    ('active_order_ids', None), ('active_order_ids', ['A', 'A']),
    ('processed_cancellation_ids', None), ('processed_cancellation_ids', [None]),
    ('minutes_by_order', None), ('minutes_by_order', {'A': -4}),
    ('minutes_by_order', {'A': True}), ('minutes_by_order', {'A': '4'}),
    ('minutes_by_order', {'B': 6}), ('workload_minutes', -10),
    ('workload_minutes', float('nan')),
])
def test_malformed_cancellation_state_is_not_changed(field, value):
    partner = loaded_partner()
    partner[field] = value
    before = deepcopy(partner)
    result = process_cancellation(partner, 'A', 'C')
    # NaN cannot be compared to itself; compare its representation for this no-op.
    assert repr(result) == repr(before)
    assert repr(partner) == repr(before)


def test_unknown_order_records_event_once_without_releasing_work():
    partner = loaded_partner()
    once = process_cancellation(partner, 'UNKNOWN', 'C')
    assert once['workload_minutes'] == 10
    assert once['active_order_ids'] == ['A', 'B']
    assert once['processed_cancellation_ids'] == ['C']
    assert process_cancellation(once, 'A', 'C') == once


def test_new_event_for_already_cancelled_order_does_not_release_twice():
    once = process_cancellation(loaded_partner(), 'A', 'C1')
    twice = process_cancellation(once, 'A', 'C2')
    assert twice['workload_minutes'] == 6
    assert twice['active_order_ids'] == ['B']
    assert twice['processed_cancellation_ids'] == ['C1', 'C2']


@pytest.mark.parametrize('partner', [None, [], 1, 'partner'])
def test_malformed_cancellation_record_is_safe(partner):
    assert process_cancellation(partner, 'A', 'C') == partner
