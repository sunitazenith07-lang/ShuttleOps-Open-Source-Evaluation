"""Accounting must be complete before a cancellation is applied."""
from copy import deepcopy
import pytest
from fixtures import sample_inputs
from models import new_order, new_partner
from service import assign_order, process_cancellation


@pytest.mark.parametrize('missing', ['workload_minutes', 'minutes_by_order', 'active_order_ids', 'order_minutes'])
def test_missing_accounting_does_not_apply_or_consume_event(missing):
    p = new_partner('P', 'Z')
    p.update(active_order_ids=['O'], workload_minutes=5, minutes_by_order={'O':5})
    if missing == 'order_minutes':
        del p['minutes_by_order']['O']
    else:
        del p[missing]
    before = deepcopy(p)
    assert process_cancellation(p, 'O', 'E') == before
    assert p == before


def test_fixture_incomplete_accounting_can_be_repaired_and_retried():
    _, partners, _ = sample_inputs()
    p = partners[0]
    unchanged = process_cancellation(p, 'OLD-1', 'E')
    assert unchanged == p
    unchanged['minutes_by_order']['OLD-1'] = 5
    result = process_cancellation(unchanged, 'OLD-1', 'E')
    assert result['active_order_ids'] == []
    assert result['workload_minutes'] == 0
    assert result['processed_cancellation_ids'] == ['E']


def test_explicit_zero_accounting_is_valid():
    p = new_partner('P', 'Z')
    p.update(active_order_ids=['O'], minutes_by_order={'O':0})
    result = process_cancellation(p, 'O', 'E')
    assert result['active_order_ids'] == []
    assert result['workload_minutes'] == 0
    assert result['processed_cancellation_ids'] == ['E']


@pytest.mark.parametrize('active', [True, False])
def test_already_active_order_is_not_assigned_to_another_partner(active):
    a, b = new_partner('A', 'Z'), new_partner('B', 'Z')
    a.update(active=active, active_order_ids=['O'])
    before = deepcopy([a,b])
    result = assign_order(new_order('O','R','D'), [a,b], {('Z','R'):1,('R','D'):1})
    assert result['partner_id'] is None
    assert result['reason'] == 'order is already active'
    assert [a,b] == before
