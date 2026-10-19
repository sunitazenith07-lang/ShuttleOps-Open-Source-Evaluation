"""Domain services for ShuttleOps."""
import json
from pathlib import Path
from models import RECORD_CLASS, VALID_STATUSES, VALID_CATEGORIES
DATA_FILE = Path(__file__).resolve().parent / "data" / "records.json"
def load_records(path=DATA_FILE):
    path=Path(path)
    if not path.exists(): return []
    with path.open("r", encoding="utf-8") as handle: payload=json.load(handle)
    if not isinstance(payload,list): raise ValueError("Record storage must contain a JSON list")
    return [RECORD_CLASS.from_dict(row) for row in payload]
def save_records(records,path=DATA_FILE):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+".tmp")
    with temp.open("w",encoding="utf-8") as handle:
        json.dump([x.to_dict() for x in records],handle,indent=2,ensure_ascii=False); handle.write("\n")
    temp.replace(path)
def find_record(records,record_id):
    return next((x for x in records if x.id==record_id),None)
def list_records(records=None):
    return load_records() if records is None else list(records)
def search_records(query,records=None):
    items=list_records(records); query="" if query is None else str(query)
    if not query: return items
    # Intentional starter bug: query matching isn't normalised.
    return [x for x in items if query in x.searchable_text]
def filter_records(records=None,query="",category=None,status=None):
    items=list_records(records)
    if category is not None and category not in VALID_CATEGORIES: raise ValueError(f"Invalid category: {category}")
    if status is not None and status not in VALID_STATUSES: raise ValueError(f"Invalid status: {status}")
    result=search_records(query,items)
    if category is not None: result=[x for x in result if x.category==category]
    if status is not None: result=[x for x in result if x.status==status]
    return result
def update_status(record_id,new_status,records=None):
    items=load_records() if records is None else records
    if new_status not in VALID_STATUSES: raise ValueError(f"Invalid status: {new_status}")
    item=find_record(items,record_id)
    if item is None: raise LookupError(f"Record {record_id} not found")
    item.status=new_status
    # Intentional starter bug: updated status is not persisted.
    return item
def summary(records=None):
    items=list_records(records)
    return {
        # Intentional starter bug: cancelled trips are omitted from the total.
        "total":sum(1 for x in items if x.status!="Cancelled"),
        "by_status":{s:sum(x.status==s for x in items) for s in VALID_STATUSES},
        "by_category":{c:sum(x.category==c for x in items) for c in sorted({x.category for x in items})},
    }
def book_seat(trip_id:int,records=None):
    items=load_records() if records is None else records
    trip=find_record(items,trip_id)
    if trip is None: raise LookupError(f"Trip {trip_id} not found")
    # Intentional starter bug: status and capacity safeguards are missing.
    trip.passengers+=1
    if records is None: save_records(items)
    return trip
def available_seats(trip,records=None):
    if trip.status=="Cancelled": return 0
    return max(0,trip.capacity-trip.passengers)
