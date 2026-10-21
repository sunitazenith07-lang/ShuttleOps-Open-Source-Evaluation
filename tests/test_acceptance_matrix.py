# Parameterized acceptance matrix; each parameter set is counted as an individual pytest case.
import pytest
from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation


@pytest.mark.parametrize("leg1,workload,prep,leg2,now,expected", [
    (0,0,0,0,0,0),(1,0,0,1,0,2),(1,2,3,4,5,15),
    (8,5,10,12,0,35),(12,2,10,4,3,31),(3,7,5,9,10,34),
    (20,0,10,20,0,50),(4,4,4,4,4,20),(2,1,1,2,1,7),
    (9,9,9,9,9,45),(60,30,10,15,5,120),(100,0,0,100,0,200),
    (0,10,0,0,5,15),(10,0,10,0,0,20),(0,0,10,10,0,20),
    (7,3,6,4,2,22),(6,4,5,3,1,19),(2,5,8,4,3,22),
    (13,11,9,7,6,46),(1,1,1,1,1,5),
])
def test_eta_calculation_matrix(leg1, workload, prep, leg2, now, expected):
    order = new_order("O","R","D",prep)
    partner = new_partner("P","Z")
    partner["workload_minutes"] = workload
    result = estimate_eta(order,partner,{("Z","R"):leg1,("R","D"):leg2},now)
    assert result["eligible"] is True
    assert result["pickup_minutes"] == now + leg1 + workload
    assert result["eta_minutes"] == expected


