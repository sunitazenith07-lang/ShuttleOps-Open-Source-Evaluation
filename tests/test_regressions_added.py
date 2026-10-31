"""Additional regressions for malformed records and state consistency."""
from copy import deepcopy
from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


def _travel():
    return {('Z', 'R'): 2, ('R', 'D'): 3}


def test_malformed_partner_entries_do_not_crash():
    result = assign_order(new_order('O', 'R', 'D'), [None, 1, {}, new_partner('P', 'Z')], _travel())
    assert result['partner_id'] == 'P'


def test_missing_route_does_not_default_to_zero():
    result = assign_order(new_order('O', 'R', 'D'), [new_partner('P', 'Z')], {('Z', 'R'): 0})
    assert result['partner_id'] is None


def test_invalid_order_does_not_assign():
    assert assign_order({'order_id': 'O'}, [new_partner('P', 'Z')], _travel())['partner_id'] is None


def test_duplicate_event_does_not_release_reused_order_id():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O'], workload_minutes=5, minutes_by_order={'O': 5})
    cancelled = process_cancellation(partner, 'O', 'EVENT')
    cancelled.update(active_order_ids=['O'], workload_minutes=9, minutes_by_order={'O': 9})
    replay = process_cancellation(cancelled, 'O', 'EVENT')
    assert replay['active_order_ids'] == ['O']
    assert replay['workload_minutes'] == 9
    assert replay['processed_cancellation_ids'] == ['EVENT']


def test_cancellation_does_not_mutate_original():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['O'], workload_minutes=4, minutes_by_order={'O': 4})
    original = deepcopy(partner)
    process_cancellation(partner, 'O', 'E')
    assert partner == original


def test_invalid_time_values_are_rejected():
    partner = new_partner('P', 'Z')
    for bad in (float('nan'), float('inf'), -1, True, '5'):
        assert not estimate_eta(new_order('O', 'R', 'D'), partner, {('Z', 'R'): bad, ('R', 'D'): 3})['eligible']


def test_partner_at_capacity_is_rejected():
    partner = new_partner('P', 'Z', capacity=1)
    partner['active_order_ids'] = ['OLD']
    assert assign_order(new_order('O', 'R', 'D'), [partner], _travel())['partner_id'] is None


def test_tie_independent_of_input_order():
    a, b = new_partner('A', 'Z'), new_partner('B', 'Z')
    for partners in ([a, b], [b, a]):
        assert assign_order(new_order('O', 'R', 'D'), partners, _travel())['partner_id'] == 'A'
