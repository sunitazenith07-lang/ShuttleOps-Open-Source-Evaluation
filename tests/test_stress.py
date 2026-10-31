"""Seeded stress checks and boundary regressions for dispatch."""
from copy import deepcopy
from itertools import product
import random

import pytest

from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


@pytest.mark.parametrize('workload,released', [(10**400, 0.5), (0.5, 10**400)])
def test_cancellation_numeric_overflow_is_atomic(workload, released):
    p = new_partner('P', 'Z')
    p.update(active_order_ids=['O'], workload_minutes=workload, minutes_by_order={'O': released})
    before = deepcopy(p)
    assert process_cancellation(p, 'O', 'E') == before
    assert p == before


def test_duplicate_partner_ids_have_deterministic_result():
    a, b = new_partner('P', 'X'), new_partner('P', 'Y')
    # Different pickup values can round to the same floating-point ETA.
    order = new_order('O', 'R', 'D', 1e20)
    travel = {('X', 'R'): 1, ('Y', 'R'): 2, ('R', 'D'): 0}
    assert assign_order(order, [a, b], travel) == assign_order(order, [b, a], travel)


@pytest.mark.parametrize('seed', range(30))
def test_random_dispatch_against_independent_oracle(seed):
    rng = random.Random(seed)
    for case in range(100):
        order = new_order('O', 'R', 'D', rng.randrange(80) / 4)
        now = rng.randrange(100) / 4
        travel = {('R', 'D'): rng.randrange(100) / 4}
        partners, expected = [], []
        for i in range(rng.randrange(25)):
            p = new_partner(f'P{i}', f'Z{i}', rng.randrange(1, 6))
            p['active'] = rng.choice([True, False])
            p['active_order_ids'] = [f'O{j}' for j in range(rng.randrange(6))]
            p['workload_minutes'] = rng.randrange(200) / 4
            partners.append(p)
            if rng.randrange(5) == 0:
                continue
            leg = rng.randrange(100) / 4
            travel[(p['zone'], 'R')] = leg
            if p['active'] and len(p['active_order_ids']) < p['capacity']:
                pickup = now + leg + p['workload_minutes']
                expected.append((pickup + order['prep_minutes'] + travel[('R', 'D')], p['partner_id'], pickup))
        before = deepcopy((order, partners, travel))
        result = assign_order(order, partners, travel, now)
        if expected:
            eta, pid, pickup = sorted(expected)[0]
            assert (result['eta_minutes'], result['partner_id'], result['pickup_minutes']) == (eta, pid, pickup)
        else:
            assert result['partner_id'] is None and result['reason']
        assert (order, partners, travel) == before
        rng.shuffle(partners)
        assert assign_order(order, partners, travel, now) == result


@pytest.mark.parametrize('seed', range(20))
def test_random_cancellation_sequences_against_state_model(seed):
    rng = random.Random(seed)
    p = new_partner('P', 'Z', 25)
    remaining = {f'O{i}': rng.randrange(100) for i in range(20)}
    p.update(active_order_ids=list(remaining), minutes_by_order=dict(remaining), workload_minutes=sum(remaining.values()))
    seen = []
    for _ in range(200):
        order = f'O{rng.randrange(25)}'
        event = f'E{rng.randrange(100)}'
        before = deepcopy(p)
        updated = process_cancellation(p, order, event)
        assert p == before
        if event not in seen:
            seen.append(event)
            remaining.pop(order, None)
        assert updated['active_order_ids'] == list(remaining)
        assert updated['minutes_by_order'] == remaining
        assert updated['workload_minutes'] == sum(remaining.values())
        assert updated['processed_cancellation_ids'] == seen
        assert process_cancellation(updated, order, event) == updated
        p = updated


BAD = [None, '', ' ', '7', True, False, -1, float('nan'), float('inf'), -float('inf'), [], {}, [None]]


@pytest.mark.parametrize('field', ['order_id', 'restaurant_id', 'destination_zone', 'prep_minutes', 'partner_id', 'zone', 'capacity', 'active_order_ids', 'workload_minutes', 'now', 'leg1', 'leg2'])
def test_field_mutation_never_crashes(field):
    for bad in BAD:
        order, partner = new_order('O', 'R', 'D'), new_partner('P', 'Z')
        travel = {('Z', 'R'): 1, ('R', 'D'): 2}
        now = 0
        if field in order:
            order[field] = bad
        elif field in partner:
            partner[field] = bad
        elif field == 'now':
            now = bad
        else:
            travel[('Z', 'R') if field == 'leg1' else ('R', 'D')] = bad
        result = assign_order(order, [partner], travel, now)
        if result['partner_id'] is not None:
            assert result['partner_id'] == partner['partner_id']
            assert isinstance(result['eta_minutes'], (int, float))
        assert result['reason']


def test_small_integer_eta_space():
    for now, leg1, workload, prep, leg2 in product(range(4), repeat=5):
        p = new_partner('P', 'Z')
        p['workload_minutes'] = workload
        result = estimate_eta(new_order('O', 'R', 'D', prep), p, {('Z', 'R'): leg1, ('R', 'D'): leg2}, now)
        assert result['eta_minutes'] == sum((now, leg1, workload, prep, leg2))
        assert result['pickup_minutes'] == now + leg1 + workload


def test_constructor_state_is_independent():
    a, b = new_partner('A', 'Z'), new_partner('B', 'Z')
    a['active_order_ids'].append('O')
    a['minutes_by_order']['O'] = 4
    a['processed_cancellation_ids'].append('E')
    assert b['active_order_ids'] == []
    assert b['minutes_by_order'] == {}
    assert b['processed_cancellation_ids'] == []


@pytest.mark.parametrize('field', ['partner_id', 'zone', 'active', 'capacity', 'active_order_ids', 'workload_minutes'])
def test_missing_partner_fields_rejected(field):
    p = new_partner('P', 'Z')
    del p[field]
    assert not estimate_eta(new_order('O', 'R', 'D'), p, {('Z', 'R'): 1, ('R', 'D'): 1})['eligible']


def test_eta_mixed_numeric_overflow_rejected():
    p = new_partner('P', 'Z')
    p['workload_minutes'] = 10**400
    result = estimate_eta(new_order('O', 'R', 'D'), p, {('Z', 'R'): 0.5, ('R', 'D'): 1})
    assert result['eligible'] is False and result['eta_minutes'] is None


def test_dataset_cancellation_stream():
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'records.json').read_text())
    partners = {p['partner_id']: deepcopy(p) for p in data['partners']}
    expected = deepcopy(partners)
    for event in data['cancellation_events']:
        pid, oid = event['partner_id'], event['order_id']
        # Dataset has no event IDs; synthesize a stable ID for each partner/order pair.
        eid = f'{pid}:{oid}'
        p = partners[pid]
        before = deepcopy(p)
        result = process_cancellation(p, oid, eid)
        assert p == before
        oracle = expected[pid]
        if oid in oracle['active_order_ids']:
            oracle['active_order_ids'].remove(oid)
            oracle['workload_minutes'] = max(0, oracle['workload_minutes'] - oracle['minutes_by_order'].pop(oid, 0))
        assert result['active_order_ids'] == oracle['active_order_ids']
        assert result['workload_minutes'] == oracle['workload_minutes']
        assert result['minutes_by_order'] == oracle['minutes_by_order']
        assert process_cancellation(result, oid, eid) == result
        partners[pid] = result
