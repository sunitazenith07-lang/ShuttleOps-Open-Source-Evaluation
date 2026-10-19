"""110-case visible ShuttleOps contract. Untouched starter intentionally has 24 failures."""
import json
from copy import deepcopy
import pytest
import service as service
from models import RECORD_CLASS, FIELD_NAMES, VALID_STATUSES, VALID_CATEGORIES
from service import load_records, save_records, find_record, search_records, filter_records, update_status, summary, book_seat
from fixtures import make_records

STATUS_CHECKS=["Scheduled","Delayed","Cancelled"]
CATEGORY_CHECKS=["Campus Loop","Airport","City","Night"]
SEARCH_CASES=[("North Loop Shuttle",[1]),("Airport Express",[2]),("Evening Circle",[3]),("Library Connector",[4]),("South Campus Connector",[5]),("Night Shuttle",[6]),("Central Hub",[1]),("City",[5])]
NORMALIZATION_CASES=[("north loop",[1]),("NORTH LOOP",[1]),(" North Loop ",[1]),("airport express",[2]),("CENTRAL HUB",[1]),("library connector",[4]),("Night Shuttle  ",[6]),(" campus loop",[1,4])]

@pytest.mark.parametrize("field",FIELD_NAMES)
def test_model_serialisation_preserves_each_field(field):
    row=make_records()[0]; assert row.to_dict()[field]==getattr(row,field)
@pytest.mark.parametrize("status",STATUS_CHECKS)
def test_supported_status_values_are_declared(status):
    assert status in VALID_STATUSES
@pytest.mark.parametrize("category",CATEGORY_CHECKS)
def test_supported_categories_are_declared(category):
    assert category in VALID_CATEGORIES
@pytest.mark.parametrize("size",[1,2,4,6])
def test_storage_round_trip(tmp_path,size):
    path=tmp_path/"nested"/"records.json"; expected=make_records()[:size]; save_records(expected,path)
    assert [x.to_dict() for x in load_records(path)]==[x.to_dict() for x in expected]
def test_missing_storage_returns_empty_list(tmp_path):
    assert load_records(tmp_path/"missing.json")==[]
def test_malformed_json_is_reported(tmp_path):
    path=tmp_path/"broken.json"; path.write_text("[broken",encoding="utf-8")
    with pytest.raises(json.JSONDecodeError): load_records(path)
def test_non_list_json_is_rejected(tmp_path):
    path=tmp_path/"bad.json"; path.write_text('{"not":"a list"}',encoding="utf-8")
    with pytest.raises(ValueError): load_records(path)
@pytest.mark.parametrize("record_id,expected",[(1,1),(2,2),(3,3),(6,6),(999,None)])
def test_find_record_by_id(record_id,expected):
    row=find_record(make_records(),record_id); assert (row.id if row else None)==expected
@pytest.mark.parametrize("category",CATEGORY_CHECKS)
def test_filter_by_each_category(category):
    assert [x.id for x in filter_records(make_records(),category=category)]==[x.id for x in make_records() if x.category==category]
@pytest.mark.parametrize("status",STATUS_CHECKS)
def test_filter_by_each_status(status):
    assert [x.id for x in filter_records(make_records(),status=status)]==[x.id for x in make_records() if x.status==status]
@pytest.mark.parametrize("category,status",[("Campus Loop","Scheduled"),("Airport","Delayed"),("Night","Cancelled"),("City","Delayed"),("Campus Loop","Cancelled"),("Airport","Scheduled")])
def test_combined_filters_return_intersection(category,status):
    assert [x.id for x in filter_records(make_records(),category=category,status=status)]==[x.id for x in make_records() if x.category==category and x.status==status]
@pytest.mark.parametrize("query,expected",SEARCH_CASES)
def test_exact_case_search(query,expected):
    assert [x.id for x in search_records(query,make_records())]==expected
@pytest.mark.parametrize("query,count",[("",6),(None,6)])
def test_empty_search_returns_all_records(query,count):
    assert len(search_records(query,make_records()))==count
@pytest.mark.parametrize("status",["Scheduled","Delayed","Cancelled","Scheduled"])
def test_update_status_mutates_explicit_list(status):
    rows=make_records(); changed=update_status(1,status,rows)
    assert changed.status==status and rows[0].status==status
@pytest.mark.parametrize("status",["NOT-VALID","","UNKNOWN-STATE"])
def test_invalid_status_update_is_rejected(status):
    with pytest.raises(ValueError): update_status(1,status,make_records())
def test_update_missing_record_is_rejected():
    with pytest.raises(LookupError): update_status(999,"Scheduled",make_records())
@pytest.mark.parametrize("status",STATUS_CHECKS)
def test_summary_status_buckets_are_correct(status):
    rows=make_records(); assert summary(rows)["by_status"][status]==sum(x.status==status for x in rows)
