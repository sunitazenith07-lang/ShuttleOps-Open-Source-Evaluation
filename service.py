import math
from copy import deepcopy

def _is_valid_time(val):
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    if math.isnan(val) or math.isinf(val) or val < 0:
        return False
    return True

def estimate_eta(order, partner, travel, now=0):
    p_id = partner.get('partner_id') if isinstance(partner, dict) else None
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    
    o_id = order.get('order_id')
    if o_id is None or o_id == '' or o_id == 0:
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_time(order.get('prep_minutes')) or not _is_valid_time(now):
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    
    if 'partner_id' not in partner or 'zone' not in partner:
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    if 'active' in partner and not isinstance(partner['active'], bool):
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
        
    if not partner.get('active', True):
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    
    if 'capacity' in partner:
        capacity = partner['capacity']
        if capacity is None or isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
            return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
            
    active_orders = partner.get('active_order_ids', [])
    capacity_limit = partner.get('capacity', 2)
    if len(active_orders) >= capacity_limit:
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    
    if leg1 is None or leg2 is None:
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_time(leg1) or not _is_valid_time(leg2):
        return {'partner_id': p_id, 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + partner.get('workload_minutes', 0)
    return {
        'partner_id': p_id,
        'pickup_minutes': pickup,
        'eta_minutes': pickup + order.get('prep_minutes', 0) + leg2,
        'eligible': True
    }

def assign_order(order, partners, travel, now=0):
    
    if not isinstance(order, dict) or not _is_valid_time(now) or not isinstance(travel, dict):
        o_id = order.get('order_id') if isinstance(order, dict) else None
        return {
            'order_id': o_id if o_id not in (0, '', None) else None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }
        
    o_id = order.get('order_id')
    if o_id is None or o_id == '' or o_id == 0:
        return {
            'order_id': None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }

    options = []
    for partner in partners:
        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get('eligible') and estimate.get('eta_minutes') is not None:
            options.append(estimate)
            
    if not options:
        return {
            'order_id': o_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }
        
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': o_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }

def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    out.setdefault('minutes_by_order', {})
    
    if event_id is None or order_id is None:
        return out
        
    if event_id in out['processed_cancellation_ids']:
        return out
        
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(0, out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0))
        
    out['processed_cancellation_ids'].append(event_id)
    return out
