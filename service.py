from collections.abc import Mapping
from copy import deepcopy
from math import isfinite


def valid_id(value):
    return isinstance(value,str) and bool(value.strip())


def valid_minutes(value):
    return (
        not isinstance(value,bool)
        and isinstance(value,(int,float))
        and isfinite(value)
        and value >= 0
    )

def estimate_eta(order,partner,travel,now=0):
    partner_id=partner.get('partner_id') if isinstance(partner,Mapping) else None

    if not (
        isinstance(order,Mapping)
        and isinstance(partner,Mapping)
        and isinstance(travel,Mapping)
        and all(valid_id(x) for x in [
            order.get('order_id'),order.get('restaurant_id'),
            order.get('destination_zone'),partner.get('partner_id'),
            partner.get('zone')
        ])
        and all(valid_minutes(x) for x in [
            order.get('prep_minutes'),partner.get('workload_minutes'),now
        ])
    ):
        return {'partner_id': partner_id,'eta_minutes': None,'eligible': False}

    leg1=travel.get((partner['zone'],order['restaurant_id']))
    leg2=travel.get((order['restaurant_id'],order['destination_zone']))

    if not valid_minutes(leg1) or not valid_minutes(leg2):
        return {'partner_id': partner_id,'eta_minutes': None,'eligible': False}

    pickup=now+leg1+partner['workload_minutes']
    eta=pickup+order['prep_minutes']+leg2

    if not valid_minutes(pickup) or not valid_minutes(eta):
        return {'partner_id': partner_id,'eta_minutes': None,'eligible': False}

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True
    }


def assign_order(order,partners,travel,now=0):
    options=[]
    if isinstance(partners,(list,tuple)):
        for partner in partners:
            if not isinstance(partner,Mapping):
                continue
            ids=partner.get('active_order_ids')
            capacity=partner.get('capacity')
            if (
                partner.get('active') is not True
                or not isinstance(ids,list)
                or any(not valid_id(x) for x in ids)
                or len(ids) != len(set(ids))
                or isinstance(capacity,bool)
                or not isinstance(capacity,int)
                or capacity < 1
                or len(ids) >= capacity
            ):
                continue

            estimate=estimate_eta(order,partner,travel,now)
            if estimate['eligible']:
                options.append(estimate)
    if not options:
        return {'order_id': order.get('order_id') if isinstance(order,Mapping) else None,'partner_id': None,'eta_minutes': None,'reason': 'no eligible partner or missing time data'}

    chosen=min(options,key=lambda x: (x['eta_minutes'],x['partner_id']))

    return {
        'order_id': order['order_id'],
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner,order_id,event_id):
    out=deepcopy(dict(partner)) if isinstance(partner,Mapping) else {}

    ids=out.get('active_order_ids')
    ids=[x for x in ids if valid_id(x)] if isinstance(ids,list) else []
    out['active_order_ids']=ids

    processed=out.get('processed_cancellation_ids')
    processed=list(dict.fromkeys(
        x for x in processed if valid_id(x)
    )) if isinstance(processed,list) else []
    out['processed_cancellation_ids']=processed

    minutes=out.get('minutes_by_order')
    minutes={
        k: v for k,v in minutes.items()
        if valid_id(k) and valid_minutes(v)
    } if isinstance(minutes,Mapping) else {}
    out['minutes_by_order']=minutes

    workload=out.get('workload_minutes')
    if not valid_minutes(workload):
        workload=0
    out['workload_minutes']=workload

    if not valid_id(event_id) or event_id in processed or not valid_id(order_id):
        return out

    if order_id in ids:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes']=max(0,workload - minutes.get(order_id,0))
        minutes.pop(order_id,None)

    processed.append(event_id)
    return out