"""Optional decision reports must explain, rather than change, dispatch."""

from copy import deepcopy
from itertools import permutations
import json
from pathlib import Path

import pytest

from fixtures import sample_inputs
from models import new_order, new_partner
from service import assign_order, estimate_eta, explain_assignment, process_cancellation


TRAVEL = {('Z', 'R'): 1, ('R', 'D'): 2}


def test_demo_explains_winner_and_higher_eta_without_changing_assignment():
    order, partners, travel = sample_inputs()
    original_result = assign_order(order, partners, travel)
    result = explain_assignment(order, partners, travel)
    assert {key: value for key, value in result.items() if key != 'candidates'} == original_result
    assert 'candidates' not in original_result
    assert result['candidates'] == [
        {'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35,
         'eligible': True, 'candidate_index': 0, 'selected': True,
         'reason': 'selected by ETA and partner ID'},
        {'partner_id': 'P-1', 'pickup_minutes': 14, 'eta_minutes': 36,
         'eligible': True, 'candidate_index': 1, 'selected': False,
         'reason': 'higher ETA than selected partner'},
    ]


@pytest.mark.parametrize('changes,reason', [
    ({'active': False}, 'inactive partner'),
    ({'capacity': 0}, 'invalid capacity or active orders'),
    ({'capacity': 1, 'active_order_ids': ['OLD']}, 'partner at capacity'),
    ({'zone': 'UNKNOWN'}, 'missing travel time'),
    ({'partner_id': None}, 'invalid partner'),
    ({'active_order_ids': ['A', 'A']}, 'invalid capacity or active orders'),
    ({'workload_minutes': -1}, 'invalid workload'),
])
def test_rejection_reason_is_retained_alongside_valid_winner(changes, reason):
    partner = new_partner('BAD', 'Z')
    partner.update(changes)
    result = explain_assignment(new_order('O', 'R', 'D'),
                                [partner, new_partner('OK', 'Z')], TRAVEL)
    rejected, selected = result['candidates']
    assert (rejected['eligible'], rejected['selected'], rejected['reason']) == (False, False, reason)
    assert rejected['eta_minutes'] is None
    assert result['partner_id'] == 'OK'
    assert selected['eligible'] and selected['selected']


@pytest.mark.parametrize('bad', [None, [], 'partner', 1])
def test_malformed_candidate_keeps_its_input_index(bad):
    result = explain_assignment(new_order('O', 'R', 'D'),
                                [bad, new_partner('P', 'Z')], TRAVEL)
    assert result['candidates'][0] == {
        'partner_id': None, 'eta_minutes': None, 'eligible': False,
        'reason': 'invalid partner', 'candidate_index': 0, 'selected': False,
    }
    assert result['candidates'][1]['candidate_index'] == 1
    assert result['candidates'][1]['selected'] is True


def test_tie_explanation_and_winner_are_stable_across_permutations():
    partners = [new_partner(pid, 'Z') for pid in ['P-2', 'P-10', 'P-1']]
    for ordered in permutations(partners):
        result = explain_assignment(new_order('O', 'R', 'D'), ordered, TRAVEL)
        assert result['partner_id'] == 'P-1'
        assert [row['partner_id'] for row in result['candidates']] == [p['partner_id'] for p in ordered]
        assert sum(row['selected'] for row in result['candidates']) == 1
        for row in result['candidates']:
            assert row['eligible'] is True
            if row['partner_id'] != 'P-1':
                assert row['reason'] == 'equal ETA; earlier partner ID selected'


def test_identical_duplicate_candidate_rows_select_only_first_row():
    partner = new_partner('P', 'Z')
    result = explain_assignment(new_order('O', 'R', 'D'), [partner, partner], TRAVEL)
    assert [row['selected'] for row in result['candidates']] == [True, False]
    assert result['candidates'][1]['reason'] == 'equal ETA and partner ID; earlier candidate selected'


