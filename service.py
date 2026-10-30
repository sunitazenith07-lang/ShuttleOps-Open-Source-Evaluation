from copy import deepcopy
import math


def is_valid_minutes(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def is_valid_identifier(value):
    return isinstance(value, str) and bool(value.strip())


def estimate_eta(order, partner, travel, now=0):
    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))
    prep=order.get('prep_minutes',0)
    workload=partner.get('workload_minutes',0)
    if (
        not is_valid_minutes(leg1)
        or not is_valid_minutes(leg2)
        or not is_valid_minutes(prep)
        or not is_valid_minutes(workload)
        or not is_valid_minutes(now)
    ):
        return {
            "partner_id": partner.get("partner_id"),
            "eta_minutes": None,
            "eligible": False,
        }
    pickup=now+leg1+workload
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':pickup+prep+leg2,'eligible':True}


def assign_order(order, partners, travel, now=0):
    if order.get('status') == 'CANCELLED':
        return {
            'order_id':order.get('order_id'),
            'partner_id':None,
            'eta_minutes':None,
            'reason':'order is cancelled',
        }
    if not all(
        is_valid_identifier(order.get(field))
        for field in ("order_id", "restaurant_id", "destination_zone")
    ):
        return {
            'order_id':order.get('order_id'),
            'partner_id':None,
            'eta_minutes':None,
            'reason':'invalid order data',
        }
    options=[]
    for partner in partners:
        if partner.get('active') is not True:
            continue
        capacity=partner.get('capacity')
        active_order_ids=partner.get('active_order_ids')
        if (
            not isinstance(capacity,int)
            or isinstance(capacity,bool)
            or capacity < 1
            or not isinstance(active_order_ids,list)
            or len(active_order_ids) >= capacity
        ):
            continue
        estimate=estimate_eta(order,partner,travel,now)
        if estimate['eligible']:
            options.append(estimate)
    if len(options)==0:
        return {'order_id':order.get('order_id'),'partner_id':None,'eta_minutes':None,'reason':'no eligible partner or missing time data'}
    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    out=deepcopy(partner)
    if not is_valid_identifier(event_id):
        return out
    out.setdefault('active_order_ids',[]); out.setdefault('processed_cancellation_ids',[])
    if event_id in out['processed_cancellation_ids']:
        return out
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes']=max(0,out.get('workload_minutes',0)-out.get('minutes_by_order',{}).get(order_id,0))
    out['processed_cancellation_ids'].append(event_id)
    return out
