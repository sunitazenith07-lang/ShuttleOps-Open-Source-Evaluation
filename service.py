from copy import deepcopy


def estimate_eta(order, partner, travel, now=0):
    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))
    if leg1 is None or leg2 is None:
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}
    pickup=now+leg1+partner.get('workload_minutes',0)
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':pickup+order.get('prep_minutes',0)+leg2,'eligible':True}


def assign_order(order, partners, travel, now=0):
    options=[]
    for partner in partners:
        # Starter is intentionally incomplete: active/capacity/time validation is missing.
        estimate=estimate_eta(order,partner,travel,now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return {'order_id':order.get('order_id'),'partner_id':None,'eta_minutes':None,'reason':'no eligible partner or missing time data'}
    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    out=deepcopy(partner); out.setdefault('active_order_ids',[]); out.setdefault('processed_cancellation_ids',[])
    # Starter defect: event_id is recorded but not checked before applying the event.
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes']=max(0,out.get('workload_minutes',0)-out.get('minutes_by_order',{}).get(order_id,0))
    out['processed_cancellation_ids'].append(event_id)
    return out
