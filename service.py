from copy import deepcopy
import math


def _is_valid_non_negative_finite(val):
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    if val < 0:
        return False
    if isinstance(val, int):
        return True
    return math.isfinite(val)


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_non_negative_finite(now):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    prep=order.get('prep_minutes')
    if not _is_valid_non_negative_finite(prep):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))
    if not _is_valid_non_negative_finite(leg1) or not _is_valid_non_negative_finite(leg2):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_finite(workload):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    # Issue 4: Wrap arithmetic in try/except OverflowError; validate computed results are finite.
    try:
        pickup = now + leg1 + workload
        eta_minutes = pickup + prep + leg2
    except OverflowError:
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    if not _is_valid_non_negative_finite(pickup) or not _is_valid_non_negative_finite(eta_minutes):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':eta_minutes,'eligible':True}


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order data'}
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        val = order.get(field)
        if not isinstance(val, str) or not val.strip():
            return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': f'invalid {field}'}
    prep = order.get('prep_minutes')
    if not _is_valid_non_negative_finite(prep):
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid prep_minutes'}

    if not isinstance(partners, (list, tuple, set)):
        partners = []
    if not isinstance(travel, dict):
        travel = {}

    options=[]
    for partner in partners:
        if not isinstance(partner, dict) or partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue
        # Issue 1: If active_order_ids is present but not a list/tuple/set (e.g. None or str),
        # skip the partner (treat as ineligible). A missing key defaults to [] (valid, zero orders).
        if 'active_order_ids' in partner:
            active_orders = partner['active_order_ids']
            if not isinstance(active_orders, (list, tuple, set)):
                continue
        else:
            active_orders = []
        active_count = len(active_orders)
        if active_count >= capacity:
            continue
        # Issue 3: Validate partner_id is a non-empty string before ETA estimation.
        pid = partner.get('partner_id')
        if not isinstance(pid, str) or not pid.strip():
            continue
        estimate=estimate_eta(order,partner,travel,now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return {'order_id':order.get('order_id'),'partner_id':None,'eta_minutes':None,'reason':'no eligible partner or missing time data'}
    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    out=deepcopy(partner) if isinstance(partner, dict) else {}
    out.setdefault('active_order_ids',[])
    out.setdefault('processed_cancellation_ids',[])
    # Issue 5: Validate event_id is a non-empty string before processing.
    if not isinstance(event_id, str) or not event_id.strip():
        return out
    # Duplicate-event idempotency guard.
    if event_id in out['processed_cancellation_ids']:
        return out
    # Issue 2: Validate active_order_ids; if not a list, skip mutation safely.
    active_order_ids = out.get('active_order_ids')
    if not isinstance(active_order_ids, list):
        # Cannot remove from a malformed field; still record event if valid.
        out['processed_cancellation_ids'].append(event_id)
        return out
    if order_id in active_order_ids:
        active_order_ids.remove(order_id)
        # Issue 2: Validate minutes_by_order; treat as 0 if not a dict.
        minutes_by_order = out.get('minutes_by_order')
        released = minutes_by_order.get(order_id, 0) if isinstance(minutes_by_order, dict) else 0
        # Issue 2: Validate workload_minutes; treat as 0 if not a valid non-negative numeric.
        workload = out.get('workload_minutes', 0)
        if not _is_valid_non_negative_finite(workload):
            workload = 0
        out['workload_minutes'] = max(0, workload - released)
    out['processed_cancellation_ids'].append(event_id)
    return out
