from copy import deepcopy
from math import isfinite


def is_valid_time(value):
    """True for a real, finite, non-negative number (bool is not a time)."""
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value) and value>=0


def is_valid_id(value):
    """True for a string that is not empty once whitespace is stripped."""
    return isinstance(value,str) and bool(value.strip())


def validate_order(order):
    """Return a reason string if the order is invalid, else None."""
    if not isinstance(order,dict):
        return 'order is malformed'
    for field in ('order_id','restaurant_id','destination_zone'):
        if not is_valid_id(order.get(field)):
            return f'invalid {field}'
    if not is_valid_time(order.get('prep_minutes')):
        return 'invalid prep_minutes'
    return None


def ineligible(partner, reason):
    """Build the result for a partner that cannot get a reliable ETA."""
    return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False,'reason':reason}

def compute_eta(now, to_restaurant, workload, prep, to_customer):
    """Return (pickup, eta) in minutes.

    pickup = now + partner-to-restaurant travel + remaining workload
    eta = pickup + restaurant preparation + restaurant-to-customer travel
    """
    pickup=now+to_restaurant+workload
    return pickup,pickup+prep+to_customer


def estimate_eta(order, partner, travel, now=0):
    reason=validate_order(order)
    if reason is None and not is_valid_time(now):
        reason='invalid current time'
    if reason:
        return ineligible(partner,reason)
    zone=partner.get('zone')
    if not is_valid_id(zone):
        return ineligible(partner,'invalid zone')
    leg1=travel.get((zone,order['restaurant_id']))
    leg2=travel.get((order['restaurant_id'],order['destination_zone']))
    if leg1 is None or leg2 is None:
        return ineligible(partner,'missing travel time')
    if not (is_valid_time(leg1) and is_valid_time(leg2)):
        return ineligible(partner,'invalid travel time')
    workload=partner.get('workload_minutes',0)
    if not is_valid_time(workload):
        return ineligible(partner,'invalid workload_minutes')
    pickup,eta=compute_eta(now,leg1,workload,order['prep_minutes'],leg2)
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':eta,'eligible':True}


def is_valid_capacity(value):
    """True for a whole number of order slots, at least 1 (bool is not a count)."""
    return isinstance(value,int) and not isinstance(value,bool) and value>=1


def availability_reason(partner):
    """Return why a partner cannot take a new order, or None if available."""
    if not isinstance(partner,dict):
        return 'malformed partner record'
    if not is_valid_id(partner.get('partner_id')):
        return 'invalid partner_id'
    if partner.get('active') is not True:
        return 'inactive'
    capacity=partner.get('capacity')
    if not is_valid_capacity(capacity):
        return 'invalid capacity'
    current=partner.get('active_order_ids')
    if not isinstance(current,list):
        return 'invalid active_order_ids'
    if len(current)>=capacity:
        return 'at capacity'
    return None

def partner_label(partner):
    """Readable partner name for reasons; tolerates malformed records."""
    return str(partner.get('partner_id')) if isinstance(partner,dict) else 'unknown partner'

def unassigned(order, reason):
    """Build the result for an order that was left unassigned."""
    order_id=order.get('order_id') if isinstance(order,dict) else None
    return {'order_id':order_id,'partner_id':None,'eta_minutes':None,'reason':reason}

def assign_order(order, partners, travel, now=0):
    problem=validate_order(order)
    if problem is not None:
        return unassigned(order,f'order rejected: {problem}')
    partners=partners if isinstance(partners,(list,tuple)) else []
    travel=travel if isinstance(travel,dict) else {}
    options=[]
    excluded=[]
    for partner in partners:
        reason=availability_reason(partner)
        if reason is None:
            estimate=estimate_eta(order,partner,travel,now)
            if estimate['eligible']:
                options.append(estimate)
                continue
            reason=estimate['reason']
        excluded.append(f'{partner_label(partner)}: {reason}')
    if not options:
        summary='; '.join(sorted(excluded)) or 'no partners supplied'
        return unassigned(order,f'no eligible partner ({summary})')

    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    out=deepcopy(partner); out.setdefault('active_order_ids',[]); out.setdefault('processed_cancellation_ids',[])
    has_event_id=is_valid_id(event_id)
    if has_event_id and event_id in out['processed_cancellation_ids']:
        return out
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes']=max(0,out.get('workload_minutes',0)-out.get('minutes_by_order',{}).get(order_id,0))
    if has_event_id:
        out['processed_cancellation_ids'].append(event_id)
    return out
