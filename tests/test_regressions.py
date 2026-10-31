import pytest

from models import new_order, new_partner
from service import assign_order, process_cancellation


def test_malformed_partner_is_skipped_without_blocking_valid_partner():
    order = new_order('O', 'R', 'D')
    valid_partner = new_partner('P-2', 'Z')
    malformed_partner = new_partner('P-1', 'Z')
    malformed_partner['workload_minutes'] = 'unknown'

    result = assign_order(
        order,
        [None, {}, malformed_partner, valid_partner],
        {('Z', 'R'): 1, ('R', 'D'): 2},
    )

    assert result['partner_id'] == 'P-2'


@pytest.mark.parametrize('order', [None, {}, {'order_id': 'O'}])
def test_malformed_order_is_left_unassigned(order):
    result = assign_order(
        order,
        [new_partner('P', 'Z')],
        {('Z', 'R'): 1, ('R', 'D'): 2},
    )

    assert result['partner_id'] is None
    assert result['eta_minutes'] is None
    assert result['reason']


def test_finite_inputs_that_overflow_eta_are_ineligible():
    order = new_order('O', 'R', 'D', prep_minutes=1)
    partner = new_partner('P', 'Z')
    partner['workload_minutes'] = 1e308

    result = assign_order(
        order,
        [partner],
        {('Z', 'R'): 1e308, ('R', 'D'): 1},
    )

    assert result['partner_id'] is None
    assert result['eta_minutes'] is None


def test_cancellation_does_not_mutate_original_partner():
    partner = new_partner('P', 'Z')
    partner.update(
        active_order_ids=['O'],
        workload_minutes=9,
        minutes_by_order={'O': 9},
    )

    result = process_cancellation(partner, 'O', 'C')

    assert result['active_order_ids'] == []
    assert result['workload_minutes'] == 0
    assert partner['active_order_ids'] == ['O']
    assert partner['workload_minutes'] == 9