def test_all_candidates_rejected_has_no_selected_row():
    inactive = new_partner('A', 'Z')
    inactive['active'] = False
    result = explain_assignment(new_order('O', 'R', 'D'),
                                [inactive, new_partner('B', 'UNKNOWN')], TRAVEL)
    assert result['partner_id'] is None
    assert result['reason'] == 'no eligible partner or missing time data'
    assert [row['reason'] for row in result['candidates']] == ['inactive partner', 'missing travel time']
    assert not any(row['selected'] or row['eligible'] for row in result['candidates'])


@pytest.mark.parametrize('partners', [[], None, {}, 1, 'partners'])
def test_empty_or_invalid_partner_collection_matches_existing_result(partners):
    order = new_order('O', 'R', 'D')
    assert explain_assignment(order, partners, TRAVEL) == dict(
        assign_order(order, partners, TRAVEL), candidates=[])


@pytest.mark.parametrize('order,now,reason', [
    (None, 0, 'invalid order'),
    (new_order('O', 'R', 'D', -1), 0, 'invalid order'),
    (new_order('O', 'R', 'D'), float('inf'), 'invalid current time'),
    (new_order('O', 'R', 'D'), float('nan'), 'invalid current time'),
])
def test_invalid_request_explains_every_candidate(order, now, reason):
    result = explain_assignment(order, [new_partner('P', 'Z')], TRAVEL, now)
    assert result['partner_id'] is None
    assert result['candidates'][0]['reason'] == reason
    assert result['candidates'][0]['selected'] is False


@pytest.mark.parametrize('travel,reason', [
    (None, 'invalid travel data'),
    ({('Z', 'R'): True, ('R', 'D'): 2}, 'invalid travel time'),
    ({('Z', 'R'): 1e308, ('R', 'D'): 1e308}, 'time calculation overflow'),
])
def test_invalid_travel_and_overflow_are_explained(travel, reason):
    result = explain_assignment(new_order('O', 'R', 'D'), [new_partner('P', 'Z')], travel)
    assert result['candidates'][0]['reason'] == reason
    assert result['partner_id'] is None


def test_fractional_report_does_not_mutate_inputs():
    order = new_order('O', 'R', 'D', 0.25)
    partner = new_partner('P', 'Z')
    partner['workload_minutes'] = 0.5
    partners = [partner]
    travel = {('Z', 'R'): 0.25, ('R', 'D'): 0.5}
    before = deepcopy((order, partners, travel))
    result = explain_assignment(order, partners, travel, now=0.5)
    assert (result['pickup_minutes'], result['eta_minutes']) == (1.25, 2.0)
    assert (order, partners, travel) == before


def test_explanation_preserves_every_dataset_assignment():
    data = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'records.json').read_text())
    travel = {(row['from'], row['to']): row['minutes'] for row in data['travel_times']}
    for order in data['orders']:
        result = explain_assignment(order, data['partners'], travel, now=7)
        candidates = result.pop('candidates')
        assert result == assign_order(order, data['partners'], travel, now=7)
        assert len(candidates) == len(data['partners'])
        selected = [row for row in candidates if row['selected']]
        assert len(selected) == (0 if result['partner_id'] is None else 1)
        if selected:
            assert selected[0]['partner_id'] == result['partner_id']
            assert selected[0]['eta_minutes'] == result['eta_minutes']
        assert all(row['reason'] for row in candidates)


def test_large_integer_eta_and_mixed_float_overflow_are_safe():
    huge = 10**1000
    order = new_order('O', 'R', 'D', 0)
    partner = new_partner('P', 'Z')
    result = explain_assignment(order, [partner], {('Z', 'R'): huge, ('R', 'D'): 0}, now=huge)
    assert result['eta_minutes'] == 2 * huge
    assert result['candidates'][0]['selected'] is True
    mixed = estimate_eta(order, partner, {('Z', 'R'): huge, ('R', 'D'): 0.0})
    assert mixed['eligible'] is False
    assert mixed['reason'] == 'time calculation overflow'


def test_fractional_cancellation_remains_idempotent():
    partner = new_partner('P', 'Z')
    partner.update(active_order_ids=['A'], workload_minutes=0.75, minutes_by_order={'A': 0.25})
    once = process_cancellation(partner, 'A', 'C')
    assert once['workload_minutes'] == 0.5
    assert process_cancellation(once, 'A', 'C') == once
