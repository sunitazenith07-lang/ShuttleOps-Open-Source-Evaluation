from models import new_order,new_partner
from service import estimate_eta,assign_order,process_cancellation


def test_eta_formula():
    o=new_order('O','R','D',10); p=new_partner('P','Z'); r=estimate_eta(o,p,{('Z','R'):8,('R','D'):12})
    assert r['eta_minutes']==30 and r['pickup_minutes']==8


def test_missing_travel_is_not_zero():
    r=estimate_eta(new_order('O','R','D'),new_partner('P','Z'),{})
    assert not r['eligible'] and r['eta_minutes'] is None


def test_inactive_partner_not_assigned():
    o=new_order('O','R','D'); p=new_partner('P','Z'); p['active']=False
    assert assign_order(o,[p],{('Z','R'):1,('R','D'):1})['partner_id'] is None


def test_full_partner_not_assigned():
    o=new_order('O','R','D'); p=new_partner('P','Z',1); p['active_order_ids']=['A']
    assert assign_order(o,[p],{('Z','R'):1,('R','D'):1})['partner_id'] is None


def test_lowest_eta_selected():
    o=new_order('O','R','D'); a=new_partner('A','X'); b=new_partner('B','Y')
    result=assign_order(o,[a,b],{('X','R'):1,('Y','R'):3,('R','D'):4})
    assert result['partner_id']=='A'


def test_tie_break_by_partner_id():
    o=new_order('O','R','D'); a=new_partner('A','X'); z=new_partner('Z','Y')
    result=assign_order(o,[z,a],{('X','R'):3,('Y','R'):3,('R','D'):4})
    assert result['partner_id']=='A'


def test_negative_prep_time_is_rejected():
    o=new_order('O','R','D',-5); p=new_partner('P','Z')
    assert assign_order(o,[p],{('Z','R'):1,('R','D'):1})['partner_id'] is None


def test_no_candidate_returns_reason():
    result=assign_order(new_order('O','R','D'),[],{})
    assert result['partner_id'] is None and result['reason']


def test_duplicate_cancellation_is_idempotent():
    p=new_partner('P','Z'); p.update(active_order_ids=['O1'],workload_minutes=9,minutes_by_order={'O1':9})
    once=process_cancellation(p,'O1','C1'); twice=process_cancellation(once,'O1','C1')
    assert twice['workload_minutes']==0 and twice['processed_cancellation_ids']==['C1']


def test_partner_without_valid_id_cannot_be_estimated():
    order=new_order('O','R','D')
    partner=new_partner('', 'Z')
    result=estimate_eta(order,partner,{('Z','R'):1,('R','D'):1})
    assert result['eligible'] is False and result['eta_minutes'] is None


def test_invalid_partner_workload_is_rejected():
    order=new_order('O','R','D')
    partner=new_partner('P','Z')
    partner['workload_minutes']=-1
    result=estimate_eta(order,partner,{('Z','R'):1,('R','D'):1})
    assert result['eligible'] is False and result['eta_minutes'] is None


def test_zero_duration_routes_are_valid():
    order=new_order('O','R','D',0)
    partner=new_partner('P','Z')
    result=estimate_eta(order,partner,{('Z','R'):0,('R','D'):0})
    assert result['eligible'] is True
    assert result['pickup_minutes']==0 and result['eta_minutes']==0


def test_cancellation_does_not_mutate_original_partner():
    partner=new_partner('P','Z')
    partner.update(active_order_ids=['O1'],workload_minutes=9,minutes_by_order={'O1':9})
    result=process_cancellation(partner,'O1','C1')
    assert partner['active_order_ids']==['O1'] and partner['workload_minutes']==9
    assert result['active_order_ids']==[] and result['workload_minutes']==0
