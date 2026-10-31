"""Regression coverage for the optional explainability feature."""
from copy import deepcopy
from models import new_order, new_partner
from explainer import explain_dispatch


def setup():
    order = new_order('O-1', 'R-1', 'Z-9', 12)
    partners = [new_partner('P-02', 'Z-2', 2), new_partner('P-01', 'Z-1', 1)]
    travel = {('Z-1', 'R-1'): 8, ('Z-2', 'R-1'): 8, ('R-1', 'Z-9'): 10}
    return order, partners, travel


def test_candidate_reasons_and_tie_breaking():
    order, partners, travel = setup()
    report = explain_dispatch(order, partners, travel, 0)
    assert report['decision']['partner_id'] == 'P-01'
    assert [x['partner_id'] for x in report['candidates']] == ['P-01', 'P-02']
    assert [x['status'] for x in report['candidates']] == ['SELECTED', 'ELIGIBLE']
    assert all(x['eta_minutes'] == 30 for x in report['candidates'])


def test_rejection_reasons_are_specific():
    order, partners, travel = setup()
    partners[0]['active'] = False
    partners[1]['active_order_ids'] = ['busy']
    report = explain_dispatch(order, partners, travel)
    assert [x['reason'] for x in report['candidates']] == ['Full capacity', 'Inactive partner']


def test_missing_travel_not_imputed():
    order, partners, travel = setup()
    del travel[('Z-1', 'R-1')]
    report = explain_dispatch(order, partners, travel)
    row = report['candidates'][0]
    assert row['reason'] == 'Missing travel data'
    assert row['eta_minutes'] is None


def test_no_mutation_and_deterministic_display():
    order, partners, travel = setup()
    before = deepcopy((order, partners, travel))
    first = explain_dispatch(order, partners, travel)
    second = explain_dispatch(order, list(reversed(partners)), travel)
    assert first == second
    assert (order, partners, travel) == before


def test_empty_and_malformed_candidates():
    order, partners, travel = setup()
    assert explain_dispatch(order, [], travel)['candidates'] == []
    report = explain_dispatch(order, [None, {'partner_id': 'BROKEN'}], travel)
    assert all(row['status'] == 'REJECTED' for row in report['candidates'])


def test_invalid_order_explained_without_crash():
    order, partners, travel = setup()
    order['prep_minutes'] = -10
    report = explain_dispatch(order, partners, travel)
    assert report['decision']['partner_id'] is None
    assert all(r['reason'] == 'Invalid order' for r in report['candidates'])
