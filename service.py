from copy import deepcopy
import math


def is_valid_number(val):
    """Utility to strictly check for valid non-negative integer/float (rejecting bool, None, string, nan, inf)."""
    if val is None or isinstance(val, bool):
        return False, 0.0
    if isinstance(val, str):
        return False, 0.0
    try:
        num = float(val)
        if math.isnan(num) or math.isinf(num) or num < 0:
            return False, 0.0
        return True, num
    except (ValueError, TypeError):
        return False, 0.0


def estimate_eta(order, partner, travel, now=0):
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    # Validate leg1 and leg2 strictly
    valid1, num_leg1 = is_valid_number(leg1)
    valid2, num_leg2 = is_valid_number(leg2)
    if not valid1 or not valid2:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    # Validate now parameter strictly
    valid_now, num_now = is_valid_number(now)
    if not valid_now:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    # Validate prep_minutes strictly
    raw_prep = order.get('prep_minutes', 0)
    valid_prep, num_prep = is_valid_number(raw_prep)
    if not valid_prep:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    workload = partner.get('workload_minutes', 0)
    valid_wl, num_wl = is_valid_number(workload)
    if not valid_wl:
        num_wl = 0.0
    pickup = num_now + num_leg1 + num_wl
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + num_prep + num_leg2,
        'eligible': True
    }
def assign_order(order, partners, travel, now=0):
    # 1. Validate order structure
    if not order or not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order structure'}
    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    dest_zone = order.get('destination_zone')
    # Strict check for required string/numeric fields (disallow empty string, None, 0, False)
    if order_id in ("", None, 0, False) or restaurant_id in ("", None, 0, False) or dest_zone in ("", None, 0, False):
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order fields'}
    # 2. Validate current time (`now`)
    valid_now, num_now = is_valid_number(now)
    if not valid_now:
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid current time'}
    # 3. Validate prep_minutes strictly
    raw_prep = order.get('prep_minutes')
    valid_prep, num_prep = is_valid_number(raw_prep)
    if not valid_prep:
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid prep_minutes'}
    options = []
    for partner in partners:
        # Filter inactive partners
        if not partner.get('active', True):
            continue
        # Filter capacity strictly: Capacity must be a positive integer (not float, not bool, not None)
        raw_cap = partner.get('capacity', 1)
        if not isinstance(raw_cap, int) or isinstance(raw_cap, bool) or raw_cap < 1:
            continue
        active_orders = len(partner.get('active_order_ids', []))
        if active_orders >= raw_cap:
            continue
        # Calculate ETA
        estimate = estimate_eta(order, partner, travel, num_now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
    # Deterministic tie-breaking: lowest ETA, then partner_id ascending lexicographically
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
    # Idempotency check for duplicate cancellations
    if event_id in out['processed_cancellation_ids']:
        return out
    out['processed_cancellation_ids'].append(event_id)
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        released_workload = out.get('minutes_by_order', {}).get(order_id, 0)
        out['workload_minutes'] = max(0, out.get('workload_minutes', 0) - released_workload)

    return out