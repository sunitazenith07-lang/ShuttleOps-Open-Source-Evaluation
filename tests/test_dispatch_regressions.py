import pytest
from copy import deepcopy
from models import new_order, new_partner
from service import assign_order, compute_eta, estimate_eta, process_cancellation

TRAVEL = {('Z', 'R'): 1, ('R', 'D'): 1}


def order(prep=0):
    return new_order('O', 'R', 'D', prep)


def test_worked_eta_numbers():
    pickup, eta = compute_eta(0, 8, 5, 10, 12)
    assert (pickup, eta) == (13, 35)


def test_prep_is_not_part_of_pickup():
    p = new_partner('P', 'Z')
    p['workload_minutes'] = 3
    result = estimate_eta(new_order('O', 'R', 'D', 10), p, {('Z', 'R'): 2, ('R', 'D'): 4}, now=1)
    assert result['pickup_minutes'] == 1 + 2 + 3
    assert result['eta_minutes'] == 6 + 10 + 4


def test_inactive_partner_excluded():
    p = new_partner('P', 'Z')
    p['active'] = False
    result = assign_order(order(), [p], TRAVEL)
    assert result['partner_id'] is None
    assert 'P: inactive' in result['reason']


@pytest.mark.parametrize('load,expected', [(1, 'P'), (2, None)])
def test_capacity_boundary(load, expected):
    p = new_partner('P', 'Z', 2)
    p['active_order_ids'] = [f'OLD{i}' for i in range(load)]
    assert assign_order(order(), [p], TRAVEL)['partner_id'] == expected


def test_missing_partner_leg_is_not_zero():
    no_route = new_partner('A', 'X')
    far = new_partner('B', 'Y')
    travel = {('Y', 'R'): 50, ('R', 'D'): 1}
    result = assign_order(order(), [no_route, far], travel)
    assert result['partner_id'] == 'B'
    assert result['eta_minutes'] == 51


def test_missing_customer_leg_blocks_eta():
    result = assign_order(order(), [new_partner('P', 'Z')], {('Z', 'R'): 1})
    assert result['partner_id'] is None
    assert 'P: missing travel time' in result['reason']


def test_eta_tie_breaks_by_string_partner_id():
    partners = [new_partner('P2', 'Z'), new_partner('P10', 'Z')]
    for ordering in (partners, partners[::-1]):
        assert assign_order(order(), ordering, TRAVEL)['partner_id'] == 'P10'


def test_no_eligible_partner_reports_each_reason():
    inactive = new_partner('P1', 'Z')
    inactive['active'] = False
    full = new_partner('P2', 'Z', 1)
    full['active_order_ids'] = ['X']
    no_route = new_partner('P3', 'Z')
    result = assign_order(order(), [no_route, full, inactive], {})
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None
    assert result['reason'] == (
        'no eligible partner (P1: inactive; P2: at capacity; P3: missing travel time)'
    )


def loaded_partner():
    p = new_partner('P', 'Z')
    p.update(active_order_ids=['A', 'B'], workload_minutes=30, minutes_by_order={'A': 10, 'B': 20})
    return p


def test_duplicate_cancellation_releases_once():
    once = process_cancellation(loaded_partner(), 'A', 'C1')
    twice = process_cancellation(once, 'A', 'C1')
    assert once['active_order_ids'] == ['B']
    assert once['workload_minutes'] == 20
    assert twice == once


def test_same_event_id_for_another_order_is_ignored():
    once = process_cancellation(loaded_partner(), 'A', 'C1')
    result = process_cancellation(once, 'B', 'C1')
    assert result['active_order_ids'] == ['B']
    assert result['workload_minutes'] == 20


def test_cancellation_workload_never_negative():
    p = loaded_partner()
    p['workload_minutes'] = 5
    result = process_cancellation(p, 'B', 'C1')
    assert result['workload_minutes'] == 0


@pytest.mark.parametrize('order_id', ['UNKNOWN', None, ''])
def test_cancelling_unknown_order_changes_nothing(order_id):
    result = process_cancellation(loaded_partner(), order_id, 'C1')
    assert result['active_order_ids'] == ['A', 'B']
    assert result['workload_minutes'] == 30


def test_cancellation_does_not_mutate_input():
    p = loaded_partner()
    process_cancellation(p, 'A', 'C1')
    assert p == loaded_partner()


@pytest.mark.parametrize('field,value', [
    ('order_id', ''), ('order_id', None), ('order_id', '   '),
    ('restaurant_id', ''), ('destination_zone', None),
    ('prep_minutes', -1), ('prep_minutes', '5'), ('prep_minutes', None),
])
def test_invalid_order_is_rejected_with_reason(field, value):
    bad = order()
    bad[field] = value
    result = assign_order(bad, [new_partner('P', 'Z')], TRAVEL)
    assert result['partner_id'] is None
    assert result['reason'] == f'order rejected: invalid {field}'


def test_unknown_restaurant_is_unassigned():
    result = assign_order(new_order('O', 'NOWHERE', 'D'), [new_partner('P', 'Z')], TRAVEL)
    assert result['partner_id'] is None
    assert 'P: missing travel time' in result['reason']


@pytest.mark.parametrize('travel', [
    {('Z', 'R'): -1, ('R', 'D'): 1},
    {('Z', 'R'): 1, ('R', 'D'): -1},
    {('Z', 'R'): '1', ('R', 'D'): 1},
])
def test_negative_or_non_numeric_travel_is_rejected(travel):
    result = assign_order(order(), [new_partner('P', 'Z')], travel)
    assert result['partner_id'] is None
    assert 'P: invalid travel time' in result['reason']


@pytest.mark.parametrize('now', [-1, '5', None, True])
def test_invalid_current_time_is_rejected(now):
    result = assign_order(order(), [new_partner('P', 'Z')], TRAVEL, now)
    assert result['partner_id'] is None
    assert 'P: invalid current time' in result['reason']


def test_empty_partner_list_is_unassigned_with_reason():
    result = assign_order(order(), [], TRAVEL)
    assert result['partner_id'] is None
    assert result['reason'] == 'no eligible partner (no partners supplied)'


def test_empty_order_is_rejected():
    result = assign_order({}, [new_partner('P', 'Z')], TRAVEL)
    assert result['partner_id'] is None
    assert result['reason'] == 'order rejected: invalid order_id'


def test_result_is_independent_of_partner_order():
    partners = []
    for i, pid in enumerate(['P3', 'P1', 'P10', 'P2']):
        p = new_partner(pid, 'Z')
        p['workload_minutes'] = i % 2
        partners.append(p)
    first = assign_order(order(), partners, TRAVEL)
    for shuffled in (partners[::-1], partners[1:] + partners[:1]):
        assert assign_order(order(), shuffled, TRAVEL) == first


def test_assign_order_does_not_mutate_inputs():
    partners = [new_partner('P', 'Z')]
    snapshot = deepcopy(partners)
    assign_order(order(), partners, TRAVEL)
    assert partners == snapshot


def test_invalid_partner_zone_is_excluded_not_a_crash():
    p = new_partner('P', 'Z')
    p['zone'] = ['Z']
    result = assign_order(order(), [p], TRAVEL)
    assert result['partner_id'] is None
    assert 'P: invalid zone' in result['reason']


def test_cancellations_without_event_id_are_each_applied():
    once = process_cancellation(loaded_partner(), 'A', None)
    twice = process_cancellation(once, 'B', None)
    assert twice['active_order_ids'] == []
    assert twice['workload_minutes'] == 0
    assert twice['processed_cancellation_ids'] == []
