from copy import deepcopy
import math


def _is_valid_numeric(value, allow_zero=True):
    """Return True if value is a finite int or float (not bool), non-negative."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    if math.isnan(value) or math.isinf(value):
        return False
    if value < 0:
        return False
    if not allow_zero and value == 0:
        return False
    return True


def _is_valid_travel_time(value):
    """Return True if value is a valid travel time (non-negative finite int/float, not bool)."""
    return _is_valid_numeric(value, allow_zero=True)


def _is_valid_order(order):
    """Return True if the order has valid required fields."""
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        val = order.get(field)
        if not val or not isinstance(val, str):
            return False
    prep = order.get('prep_minutes')
    if not _is_valid_numeric(prep, allow_zero=True):
        return False
    return True


def _is_eligible_partner(partner):
    """Return True if the partner is active and has remaining capacity."""
    if partner.get('active') is not True:
        return False
    capacity = partner.get('capacity')
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
        return False
    current_orders = len(partner.get('active_order_ids', []))
    if current_orders >= capacity:
        return False
    return True


def estimate_eta(order, partner, travel, now=0):
    # Validate now
    if not _is_valid_numeric(now, allow_zero=True):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # Validate order prep_minutes
    prep = order.get('prep_minutes', 0)
    if not _is_valid_numeric(prep, allow_zero=True):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))

    # Both legs must be present and valid
    if leg1 is None or leg2 is None:
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not _is_valid_travel_time(leg1) or not _is_valid_travel_time(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + partner.get('workload_minutes', 0)
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    # Validate order fields before processing
    if not _is_valid_order(order):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order fields',
        }

    options = []
    for partner in partners:
        # Filter: must be active and have capacity
        if not _is_eligible_partner(partner):
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order.get('order_id'),
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    # Idempotency: if this event was already processed, do nothing
    if event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(
            0,
            out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0),
        )
    out['processed_cancellation_ids'].append(event_id)
    return out
