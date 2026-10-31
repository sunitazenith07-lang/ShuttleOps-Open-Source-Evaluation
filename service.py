def estimate_eta(order, partner, travel, now=0):
    """
    Calculate ETA for a partner-order combination.
    Returns eligible=False if any validation fails.
    Returns eligible=True with calculated ETA if all inputs are valid.
    """
    # Validate now parameter - must be non-negative number
    if not isinstance(now, (int, float)) or isinstance(now, bool):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if now < 0 or now != now or now == float('inf'):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    # Validate order prep time
    prep_minutes = order.get('prep_minutes')
    if prep_minutes is None:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not isinstance(prep_minutes, (int, float)) or isinstance(prep_minutes, bool):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if prep_minutes < 0 or prep_minutes != prep_minutes or prep_minutes == float('inf'):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    # Get travel times
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    
    # Check travel times exist
    if leg1 is None or leg2 is None:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    # Validate travel times
    if not isinstance(leg1, (int, float)) or isinstance(leg1, bool):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not isinstance(leg2, (int, float)) or isinstance(leg2, bool):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if leg1 < 0 or leg2 < 0:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if leg1 != leg1 or leg2 != leg2:  # NaN check
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if leg1 == float('inf') or leg2 == float('inf'):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    # Get partner workload
    workload = partner.get('workload_minutes', 0)
    if not isinstance(workload, (int, float)) or isinstance(workload, bool):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if workload < 0:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    
    # All validations passed - calculate ETA
    pickup = now + leg1 + workload
    eta = pickup + prep_minutes + leg2
    
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True  # FIXED: Was False, should be True
    }


def assign_order(order, partners, travel, now=0):
    """
    Assign order to best eligible partner.
    Returns partner_id or None with reason.
    Always returns eta_minutes field (None if no assignment).
    """
    # Validate order fields
    if not is_valid_order(order):
        return {'partner_id': None, 'eta_minutes': None, 'reason': 'Invalid order fields'}
    
    # Validate travel data
    if not travel or not isinstance(travel, dict):
        return {'partner_id': None, 'eta_minutes': None, 'reason': 'Invalid travel data'}
    
    # Validate now parameter
    if not isinstance(now, (int, float)) or isinstance(now, bool) or now < 0:
        return {'partner_id': None, 'eta_minutes': None, 'reason': 'Invalid current time'}
    
    # Filter eligible partners
    eligible_partners = []
    
    for partner in partners:
        # Skip invalid partner data
        if not isinstance(partner, dict):
            continue
        
        # Check partner is active
        if not partner.get('active', False):
            continue
        
        # Validate capacity
        capacity = partner.get('capacity')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue
        
        # Check current workload against capacity
        active_orders = partner.get('active_order_ids', [])
        if len(active_orders) >= capacity:
            continue
        
        # Try to calculate ETA
        estimate = estimate_eta(order, partner, travel, now)
        
        # Only consider if eligible
        if estimate.get('eligible', False):
            eligible_partners.append((estimate['eta_minutes'], partner['partner_id'], partner))
    
    if not eligible_partners:
        return {'partner_id': None, 'eta_minutes': None, 'reason': 'No eligible partners'}
    
    # Sort by ETA (ascending), then by partner ID (lexicographic ascending)
    eligible_partners.sort(key=lambda x: (x[0], x[1]))
    
    return {'partner_id': eligible_partners[0][1], 'eta_minutes': eligible_partners[0][0]}


def is_valid_order(order):
    """Validate order has required fields with correct types and values."""
    if not isinstance(order, dict):
        return False
    
    required_fields = ['order_id', 'restaurant_id', 'destination_zone', 'prep_minutes']
    for field in required_fields:
        if field not in order:
            return False
    
    # Validate order_id, restaurant_id, destination_zone are non-empty strings
    for field in ['order_id', 'restaurant_id', 'destination_zone']:
        value = order[field]
        if not isinstance(value, str) or value == '':
            return False
    
    # Validate prep_minutes exists and is valid
    prep = order['prep_minutes']
    if prep is None:
        return False
    if not isinstance(prep, (int, float)) or isinstance(prep, bool):
        return False
    if prep < 0 or prep != prep or prep == float('inf'):
        return False
    
    return True


def process_cancellation(partner, order_id, cancellation_id):
    """
    Process cancellation only once. Check if already processed.
    When cancelling, remove the order's minutes from workload.
    """
    # Get current state
    processed_ids = partner.get('processed_cancellation_ids', [])
    
    # Check if this cancellation was already processed
    if cancellation_id in processed_ids:
        # Already processed, return current state without changes
        return {
            'partner_id': partner['partner_id'],
            'zone': partner['zone'],
            'active': partner.get('active', True),
            'capacity': partner.get('capacity', 1),
            'active_order_ids': list(partner.get('active_order_ids', [])),
            'workload_minutes': partner.get('workload_minutes', 0),
            'minutes_by_order': dict(partner.get('minutes_by_order', {})),
            'processed_cancellation_ids': list(processed_ids)
        }
    
    # Get current orders and minutes
    active_orders = list(partner.get('active_order_ids', []))
    minutes_by_order = dict(partner.get('minutes_by_order', {}))
    current_workload = partner.get('workload_minutes', 0)
    
    # Calculate the workload reduction
    order_minutes = 0
    if order_id in minutes_by_order:
        order_minutes = minutes_by_order[order_id]
    
    # Remove order from active orders
    if order_id in active_orders:
        active_orders.remove(order_id)
    if order_id in minutes_by_order:
        del minutes_by_order[order_id]
    
    # Calculate new workload - subtract the order's minutes, but don't go below 0
    new_workload = max(0, current_workload - order_minutes)
    
    # Add this cancellation to processed list
    new_processed_ids = list(processed_ids) + [cancellation_id]
    
    return {
        'partner_id': partner['partner_id'],
        'zone': partner['zone'],
        'active': partner.get('active', True),
        'capacity': partner.get('capacity', 1),
        'active_order_ids': active_orders,
        'workload_minutes': new_workload,
        'minutes_by_order': minutes_by_order,
        'processed_cancellation_ids': new_processed_ids
    }