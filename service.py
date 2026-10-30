import math
from copy import deepcopy

def is_valid_time(value):
    """Helper: Checks if the time value is a valid non-negative integer or float."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    if math.isnan(value) or math.isinf(value):
        return False
    if value < 0:
        return False
    return True

def estimate_eta(order, partner, travel, now=0):
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    prep_time = order.get('prep_minutes', 0)
    
    # Validation checks for all time-related inputs
    if not is_valid_time(leg1) or not is_valid_time(leg2) or not is_valid_time(prep_time) or not is_valid_time(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    pickup = now + leg1 + partner.get('workload_minutes', 0)
    
    return {
        'partner_id': partner.get('partner_id'), 
        'pickup_minutes': pickup, 
        'eta_minutes': pickup + prep_time + leg2, 
        'eligible': True
    }

def assign_order(order, partners, travel, now=0):
    order_id = order.get('order_id')
    prep_minutes = order.get('prep_minutes')
    
    # Validate order ID format
    if not order_id or not isinstance(order_id, str):
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order_id'}
    
    # Validate time properties on the main order assignment level
    if not is_valid_time(prep_minutes):
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid prep time'}
    if not is_valid_time(now):
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid current time'}

    options = []
    for partner in partners:
        # Check partner active status strictly
        if partner.get('active') is not True:
            continue
            
        # Validate partner capacity
        capacity = partner.get('capacity')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue
            
        active_orders = len(partner.get('active_order_ids', []))
        if active_orders >= capacity:
            continue
            
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)
            
    if not options:
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
        
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    
    return {
        'order_id': order_id, 
        'partner_id': chosen['partner_id'], 
        'pickup_minutes': chosen['pickup_minutes'], 
        'eta_minutes': chosen['eta_minutes'], 
        'reason': 'assigned'
    }

def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    
    if event_id in out['processed_cancellation_ids']:
        return out
        
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(0, out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0))
        
    out['processed_cancellation_ids'].append(event_id)
    return out