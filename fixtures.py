"""Deterministic sample records for ShuttleOps."""
from copy import deepcopy
from models import RECORD_CLASS
_SAMPLE=[
{"id":1,"route_name":"North Loop Shuttle","origin":"North Gate","destination":"Central Hub","stops":["North Gate","Library","Central Stop"],"departure_time":"09:00","capacity":30,"passengers":12,"status":"Scheduled","category":"Campus Loop"},
{"id":2,"route_name":"Airport Express","origin":"Main Gate","destination":"Airport","stops":["Main Gate","Central Stop","Airport"],"departure_time":"11:00","capacity":20,"passengers":20,"status":"Delayed","category":"Airport"},
{"id":3,"route_name":"Evening Circle","origin":"Student Housing","destination":"North Gate","stops":["Student Housing","Sports Centre","North Gate"],"departure_time":"18:00","capacity":35,"passengers":8,"status":"Cancelled","category":"Night"},
{"id":4,"route_name":"Library Connector","origin":"South Campus","destination":"Library","stops":["South Campus","Central Stop","Library"],"departure_time":"10:00","capacity":25,"passengers":9,"status":"Scheduled","category":"Campus Loop"},
{"id":5,"route_name":"South Campus Connector","origin":"North Gate","destination":"South Campus","stops":["North Gate","Central Stop","South Campus"],"departure_time":"13:30","capacity":25,"passengers":25,"status":"Delayed","category":"City"},
{"id":6,"route_name":"Night Shuttle","origin":"Library","destination":"Student Housing","stops":["Library","Sports Centre","Student Housing"],"departure_time":"22:00","capacity":40,"passengers":5,"status":"Cancelled","category":"Night"}]
def make_records():
    return [RECORD_CLASS.from_dict(row) for row in deepcopy(_SAMPLE)]
