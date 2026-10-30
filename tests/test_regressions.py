"""Regression tests for malformed input, deterministic selection and safe release."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


TRAVEL = {('Z', 'R'): 8, ('R', 'D'): 12}


@pytest.mark.parametrize('bad', [None, [], '', 1, {}, {'order_id': 'O'}])
def test_malformed_orders_return_unassigned(bad):
    result = assign_order(bad, [new_partner('P', 'Z')], TRAVEL)
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None
    assert result['reason']


@pytest.mark.parametrize('bad', [None, [], '', 1, {}, {'partner_id': []}])
def test_bad_partner_does_not_block_valid_candidate(bad):
    result = assign_order(new_order('O', 'R', 'D'), [bad, new_partner('P', 'Z')], TRAVEL)
    assert result['partner_id'] == 'P'


@pytest.mark.parametrize('field,value', [
    ('zone', []), ('partner_id', ' '), ('active', 'yes'), ('active', 1),
    ('active_order_ids', None), ('active_order_ids', ['A', 'A']),
    ('workload_minutes', -1), ('workload_minutes', True), ('workload_minutes', float('nan')),
    ('workload_minutes', float('inf')), ('workload_minutes', '5'),
])
def test_malformed_partner_fields_are_ineligible(field, value):
    partner = new_partner('P', 'Z')
    partner[field] = value
    result = estimate_eta(new_order('O', 'R', 'D'), partner, TRAVEL)
    assert result['eligible'] is False
    assert result['reason']


@pytest.mark.parametrize('travel', [None, [], '', 1])
def test_malformed_travel_is_unassigned(travel):
    assert assign_order(new_order('O', 'R', 'D'), [new_partner('P', 'Z')], travel)['partner_id'] is None


def test_worked_eta_and_inputs_remain_unchanged():
    order, partner = new_order('O', 'R', 'D', 10), new_partner('P', 'Z')
    partner['workload_minutes'] = 5
    before = deepcopy((order, partner, TRAVEL))
    result = assign_order(order, [partner], TRAVEL, now=3)
    assert result['pickup_minutes'] == 16
    assert result['eta_minutes'] == 38
    assert (order, partner, TRAVEL) == before


def test_full_partner_and_missing_route_leave_order_unassigned():
    full = new_partner('A', 'Z', 1)
    full['active_order_ids'] = ['OLD']
    missing = new_partner('B', 'UNKNOWN')
    result = assign_order(new_order('O', 'R', 'D'), [full, missing], TRAVEL)
    assert result['partner_id'] is result['eta_minutes'] is None
    assert result['reason']


def test_lexicographic_tie_and_duplicate_partner_ids():
    partners = [new_partner(pid, 'Z') for pid in ['P2', 'P10', 'A', 'A']]
    order = new_order('O', 'R', 'D')
    assert assign_order(order, partners, TRAVEL) == assign_order(order, partners[::-1], TRAVEL)
    assert assign_order(order, partners, TRAVEL)['partner_id'] == 'P10'


def test_existing_active_order_not_recommended_again():
    partner = new_partner('P', 'Z')
    partner['active_order_ids'] = ['O']
    assert not estimate_eta(new_order('O', 'R', 'D'), partner, TRAVEL)['eligible']


def busy_partner():
    p = new_partner('P', 'Z')
    p.update(active_order_ids=['A', 'B'], workload_minutes=15, minutes_by_order={'A': 5, 'B': 10})
    return p


def test_cancellation_conflicting_replay_and_new_id_cannot_release_twice():
    partner = busy_partner()
    original = deepcopy(partner)
    once = process_cancellation(partner, 'A', 'C1')
    assert partner == original
    assert once['active_order_ids'] == ['B']
    assert once['minutes_by_order'] == {'B': 10}
    assert once['workload_minutes'] == 10
    assert process_cancellation(once, 'B', 'C1') == once
    assert process_cancellation(once, 'A', 'C2') == once
    assert once['processed_cancellation_ids'] == ['C1']


@pytest.mark.parametrize('order,event', [('UNKNOWN', 'C'), ('A', None), ('A', ''), ([], 'C'), ('A', [])])
def test_bad_cancellations_are_exact_noops(order, event):
    partner = busy_partner()
    assert process_cancellation(partner, order, event) == partner


@pytest.mark.parametrize('field,value', [('workload_minutes', -1), ('active_order_ids', None),
    ('minutes_by_order', []), ('minutes_by_order', {'A': -5}), ('processed_cancellation_ids', None)])
def test_corrupt_cancellation_state_is_unchanged(field, value):
    partner = busy_partner()
    partner[field] = value
    assert process_cancellation(partner, 'A', 'C') == partner


def test_missing_per_order_minutes_releases_capacity_without_guessing_workload():
    partner = busy_partner()
    del partner['minutes_by_order']['A']
    result = process_cancellation(partner, 'A', 'C')
    assert result['workload_minutes'] == 15
    assert result['active_order_ids'] == ['B']


def test_numeric_overflow_is_safe():
    order = new_order('O', 'R', 'D', 1e308)
    assert not estimate_eta(order, new_partner('P', 'Z'), TRAVEL, 1e308)['eligible']
    order['prep_minutes'] = 0
    assert estimate_eta(order, new_partner('P', 'Z'), TRAVEL, 10**1000)['eligible'] is True
    # Mixed arithmetic that cannot represent a huge integer as float must be rejected.
    assert not estimate_eta(order, new_partner('P', 'Z'), {('Z', 'R'): 1.0, ('R', 'D'): 0}, 10**1000)['eligible']


def test_synthetic_dataset_is_deterministic_and_cancellations_preserve_bounds():
    data = json.loads((Path(__file__).parents[1] / 'data/records.json').read_text())
    travel = {(row['from'], row['to']): row['minutes'] for row in data['travel_times']}
    before = deepcopy(data)
    for order in data['orders']:
        result = assign_order(order, data['partners'], travel)
        assert result == assign_order(order, data['partners'][::-1], travel)
        if result['partner_id'] is not None:
            candidates = []
            for p in data['partners']:
                e = estimate_eta(order, p, travel)
                if e['eligible']:
                    candidates.append((e['eta_minutes'], e['partner_id']))
            assert (result['eta_minutes'], result['partner_id']) == min(candidates)
    partners = {p['partner_id']: deepcopy(p) for p in data['partners']}
    for e in data['cancellation_events']:
        p = partners.get(e.get('partner_id'))
        if p is None:
            continue
        updated = process_cancellation(p, e.get('order_id'), e.get('event_id'))
        assert 0 <= updated['workload_minutes'] <= p['workload_minutes']
        assert len(updated['active_order_ids']) <= len(p['active_order_ids'])
        assert process_cancellation(updated, e.get('order_id'), e.get('event_id')) == updated
        partners[p['partner_id']] = updated
    assert data == before
