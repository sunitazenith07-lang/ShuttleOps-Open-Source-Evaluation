from models import new_order,new_partner
from service import estimate_eta,assign_order


def test_eta_formula():
    o=new_order('O','R','D',10); p=new_partner('P','Z'); r=estimate_eta(o,p,{('Z','R'):8,('R','D'):12})
    assert r['eta_minutes']==30 and r['pickup_minutes']==8


def test_missing_travel_is_not_zero():
    r=estimate_eta(new_order('O','R','D'),new_partner('P','Z'),{})
    assert not r['eligible'] and r['eta_minutes'] is None


def test_lowest_eta_selected():
    o=new_order('O','R','D'); a=new_partner('A','X'); b=new_partner('B','Y')
    result=assign_order(o,[a,b],{('X','R'):1,('Y','R'):3,('R','D'):4})
    assert result['partner_id']=='A'


def test_tie_break_by_id():
    o=new_order('O','R','D'); a=new_partner('A','X'); z=new_partner('Z','Y')
    result=assign_order(o,[z,a],{('X','R'):3,('Y','R'):3,('R','D'):4})
    assert result['partner_id']=='A'


def test_no_candidate_has_reason():
    result=assign_order(new_order('O','R','D'),[],{})
    assert result['partner_id'] is None and result['reason']
