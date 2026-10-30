from copy import deepcopy

# Helper function to strictly validate numbers (rejects True/False, strings, NaN, infinity)
def is_valid_num(val):
    return (isinstance(val, (int, float)) 
            and not isinstance(val, bool) 
            and val >= 0 
            and val == val 
            and val != float("inf"))

def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': None, 'eta_minutes': None, 'eligible': False}

    # Validate IDs (rejects None, 0, and empty strings)
    if not order.get('order_id') or not order.get('restaurant_id') or not order.get('destination_zone'):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # Validate prep time and current time 'now'
    prep_time = order.get('prep_minutes', 0)
    if not is_valid_num(prep_time) or not is_valid_num(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # Validate travel times
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    
    if not is_valid_num(leg1) or not is_valid_num(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
        
    # Validate workload
    workload = partner.get('workload_minutes', 0)
    if not is_valid_num(workload):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    eta = pickup + prep_time + leg2
    
    return {
        'partner_id': partner.get('partner_id'), 
        'pickup_minutes': pickup, 
        'eta_minutes': eta, 
        'eligible': True
    }

def assign_order(order, partners, travel, now=0):
    if not order or not isinstance(order, dict) or not partners or not isinstance(partners, list):
        return {
            'order_id': order.get('order_id') if isinstance(order, dict) else None, 
            'partner_id': None, 
            'eta_minutes': None, 
            'reason': 'Invalid input or no partners available'
        }

    options = []
    for partner in partners:
        if not isinstance(partner, dict): 
            continue
            
        if not partner.get('active', False):
            continue
            
        # Validate capacity (must be an int >= 1, rejects bools, floats, None)
        capacity = partner.get('capacity', 2)
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue
            
        current_orders = len(partner.get('active_order_ids', []))
        if current_orders >= capacity:
            continue
            
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)
            
    if not options:
        return {
            'order_id': order.get('order_id'), 
            'partner_id': None, 
            'eta_minutes': None, 
            'reason': 'No eligible partners found'
        }
        
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    
    return {
        'order_id': order.get('order_id'), 
        'partner_id': chosen['partner_id'], 
        'pickup_minutes': chosen['pickup_minutes'], 
        'eta_minutes': chosen['eta_minutes']
    }

def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return partner

    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    
    # Idempotency: if event already processed, do nothing
    if event_id in out['processed_cancellation_ids']:
        return out
        
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        
        # Look up the specific workload for this order in 'minutes_by_order'
        minutes_to_deduct = 0
        minutes_dict = out.get('minutes_by_order', {})
        if isinstance(minutes_dict, dict) and order_id in minutes_dict:
            minutes_to_deduct = minutes_dict[order_id]
            
        if not is_valid_num(minutes_to_deduct):
            minutes_to_deduct = 0
            
        current_workload = out.get('workload_minutes', 0)
        if not is_valid_num(current_workload):
            current_workload = 0
            
        # Ensure workload never drops below zero
        out['workload_minutes'] = max(0, current_workload - minutes_to_deduct)
        out['processed_cancellation_ids'].append(event_id)
        
    return out