"""Regression tests for defects fixed in service.py.

Each test pins a required behaviour from the problem statement: eligibility
rules, ETA correctness, deterministic selection and cancellation idempotency.
These complement the starter tests, which are preserved unchanged.
"""
import pytest
from models import new_order, new_partner
from service import (estimate_eta, assign_order, process_cancellation,
                     explain_assignment)


# --- Eligibility: empty / inactive / capacity -------------------------------

def test_empty_partner_list_leaves_order_unassigned():
    result = assign_order(new_order('O', 'R', 'D'), [], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None
    assert result['reason']


def test_all_partners_inactive_leaves_order_unassigned():
    partners = [new_partner(f'P{i}', 'Z') for i in range(3)]
    for p in partners:
        p['active'] = False
    result = assign_order(new_order('O', 'R', 'D'), partners, {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None
    assert 'inactive' in result['reason']


def test_all_partners_at_capacity_leaves_order_unassigned():
    partners = [new_partner(f'P{i}', 'Z', capacity=2) for i in range(3)]
    for p in partners:
        p['active_order_ids'] = ['X1', 'X2']
    result = assign_order(new_order('O', 'R', 'D'), partners, {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None
    assert 'capacity' in result['reason']


def test_full_partner_cannot_receive_extra_order_but_others_can():
    full = new_partner('FULL', 'Z', capacity=1)
    full['active_order_ids'] = ['BUSY']
    free = new_partner('FREE', 'Z', capacity=1)
    result = assign_order(new_order('O', 'R', 'D'), [full, free], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] == 'FREE'


@pytest.mark.parametrize('capacity', [0, -1, -100, 1.5, '2', None, True])
def test_invalid_capacity_partner_ineligible(capacity):
    partner = new_partner('P', 'Z')
    partner['capacity'] = capacity
    result = assign_order(new_order('O', 'R', 'D'), [partner], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None


# --- Travel-time validation -------------------------------------------------

def test_missing_partner_to_restaurant_route_ineligible():
    result = estimate_eta(new_order('O', 'R', 'D'), new_partner('P', 'Z'),
                          {('R', 'D'): 5})
    assert result['eligible'] is False
    assert result['eta_minutes'] is None


def test_missing_restaurant_to_customer_route_ineligible():
    result = estimate_eta(new_order('O', 'R', 'D'), new_partner('P', 'Z'),
                          {('Z', 'R'): 5})
    assert result['eligible'] is False
    assert result['eta_minutes'] is None


def test_missing_travel_is_never_treated_as_zero():
    order = new_order('O', 'R', 'D', 10)
    has_route = new_partner('HAS', 'Z1')
    missing = new_partner('MISS', 'Z2')
    travel = {('Z1', 'R'): 30, ('R', 'D'): 5}
    result = assign_order(order, [missing, has_route], travel)
    assert result['partner_id'] == 'HAS'


@pytest.mark.parametrize('leg', [('Z', 'R'), ('R', 'D')])
def test_negative_travel_time_rejected(leg):
    order = new_order('O', 'R', 'D')
    partner = new_partner('P', 'Z')
    travel = {('Z', 'R'): 5, ('R', 'D'): 5}
    travel[leg] = -1
    result = estimate_eta(order, partner, travel)
    assert result['eligible'] is False
    assert result['eta_minutes'] is None


def test_unknown_restaurant_id_has_no_routes_and_is_unassigned():
    order = new_order('O', 'NO-SUCH-RESTAURANT', 'D')
    result = assign_order(order, [new_partner('P', 'Z')], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None


# --- Order validation -------------------------------------------------------

def test_negative_preparation_time_rejected():
    order = new_order('O', 'R', 'D', -5)
    result = assign_order(order, [new_partner('P', 'Z')], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None


@pytest.mark.parametrize('order', [None, 'not-a-dict', {}, {'order_id': 'O'}])
def test_malformed_order_record_is_safe(order):
    result = assign_order(order, [new_partner('P', 'Z')], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None


@pytest.mark.parametrize('bad_partner', [None, 'not-a-dict', {'zone': 'Z'}])
def test_malformed_partner_record_is_safe(bad_partner):
    result = assign_order(new_order('O', 'R', 'D'), [bad_partner], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None


def test_negative_workload_partner_ineligible():
    partner = new_partner('P', 'Z')
    partner['workload_minutes'] = -10
    result = assign_order(new_order('O', 'R', 'D'), [partner], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert result['partner_id'] is None


# --- ETA formula ------------------------------------------------------------

def test_eta_and_pickup_formula():
    order = new_order('O', 'R', 'D', prep_minutes=10)
    partner = new_partner('P', 'Z')
    partner['workload_minutes'] = 7
    travel = {('Z', 'R'): 5, ('R', 'D'): 12}
    result = estimate_eta(order, partner, travel, now=3)
    # pickup = now + leg1 + workload = 3 + 5 + 7 = 15
    # eta    = pickup + prep + leg2  = 15 + 10 + 12 = 37
    assert result['pickup_minutes'] == 15
    assert result['eta_minutes'] == 37


# --- Selection --------------------------------------------------------------

def test_lowest_eta_wins_among_multiple_eligible_partners():
    order = new_order('O', 'R', 'D', prep_minutes=0)
    partners = [new_partner('SLOW', 'Z1'), new_partner('FAST', 'Z2'), new_partner('MID', 'Z3')]
    partners[0]['workload_minutes'] = 100
    travel = {('Z1', 'R'): 1, ('Z2', 'R'): 5, ('Z3', 'R'): 10, ('R', 'D'): 0}
    result = assign_order(order, partners, travel)
    assert result['partner_id'] == 'FAST'
    assert result['eta_minutes'] == 5


def test_equal_eta_tie_broken_by_partner_id():
    order = new_order('O', 'R', 'D', prep_minutes=0)
    a = new_partner('AAA', 'Z1')
    z = new_partner('ZZZ', 'Z2')
    travel = {('Z1', 'R'): 5, ('Z2', 'R'): 5, ('R', 'D'): 0}
    for _ in range(3):
        assert assign_order(order, [z, a], travel)['partner_id'] == 'AAA'
        assert assign_order(order, [a, z], travel)['partner_id'] == 'AAA'


def test_assignment_is_deterministic_across_repeated_calls():
    order, partners, travel = _demo_inputs()
    first = assign_order(order, partners, travel)
    for _ in range(5):
        assert assign_order(order, partners, travel) == first


def _demo_inputs():
    order = new_order('O-7', 'R-2', 'Z-9', 10)
    p1 = new_partner('P-2', 'Z-1')
    p1.update(workload_minutes=5, active_order_ids=['OLD-1'])
    p2 = new_partner('P-1', 'Z-3')
    p2.update(workload_minutes=2)
    travel = {('Z-1', 'R-2'): 8, ('R-2', 'Z-9'): 12, ('Z-3', 'R-2'): 12}
    return order, [p1, p2], travel


RESULT_KEYS = {'order_id', 'partner_id', 'pickup_minutes', 'eta_minutes', 'reason'}


@pytest.mark.parametrize('order,partners', [
    (new_order('O', 'R', 'D'), [new_partner('P', 'Z')]),
    (new_order('O', 'R', 'D'), []),
    (new_order('', 'R', 'D'), [new_partner('P', 'Z')]),
])
def test_assigned_and_unassigned_results_share_one_schema(order, partners):
    result = assign_order(order, partners, {('Z', 'R'): 1, ('R', 'D'): 1})
    assert set(result) == RESULT_KEYS
    if result['partner_id'] is None:
        assert result['pickup_minutes'] is None
        assert result['eta_minutes'] is None
        assert result['reason'] != 'assigned'
    else:
        assert result['reason'] == 'assigned'


def test_demo_fixture_assigns_p2_with_eta_35():
    order, partners, travel = _demo_inputs()
    result = assign_order(order, partners, travel)
    assert result == {'order_id': 'O-7', 'partner_id': 'P-2',
                      'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}


# --- Cancellation -----------------------------------------------------------

def test_duplicate_cancellation_event_applies_once():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1'], workload_minutes=9,
                   minutes_by_order={'O1': 9})
    once = process_cancellation(partner, 'O1', 'C1')
    twice = process_cancellation(once, 'O1', 'C1')
    assert twice['workload_minutes'] == 0
    assert twice['active_order_ids'] == []
    assert twice['processed_cancellation_ids'] == ['C1']


def test_duplicate_event_id_with_different_order_still_ignored():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1', 'O2'], workload_minutes=20,
                   minutes_by_order={'O1': 10, 'O2': 10})
    once = process_cancellation(partner, 'O1', 'C1')
    twice = process_cancellation(once, 'O2', 'C1')
    assert twice['active_order_ids'] == ['O2']
    assert twice['workload_minutes'] == 10
    assert twice['processed_cancellation_ids'] == ['C1']


def test_cancellation_of_unknown_order_is_safe():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1'], workload_minutes=9,
                   minutes_by_order={'O1': 9})
    result = process_cancellation(partner, 'UNKNOWN', 'C1')
    assert result['active_order_ids'] == ['O1']
    assert result['workload_minutes'] == 9
    assert result['processed_cancellation_ids'] == ['C1']


def test_workload_never_negative_when_release_exceeds_workload():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1'], workload_minutes=3,
                   minutes_by_order={'O1': 10})
    result = process_cancellation(partner, 'O1', 'C1')
    assert result['workload_minutes'] == 0


def test_cancellation_keeps_minutes_by_order_consistent():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1', 'O2'], workload_minutes=15,
                   minutes_by_order={'O1': 9, 'O2': 6})
    result = process_cancellation(partner, 'O1', 'C1')
    assert result['minutes_by_order'] == {'O2': 6}
    assert result['workload_minutes'] == 6


def test_cancellation_with_unhashable_order_id_is_safe():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=[['LIST-ID']], workload_minutes=10,
                   minutes_by_order={})
    result = process_cancellation(partner, ['LIST-ID'], 'C1')
    assert result['active_order_ids'] == []
    assert result['workload_minutes'] == 10
    assert result['processed_cancellation_ids'] == ['C1']


def test_cancellation_preserves_malformed_workload_instead_of_zeroing():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1'], workload_minutes='20',
                   minutes_by_order={'O1': 10})
    result = process_cancellation(partner, 'O1', 'C1')
    assert result['workload_minutes'] == '20'
    assert result['active_order_ids'] == []
    assert result['processed_cancellation_ids'] == ['C1']
    # The malformed record must still be rejected for new assignments.
    assigned = assign_order(new_order('O', 'R', 'D'), [result], {('Z', 'R'): 1, ('R', 'D'): 1})
    assert assigned['partner_id'] is None


def test_cancellation_does_not_mutate_original_partner():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1'], workload_minutes=9,
                   minutes_by_order={'O1': 9})
    process_cancellation(partner, 'O1', 'C1')
    assert partner['active_order_ids'] == ['O1']
    assert partner['workload_minutes'] == 9
    assert partner['processed_cancellation_ids'] == []


# --- Stretch feature: candidate-level explanation ---------------------------

def test_explain_assignment_reports_each_candidate():
    order = new_order('O', 'R', 'D', prep_minutes=0)
    ok = new_partner('OK', 'Z1')
    inactive = new_partner('OFF', 'Z2')
    inactive['active'] = False
    full = new_partner('FULL', 'Z3', capacity=1)
    full['active_order_ids'] = ['BUSY']
    no_route = new_partner('NOROUTE', 'Z4')
    travel = {('Z1', 'R'): 5, ('Z2', 'R'): 5, ('Z3', 'R'): 5, ('R', 'D'): 0}
    result = explain_assignment(order, [ok, inactive, full, no_route], travel)
    assert result['partner_id'] == 'OK'
    by_id = {c['partner_id']: c for c in result['candidates']}
    assert by_id['OK']['eligible'] is True
    assert by_id['OK']['eta_minutes'] == 5
    assert by_id['OFF']['reason'] == 'partner inactive'
    assert by_id['FULL']['reason'] == 'partner at capacity'
    assert 'travel' in by_id['NOROUTE']['reason']


def test_explain_assignment_matches_assign_order_result():
    order, partners, travel = _demo_inputs()
    explained = explain_assignment(order, partners, travel)
    assigned = assign_order(order, partners, travel)
    for key, value in assigned.items():
        assert explained[key] == value


def test_distinct_events_each_apply_once_in_order():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O1', 'O2'], workload_minutes=15,
                   minutes_by_order={'O1': 9, 'O2': 6})
    partner = process_cancellation(partner, 'O1', 'C1')
    partner = process_cancellation(partner, 'O2', 'C2')
    assert partner['active_order_ids'] == []
    assert partner['workload_minutes'] == 0
    assert partner['processed_cancellation_ids'] == ['C1', 'C2']
