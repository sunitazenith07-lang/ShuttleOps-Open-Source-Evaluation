"""Regressions for malformed inputs, state isolation, and dataset dispatch."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation

TRAVEL = {('Z', 'R'): 2, ('R', 'D'): 3}


@pytest.mark.parametrize('bad', [None, [], 'bad', 5, True])
def test_malformed_records_are_rejected(bad):
    order, partner = new_order('O', 'R', 'D'), new_partner('P', 'Z')
    assert assign_order(bad, [partner], TRAVEL)['partner_id'] is None
    assert not estimate_eta(order, bad, TRAVEL)['eligible']
    assert not estimate_eta(order, partner, bad)['eligible']
    assert assign_order(order, bad, TRAVEL)['partner_id'] is None


@pytest.mark.parametrize('field,value', [
    ('partner_id', []), ('partner_id', ' '), ('zone', {}),
    ('active', 1), ('active', 'yes'), ('active_order_ids', None),
    ('active_order_ids', 'O'), ('active_order_ids', [[]]),
    ('active_order_ids', ['A', 'A']), ('workload_minutes', -1),
    ('workload_minutes', True), ('workload_minutes', '3'),
    ('workload_minutes', float('nan')), ('workload_minutes', float('inf')),
])
def test_invalid_partner_is_skipped_without_hiding_valid_candidate(field, value):
    invalid = new_partner('A', 'Z')
    invalid[field] = value
    valid = new_partner('B', 'Z')
    assert assign_order(new_order('O', 'R', 'D'), [invalid, valid], TRAVEL)['partner_id'] == 'B'


@pytest.mark.parametrize('field', ['order_id', 'restaurant_id', 'destination_zone', 'prep_minutes'])
def test_missing_required_order_fields(field):
    order = new_order('O', 'R', 'D')
    del order[field]
    assert assign_order(order, [new_partner('P', 'Z')], TRAVEL)['partner_id'] is None


def test_overflow_is_not_a_reliable_eta():
    result = estimate_eta(new_order('O', 'R', 'D', 1e308), new_partner('P', 'Z'),
                          {('Z', 'R'): 1e308, ('R', 'D'): 1e308})
    assert not result['eligible'] and result['eta_minutes'] is None


def test_fractional_times_and_lexicographic_tie_without_mutation():
    order = new_order('O', 'R', 'D', 0.5)
    partners = [new_partner('P2', 'Z'), new_partner('P10', 'Z')]
    before = deepcopy((order, partners, TRAVEL))
    result = assign_order(order, partners, TRAVEL, now=0.25)
    assert result['partner_id'] == 'P10'
    assert result['eta_minutes'] == 5.75
    assert (order, partners, TRAVEL) == before
    assert assign_order(order, list(reversed(partners)), TRAVEL, now=0.25) == result


def cancellation_partner():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['A', 'B'], workload_minutes=12,
                   minutes_by_order={'A': 5, 'B': 7})
    return partner


def test_cancellation_replay_cannot_cancel_a_different_order():
    partner = cancellation_partner()
    before = deepcopy(partner)
    once = process_cancellation(partner, 'A', 'E')
    assert partner == before
    assert once['active_order_ids'] == ['B']
    assert once['workload_minutes'] == 7
    assert once['minutes_by_order'] == {'B': 7}
    assert process_cancellation(once, 'B', 'E') == once
    final = process_cancellation(once, 'B', 'E2')
    assert final['active_order_ids'] == [] and final['workload_minutes'] == 0
    assert once['active_order_ids'] == ['B']


@pytest.mark.parametrize('bad', [None, '', [], {}, True])
def test_invalid_cancellation_ids_do_not_modify_state(bad):
    partner = cancellation_partner()
    assert process_cancellation(partner, 'A', bad) == partner
    assert process_cancellation(partner, bad, 'E') == partner


@pytest.mark.parametrize('field,value', [
    ('active_order_ids', None), ('processed_cancellation_ids', None),
    ('minutes_by_order', []), ('minutes_by_order', {'A': -5}),
    ('minutes_by_order', {'A': '5'}), ('workload_minutes', float('inf')),
])
def test_malformed_cancellation_state_is_not_partially_changed(field, value):
    partner = cancellation_partner()
    partner[field] = value
    before = deepcopy(partner)
    assert process_cancellation(partner, 'A', 'E') == before
    assert partner == before


def test_unknown_order_records_event_without_releasing_work():
    partner = cancellation_partner()
    result = process_cancellation(partner, 'UNKNOWN', 'E')
    assert result['active_order_ids'] == partner['active_order_ids']
    assert result['workload_minutes'] == 12
    assert result['processed_cancellation_ids'] == ['E']
    assert process_cancellation(result, 'UNKNOWN', 'E') == result


def test_missing_route_explained_and_zero_route_allowed():
    order, partner = new_order('O', 'R', 'D', 0), new_partner('P', 'Z')
    assert 'missing travel time' in assign_order(order, [partner], {})['reason']
    assert assign_order(order, [partner], {('Z', 'R'): 0, ('R', 'D'): 0})['eta_minutes'] == 0


def test_dataset_orders_are_deterministic_and_selected_partner_is_eligible():
    data = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'records.json').read_text())
    travel = {(row['from'], row['to']): row['minutes'] for row in data['travel_times']}
    partners = data['partners']
    before = deepcopy(data)
    for order in data['orders']:
        result = assign_order(order, partners, travel)
        assert result == assign_order(order, list(reversed(partners)), travel)
        if result['partner_id'] is not None:
            partner = next(p for p in partners if p['partner_id'] == result['partner_id'])
            assert partner['active'] is True
            assert len(partner['active_order_ids']) < partner['capacity']
            expected = (travel[(partner['zone'], order['restaurant_id'])]
                        + partner['workload_minutes'] + order['prep_minutes']
                        + travel[(order['restaurant_id'], order['destination_zone'])])
            assert result['eta_minutes'] == expected
        else:
            assert result['eta_minutes'] is None and result['reason']
    assert data == before
