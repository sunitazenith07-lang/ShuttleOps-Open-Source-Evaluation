from copy import deepcopy
import math  # using this to check if numbers are valid

def estimate_eta(order, partner, travel, now=0):
    # checking if we got the right kind of input
    if not isinstance(order,dict) or not isinstance(partner,dict) or not isinstance(travel,dict):
        return {'partner_id':partner.get('partner_id') if isinstance(partner,dict) else None,'eta_minutes':None,'eligible':False}

    # making sure the important IDs and zones are not missing or empty
    if not all(isinstance(order.get(k),str) and order.get(k).strip() for k in ('order_id','restaurant_id','destination_zone')) or not isinstance(partner.get('partner_id'),str) or not isinstance(partner.get('zone'),str):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}

    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))

    # putting all the time values together so we can check them
    times=[leg1,leg2,order.get('prep_minutes',0),partner.get('workload_minutes',0),now]

    # making sure none of the times are negative or invalid
    if any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or x<0 for x in times):
        return {'partner_id':partner.get('partner_id'),'eta_minutes':None,'eligible':False}

    pickup=now+leg1+partner.get('workload_minutes',0)
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':pickup+order.get('prep_minutes',0)+leg2,'eligible':True}


def assign_order(order, partners, travel, now=0):
    # checking if the order and partners list are in the right format
    if not isinstance(order,dict) or not isinstance(partners,list):
        return {'order_id':None,'partner_id':None,'eta_minutes':None,'reason':'invalid input'}

    options=[]
    for partner in partners:
        # skipping partners that are not valid or are not active
        if not isinstance(partner,dict) or partner.get('active') is not True:
            continue

        capacity=partner.get('capacity')
        active_orders=partner.get('active_order_ids')

        # skipping partners who have invalid capacity or already have too many orders
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1 or not isinstance(active_orders,list) or len(active_orders)>=capacity:
            continue

        estimate=estimate_eta(order,partner,travel,now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return {'order_id':order.get('order_id'),'partner_id':None,'eta_minutes':None,'reason':'no eligible partner or missing time data'}

    chosen=min(options,key=lambda item:(item['eta_minutes'],str(item['partner_id'])))
    return {'order_id':order.get('order_id'),'partner_id':chosen['partner_id'],'pickup_minutes':chosen['pickup_minutes'],'eta_minutes':chosen['eta_minutes'],'reason':'assigned'}


def process_cancellation(partner, order_id, event_id):
    out=deepcopy(partner)
    out.setdefault('active_order_ids',[])
    out.setdefault('processed_cancellation_ids',[])

    # checking if we have already handled this cancellation
    if event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)

        minutes=out.get('minutes_by_order',{}).get(order_id,0)
        workload=out.get('workload_minutes',0)

        # only changing the workload if both values are valid numbers
        if isinstance(minutes,(int,float)) and not isinstance(minutes,bool) and math.isfinite(minutes) and minutes>=0 and isinstance(workload,(int,float)) and not isinstance(workload,bool) and math.isfinite(workload) and workload>=0:
            # making sure the workload doesn't go below zero
            out['workload_minutes']=max(0,workload-minutes)

    # saving the event id so we dont process it again
    out['processed_cancellation_ids'].append(event_id)
    return out