@pytest.mark.parametrize("category",CATEGORY_CHECKS)
def test_summary_category_buckets_are_correct(category):
    rows=make_records(); assert summary(rows)["by_category"][category]==sum(x.category==category for x in rows)
def test_summary_empty_catalogue():
    result=summary([]); assert result["total"]==0 and result["by_category"]=={}
    assert result["by_status"]=={s:0 for s in VALID_STATUSES}
def test_summary_does_not_mutate_inputs():
    rows=make_records(); before=[x.to_dict() for x in rows]; summary(rows)
    assert [x.to_dict() for x in rows]==before
@pytest.mark.parametrize("repeat",[1,2,3,4])
def test_domain_action_happy_path(repeat):
    rows=make_records(); count=rows[0].passengers; changed=book_seat(1,rows)
    assert changed.passengers==count+1 and rows[0].passengers==count+1
@pytest.mark.parametrize("case",[0,1,2,3])
def test_filtering_does_not_mutate_input(case):
    rows=make_records(); before=[x.to_dict() for x in rows]
    if case==0: filter_records(rows,category=CATEGORY_CHECKS[0])
    elif case==1: filter_records(rows,status=STATUS_CHECKS[0])
    elif case==2: filter_records(rows,query=SEARCH_CASES[0][0])
    else: filter_records(rows,category=CATEGORY_CHECKS[2],status=STATUS_CHECKS[1])
    assert [x.to_dict() for x in rows]==before
@pytest.mark.parametrize("size",[2,4,6])
def test_sample_subsets_have_unique_ids(size):
    ids=[x.id for x in make_records()[:size]]; assert len(ids)==len(set(ids))
def test_separate_storage_loads_return_distinct_objects(tmp_path):
    path=tmp_path/"records.json"; save_records(make_records(),path); one,two=load_records(path),load_records(path)
    assert one[0]==two[0] and one[0] is not two[0]
@pytest.mark.parametrize("case",[0,1])
def test_repeated_search_is_stable(case):
    rows=make_records(); before=[x.to_dict() for x in rows]
    filter_records(rows,query=SEARCH_CASES[case][0]); filter_records(rows,query=SEARCH_CASES[case][0])
    assert [x.to_dict() for x in rows]==before
@pytest.mark.parametrize("query",["NOT-A-REAL-RECORD-991","xxxxxxxxxx","987654321"])
def test_no_match_query_returns_empty_list(query):
    assert search_records(query,make_records())==[]

# Deliberate failures: 8 normalization, 4 persistence, 4 total, 4 data validation, 4 booking-safety cases.
@pytest.mark.parametrize("query,expected",NORMALIZATION_CASES)
def test_search_normalises_case_and_whitespace(query,expected):
    assert [x.id for x in search_records(query,make_records())]==expected
@pytest.mark.parametrize("status",["Scheduled","Delayed","Cancelled","Scheduled"])
def test_status_update_is_persisted(monkeypatch,status):
    rows=make_records(); saved=[]
    monkeypatch.setattr(service,"load_records",lambda:rows)
    monkeypatch.setattr(service,"save_records",lambda items,path=service.DATA_FILE:saved.append([x.to_dict() for x in items]))
    service.update_status(1,status)
    assert len(saved)==1 and saved[0][0]["status"]==status
@pytest.mark.parametrize("case",[0,1,2,3])
def test_summary_total_includes_cancelled_trips(case):
    rows=make_records(); terminal=next(x for x in rows if x.status=="Cancelled")
    other=[x for x in rows if x.status!="Cancelled"]; selected=[terminal]+other[:case]
    assert summary(selected)["total"]==len(selected)
@pytest.mark.parametrize("kind",["duplicate-id","invalid-status","invalid-category","negative-id"])
def test_storage_rejects_invalid_records(tmp_path,kind):
    row=make_records()[0].to_dict()
    if kind=="duplicate-id": payload=[row,deepcopy(row)]
    else:
        bad=deepcopy(row)
        if kind=="invalid-status": bad["status"]="Not A Status"
        elif kind=="invalid-category": bad["category"]="Not A Category"
        else: bad["id"]=-1
        payload=[bad]
    path=tmp_path/"invalid.json"; path.write_text(json.dumps(payload),encoding="utf-8")
    with pytest.raises(ValueError): load_records(path)
@pytest.mark.parametrize("case",[0,1,2,3])
def test_booking_rejects_unsafe_edge_cases(case):
    rows=make_records()
    if case==0: rows[0].passengers=rows[0].capacity
    elif case==1: rows[0].status="Cancelled"
    elif case==2: rows[0].capacity=0
    else: rows[0].passengers=rows[0].capacity+1
    with pytest.raises(ValueError): book_seat(1,records=rows)
