from copy import deepcopy

def is_valid_time(t):
    """Helper to validate time variables are valid numbers >= 0, rejecting bools, None, strings, NaNs, and inf."""
    return isinstance(t, (int, float)) and not isinstance(t, bool) and t >= 0 and t == t and t != float('inf')

def estimate_eta(order, partner, travel, now=0):
    if not order.get('order_id') or not order.get('restaurant_id') or not order.get('destination_zone'):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    prep = order.get('prep_minutes', 0)
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    
    if not (is_valid_time(now) and is_valid_time(prep) and is_valid_time(leg1) and is_valid_time(leg2)):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
        
    pickup = now + leg1 + partner.get('workload_minutes', 0)
    
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True
    }

def assign_order(order, partners, travel, now=0):
    options = []
    for partner in partners:
        if not partner.get('active', False):
            continue
        
        capacity = partner.get('capacity', 0)
        # Strict capacity validation: must be integer, not boolean, and >= 1
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue
            
        active_orders_count = len(partner.get('active_order_ids', []))
        if active_orders_count >= capacity:
            continue
            
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)
            
    if not options:
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }
        
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order.get('order_id'),
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