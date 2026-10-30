"""Safety and selection cases beyond the original acceptance matrix."""

from copy import deepcopy
from itertools import permutations

import pytest

from fixtures import sample_inputs
from models import new_order, new_partner
from service import assign_order, estimate_eta


TRAVEL = {('Z', 'R'): 1, ('R', 'D'): 2}


@pytest.mark.parametrize('bad', [None, [], 'record', 7])
def test_malformed_records_are_safe(bad):
    order = new_order('O', 'R', 'D')
    partner = new_partner('P', 'Z')
    assert assign_order(bad, [partner], TRAVEL)['partner_id'] is None
    assert assign_order(order, [bad, partner], TRAVEL)['partner_id'] == 'P'
    assert estimate_eta(order, bad, TRAVEL)['eligible'] is False
    assert assign_order(order, [partner], bad)['partner_id'] is None


@pytest.mark.parametrize('field,value', [
    ('partner_id', ''), ('partner_id', []), ('zone', None),
    ('active', 1), ('active', 'yes'), ('active_order_ids', None),
    ('active_order_ids', 'O'), ('active_order_ids', ['O', 'O']),
    ('workload_minutes', -1), ('workload_minutes', '5'),
    ('workload_minutes', True), ('workload_minutes', float('nan')),
    ('workload_minutes', float('inf')),
])
def test_malformed_partner_fields_are_ineligible(field, value):
    partner = new_partner('P', 'Z')
    partner[field] = value
    result = estimate_eta(new_order('O', 'R', 'D'), partner, TRAVEL)
    assert result['eligible'] is False
    assert result['eta_minutes'] is None
    assert result['reason']


@pytest.mark.parametrize('field', ['order_id', 'restaurant_id', 'destination_zone', 'prep_minutes'])
def test_missing_required_order_field_is_rejected(field):
    order = new_order('O', 'R', 'D')
    del order[field]
    assert assign_order(order, [new_partner('P', 'Z')], TRAVEL)['partner_id'] is None


@pytest.mark.parametrize('bad_id', [' ', [], {}, True])
def test_invalid_identifier_is_rejected_before_route_lookup(bad_id):
    order = new_order('O', bad_id, 'D')
    assert assign_order(order, [new_partner('P', 'Z')], TRAVEL)['partner_id'] is None


def test_lowest_eta_is_selected_after_eligibility_filtering():
    order = new_order('O', 'R', 'D', 0)
    inactive = new_partner('A', 'FAST')
    inactive['active'] = False
    full = new_partner('B', 'FAST', 1)
    full['active_order_ids'] = ['OLD']
    missing = new_partner('C', 'UNKNOWN')
    available = new_partner('D', 'Z')
    result = assign_order(order, [inactive, full, missing, available],
                          TRAVEL | {('FAST', 'R'): 0})
    assert result['partner_id'] == 'D'
    assert result['eta_minutes'] == 3


def test_lexicographic_tie_is_independent_of_every_input_permutation():
    partners = [new_partner(pid, 'Z') for pid in ['P-2', 'P-10', 'P-1']]
    for permutation in permutations(partners):
        assert assign_order(new_order('O', 'R', 'D'), permutation, TRAVEL)['partner_id'] == 'P-1'


def test_unassigned_explanation_distinguishes_invalid_order_and_no_candidates():
    invalid = assign_order(None, [], {})
    empty = assign_order(new_order('O', 'R', 'D'), [], {})
    missing = assign_order(new_order('O', 'R', 'D'), [new_partner('P', 'Z')], {})
    assert invalid['reason'] == 'invalid order'
    assert empty['reason'] == 'no eligible partner or missing time data'
    assert missing['partner_id'] is None
    assert estimate_eta(new_order('O', 'R', 'D'), new_partner('P', 'Z'), {})['reason'] == 'missing travel time'


def test_demo_calculation_and_inputs_are_unchanged():
    order, partners, travel = sample_inputs()
    original = deepcopy((order, partners, travel))
    assert assign_order(order, partners, travel) == {
        'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13,
        'eta_minutes': 35, 'reason': 'assigned',
    }
    assert (order, partners, travel) == original


def test_float_sum_overflow_is_rejected():
    partner = new_partner('P', 'Z')
    partner['workload_minutes'] = 1e308
    assert estimate_eta(new_order('O', 'R', 'D'), partner,
                        {('Z', 'R'): 1e308, ('R', 'D'): 1})['eligible'] is False


def test_no_eligible_partner_example():
    order = new_order('O', 'R', 'D')
    inactive = new_partner('A', 'Z')
    inactive['active'] = False
    full = new_partner('B', 'Z', 1)
    full['active_order_ids'] = ['OLD']
    missing = new_partner('C', 'UNKNOWN')
    partners = [inactive, full, missing]
    assert [estimate_eta(order, p, TRAVEL)['reason'] for p in partners] == [
        'inactive partner', 'partner at capacity', 'missing travel time',
    ]
    assert assign_order(order, partners, TRAVEL) == {
        'order_id': 'O', 'partner_id': None, 'eta_minutes': None,
        'reason': 'no eligible partner or missing time data',
    }


@pytest.mark.parametrize('partners', [None, 1, 'partners', {}])
def test_malformed_partner_collection_is_safe(partners):
    assert assign_order(new_order('O', 'R', 'D'), partners, TRAVEL)['partner_id'] is None
