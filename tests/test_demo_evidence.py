from copy import deepcopy
from demo_evidence import scenarios, run_scenario, decision_steps, verify_test_report
from decision_snapshot import capture_decision
from models import new_partner,new_order


def test_all_isolated_scenarios():
    for name in scenarios():
        result=run_scenario(name)
        assert result['passed'], result


def test_scenarios_deterministic():
    for name in scenarios():
        assert run_scenario(name)==run_scenario(name)


def test_decision_replay_does_not_mutate_input():
    partners=[new_partner('P-1','Z-1')]
    order=new_order('O-1','R-1','Z-2')
    travel={('Z-1','R-1'):3,('R-1','Z-2'):7}
    snap=capture_decision(order,partners,travel)
    original=deepcopy(snap)
    sections=decision_steps(snap)
    assert len(sections)==5
    assert sections[2]['rows'][0]['ETA']==20
    assert snap==original


def test_missing_evidence_is_not_marked_success(tmp_path):
    assert not verify_test_report(tmp_path/'missing.json')['ok']
