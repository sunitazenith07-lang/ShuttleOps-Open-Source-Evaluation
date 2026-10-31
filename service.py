from copy import deepcopy
import math
# if not order.get('restaurant_id') or not order.get('destination_zone') or not partner.get('partner_id') or not partner.get('zone'):
#     return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None, 'eta_minutes': None, 'eligible': False}
    # if not order.get('restaurant_id') or not order.get('destination_zone') or not partner.get('partner_id') or not partner.get('zone'):
    #     return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    for k in (order.get('restaurant_id'), order.get('destination_zone'), partner.get('partner_id'), partner.get('zone')):
        if not isinstance(k, str) or not k.strip():
            return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))
    prep = order.get('prep_minutes', 0)
    workload = partner.get('workload_minutes', 0)
    #if leg1 is None or not isinstance(leg1, (int, float)) or isinstance(leg1, bool) or leg1 < 0 or leg2 is None or not isinstance(leg2, (int, float)) or isinstance(leg2, bool) or leg2 < 0 or prep is None or prep < 0 or workload is None or workload < 0 or now < 0:
        #return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    for t in (leg1, leg2, prep, workload, now):
        if t is None or not isinstance(t, (int, float)) or isinstance(t, bool) or not math.isfinite(t) or t < 0:
            return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    pickup=now+leg1+partner.get('workload_minutes',0)
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':pickup+order.get('prep_minutes',0)+leg2,'eligible':True}


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partners, list) or not isinstance(travel, dict):
        return {'order_id': order.get('order_id') if isinstance(order, dict) else None, 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
    # if not order.get('order_id'):
    #     return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
    if not isinstance(order.get('order_id'), str) or not order.get('order_id').strip():
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
    options=[]
    for partner in partners:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue
        capacity = partner.get('capacity', 0)
        active_orders = partner.get('active_order_ids', [])
        # if len(active_orders) >= capacity:
        #     continue
        if not isinstance(capacity, int) or isinstance(capacity, bool) or not isinstance(active_orders, list) or len(active_orders) >= capacity:
            continue
        # Starter is intentionally incomplete: active/capacity/time validation is missing.
        estimate=estimate_eta(order,partner,travel,now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return {'order_id':order.get('order_id'),'partner_id':None,'eta_minutes':None,'reason':'no eligible partner or missing time data'}
    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return {}
    out=deepcopy(partner); out.setdefault('active_order_ids',[]); out.setdefault('processed_cancellation_ids',[])
    # Starter defect: event_id is recorded but not checked before applying the event.
    if event_id in out['processed_cancellation_ids']:
        return out
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes']=max(0,out.get('workload_minutes',0)-out.get('minutes_by_order',{}).get(order_id,0))
    out['processed_cancellation_ids'].append(event_id)
    return out