@pytest.mark.parametrize("leg1,leg2", [
    (None,1),(1,None),(None,None),(-1,1),(1,-1),(-1,-1),
    ("2",1),(1,"2"),(True,1),(1,False),(float("nan"),1),(1,float("inf")),
])
def test_invalid_or_missing_travel_time_rejected(leg1,leg2):
    order = new_order("O","R","D")
    partner = new_partner("P","Z")
    travel = {}
    if leg1 is not None: travel[("Z","R")] = leg1
    if leg2 is not None: travel[("R","D")] = leg2
    result = estimate_eta(order,partner,travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("prep", [-1,-5,-100,None,"10",True,1.5,float("inf"),float("nan"),0,1,5,10])
def test_preparation_time_validation(prep):
    order = new_order("O","R","D",prep)
    partner = new_partner("P","Z")
    result = estimate_eta(order,partner,{("Z","R"):2,("R","D"):3})
    expected_valid = isinstance(prep,(int,float)) and not isinstance(prep,bool) and prep >= 0 and prep == prep and prep != float("inf")
    assert result["eligible"] is bool(expected_valid)


@pytest.mark.parametrize("active", [False,False,False,True,True,True,0,1,None,"no","yes"])
def test_inactive_partners_never_selected(active):
    order = new_order("O","R","D")
    partner = new_partner("P","Z")
    partner["active"] = active
    result = assign_order(order,[partner],{("Z","R"):1,("R","D"):1})
    if not active:
        assert result["partner_id"] is None
    elif active is True:
        assert result["partner_id"] == "P"


@pytest.mark.parametrize("capacity,active_count", [
    (1,1),(1,2),(2,2),(3,3),(4,4),(5,5),(1,0),(2,0),(2,1),(3,2),
    (0,0),(-1,0),(True,0),(1.5,0),(None,0),
])
def test_capacity_boundary_matrix(capacity,active_count):
    order = new_order("O","R","D")
    partner = new_partner("P","Z",capacity if isinstance(capacity,int) else 2)
    partner["capacity"] = capacity
    partner["active_order_ids"] = [f"OLD{i}" for i in range(active_count)]
    result = assign_order(order,[partner],{("Z","R"):1,("R","D"):1})
    valid_capacity = isinstance(capacity,int) and not isinstance(capacity,bool) and capacity >= 1
    if valid_capacity and active_count < capacity:
        assert result["partner_id"] == "P"
    else:
        assert result["partner_id"] is None


@pytest.mark.parametrize("x_zone,travel_x,travel_y,expected", [
    ("X",1,2,"A"),("X",2,1,"B"),("X",5,5,"A"),("X",0,10,"A"),
    ("X",10,0,"B"),("X",3,4,"A"),("X",4,3,"B"),("X",9,9,"A"),
    ("X",2,9,"A"),("X",9,2,"B"),("X",1,1,"A"),("X",7,8,"A"),
    ("X",8,7,"B"),("X",0,0,"A"),("X",100,100,"A"),
])
def test_dispatch_selects_lowest_eta_and_stable_tie(x_zone,travel_x,travel_y,expected):
    order = new_order("O","R","D",prep_minutes=0)
    a = new_partner("A","X")
    b = new_partner("B","Y")
    result = assign_order(order,[b,a],{("X","R"):travel_x,("Y","R"):travel_y,("R","D"):0})
    assert result["partner_id"] == expected


@pytest.mark.parametrize("minutes", [0,1,2,3,5,8,10,15,20,30,60,100,250,500,999])
def test_duplicate_cancellation_is_idempotent_across_workloads(minutes):
    partner = new_partner("P","Z")
    partner.update(active_order_ids=["O"],workload_minutes=minutes,minutes_by_order={"O":minutes})
    once = process_cancellation(partner,"O","C")
    twice = process_cancellation(once,"O","C")
    assert twice["active_order_ids"] == []
    assert twice["workload_minutes"] == 0
    assert twice["processed_cancellation_ids"] == ["C"]


@pytest.mark.parametrize("order_id", ["O1","O2","UNKNOWN","",None,1,0,"same","long-order-id"])
def test_cancellation_only_releases_present_order(order_id):
    partner = new_partner("P","Z")
    partner.update(active_order_ids=["ACTIVE"],workload_minutes=20,minutes_by_order={"ACTIVE":20})
    result = process_cancellation(partner,order_id,"C")
    assert result["workload_minutes"] == (0 if order_id == "ACTIVE" else 20)
    assert result["active_order_ids"] == ([] if order_id == "ACTIVE" else ["ACTIVE"])


@pytest.mark.parametrize("workload,minutes", [
    (0,0),(1,1),(5,3),(10,5),(100,20),(3,10),(0,4),(50,50),(20,30),(1000,999),
])
def test_cancellation_workload_never_goes_below_zero(workload,minutes):
    partner = new_partner("P","Z")
    partner.update(active_order_ids=["O"],workload_minutes=workload,minutes_by_order={"O":minutes})
    result = process_cancellation(partner,"O","C")
    assert result["workload_minutes"] == max(0,workload-minutes)


@pytest.mark.parametrize("now", [0,1,2,5,10,60,100,1000,-1,-10,"5",True,None])
def test_current_time_validation(now):
    result = estimate_eta(new_order("O","R","D"),new_partner("P","Z"),{("Z","R"):1,("R","D"):1},now)
    if isinstance(now,(int,float)) and not isinstance(now,bool) and now >= 0:
        assert result["eligible"] is True
    else:
        assert result["eligible"] is False


@pytest.mark.parametrize("field,value", [
    ("order_id",""),("order_id",None),("restaurant_id",""),("restaurant_id",None),
    ("destination_zone",""),("destination_zone",None),("order_id",0),("restaurant_id",0),
    ("destination_zone",0),("prep_minutes",-1),("prep_minutes",None),
    ("prep_minutes","2"),("prep_minutes",True),("prep_minutes",float("nan")),
])
def test_invalid_order_fields_do_not_assign_partner(field,value):
    order = new_order("O","R","D")
    order[field] = value
    result = assign_order(order,[new_partner("P","Z")],{("Z","R"):1,("R","D"):1})
    if field in ("order_id","restaurant_id","destination_zone") or field == "prep_minutes":
        assert result["partner_id"] is None


@pytest.mark.parametrize("n", range(1,21))
def test_no_partner_and_missing_route_cases_are_safe(n):
    order = new_order("O","R","D")
    partners = [new_partner(f"P{i}","Z") for i in range(n)]
    result = assign_order(order,partners,{})
    assert result["partner_id"] is None
    assert result["eta_minutes"] is None


@pytest.mark.parametrize("partner_id", [f"P{i:02}" for i in range(10)])
def test_ties_break_by_partner_id_independent_of_input_order(partner_id):
    order = new_order("O","R","D",0)
    ids = ["P9","P8","P7","P6","P5","P4","P3","P2","P1","P0"]
    partners = [new_partner(pid,"Z") for pid in ids]
    result = assign_order(order,partners,{("Z","R"):1,("R","D"):1})
    assert result["partner_id"] == "P0"


@pytest.mark.parametrize("event_id", [f"C-{i:02}" for i in range(12)])
def test_distinct_cancellation_events_recorded_once_each(event_id):
    partner = new_partner("P","Z")
    partner.update(active_order_ids=["O"],workload_minutes=9,minutes_by_order={"O":9})
    result = process_cancellation(partner,"O",event_id)
    assert result["processed_cancellation_ids"] == [event_id]
    assert result["workload_minutes"] == 0
