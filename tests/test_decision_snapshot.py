"""Presentation snapshot regression coverage; no Streamlit dependency."""
from copy import deepcopy
from models import new_order, new_partner
from decision_snapshot import capture_decision


def sample():
    order = new_order('O-1', 'R-1', 'Z-9', 12)
    partners = [new_partner('P-1', 'Z-1', 1), new_partner('P-2', 'Z-2', 2)]
    travel = {('Z-1', 'R-1'): 8, ('Z-2', 'R-1'): 8, ('R-1', 'Z-9'): 10}
    return order, partners, travel


def test_snapshot_does_not_mutate_inputs():
    order, partners, travel = sample()
    before = deepcopy((order, partners, travel))
    snapshot = capture_decision(order, partners, travel)
    assert snapshot['report']['decision']['partner_id'] == 'P-1'
    assert (order, partners, travel) == before


def test_replay_survives_capacity_change():
    order, partners, travel = sample()
    snapshot = capture_decision(order, partners, travel)
    partners[0]['active_order_ids'].append('O-1')
    assert snapshot['context']['partners'][0]['active_order_ids'] == []
    assert snapshot['report']['candidates'][0]['status'] == 'SELECTED'
    assert snapshot['report']['decision']['partner_id'] == 'P-1'


def test_snapshots_are_deterministic():
    order, partners, travel = sample()
    one = capture_decision(order, partners, travel)
    two = capture_decision(deepcopy(order), deepcopy(partners), deepcopy(travel))
    assert one == two
