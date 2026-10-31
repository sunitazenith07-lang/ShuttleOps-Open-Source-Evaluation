from copy import deepcopy
from math import isfinite


def _identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _minutes(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and value >= 0 and (not isinstance(value, float) or isfinite(value)))


def _order_error(order):
    if not isinstance(order, dict):
        return 'invalid order record'
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        if not _identifier(order.get(field)):
            return f'invalid {field}'
    if not _minutes(order.get('prep_minutes')):
        return 'invalid preparation time'
    return None


def _partner_error(partner):
    if not isinstance(partner, dict):
        return 'invalid partner record'
    if not all(_identifier(partner.get(key)) for key in ('partner_id', 'zone')):
        return 'invalid partner ID or zone'
    if partner.get('active') is not True:
        return 'partner is inactive or has invalid active status'
    capacity = partner.get('capacity')
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        return 'invalid partner capacity'
    orders = partner.get('active_order_ids')
    if not isinstance(orders, list) or not all(_identifier(item) for item in orders):
        return 'invalid active orders'
    if len(set(orders)) != len(orders):
        return 'duplicate active orders'
    if len(orders) >= capacity:
        return 'partner is at capacity'
    if not _minutes(partner.get('workload_minutes')):
        return 'invalid remaining workload'
    return None


def estimate_eta(order, partner, travel, now=0):
    result = {'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None,
              'eta_minutes': None, 'eligible': False}
    error = _order_error(order) or _partner_error(partner)
    if error:
        return dict(result, reason=error)
    if not _minutes(now):
        return dict(result, reason='invalid current time')
    if not isinstance(travel, dict):
        return dict(result, reason='invalid travel mapping')
    leg1 = travel.get((partner['zone'], order['restaurant_id']))
    leg2 = travel.get((order['restaurant_id'], order['destination_zone']))
    if leg1 is None or leg2 is None:
        return dict(result, reason='missing travel time')
    if not _minutes(leg1) or not _minutes(leg2):
        return dict(result, reason='invalid travel time')
    try:
        pickup = now + leg1 + partner['workload_minutes']
        eta = pickup + order['prep_minutes'] + leg2
    except OverflowError:
        return dict(result, reason='ETA exceeds numeric range')
    if not _minutes(pickup) or not _minutes(eta):
        return dict(result, reason='ETA exceeds numeric range')
    return {'partner_id': partner['partner_id'], 'pickup_minutes': pickup,
            'eta_minutes': eta, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    """Recommend a partner; the caller records assignments and reserves capacity."""
    result = {'order_id': order.get('order_id') if isinstance(order, dict) else None,
              'partner_id': None, 'eta_minutes': None}
    error = _order_error(order)
    if error:
        return dict(result, reason=error)
    if not isinstance(partners, (list, tuple)):
        return dict(result, reason='invalid partner collection')
    if not partners:
        return dict(result, reason='no partners provided')
    for partner in partners:
        active_orders = partner.get('active_order_ids') if isinstance(partner, dict) else None
        if isinstance(active_orders, list) and order['order_id'] in active_orders:
            return dict(result, reason='order is already active')
    chosen = None
    reasons = set()
    for partner in partners:
        estimate = estimate_eta(order, partner, travel, now)
        if not estimate['eligible']:
            reasons.add(estimate['reason'])
            continue
        # Pickup resolves otherwise identical keys for duplicate partner records.
        if chosen is None or (estimate['eta_minutes'], estimate['partner_id'], estimate['pickup_minutes']) < (
                chosen['eta_minutes'], chosen['partner_id'], chosen['pickup_minutes']):
            chosen = estimate
    if chosen is None:
        return dict(result, reason='no eligible partner: ' + '; '.join(sorted(reasons)))
    return dict(result, partner_id=chosen['partner_id'],
                pickup_minutes=chosen['pickup_minutes'],
                eta_minutes=chosen['eta_minutes'], reason='assigned')


def process_cancellation(partner, order_id, event_id):
    """Return updated partner state, or an unchanged copy for rejected events."""
    out = deepcopy(partner)
    if not isinstance(out, dict) or not _identifier(order_id) or not _identifier(event_id):
        return out
    orders = out.get('active_order_ids')
    processed = out.get('processed_cancellation_ids', [])
    minutes = out.get('minutes_by_order')
    workload = out.get('workload_minutes')
    if (not isinstance(orders, list) or not isinstance(processed, list)
            or not isinstance(minutes, dict)
            or not all(_identifier(item) for item in orders + processed)
            or len(set(orders)) != len(orders) or not _minutes(workload)):
        return out
    if event_id in processed:
        return out
    if order_id in orders:
        released = minutes.get(order_id)
        if not _minutes(released):
            return out
        # Compute before modifying state: mixed huge ints/floats can overflow.
        try:
            remaining = max(0, workload - released)
        except OverflowError:
            return out
        orders.remove(order_id)
        out['workload_minutes'] = remaining
        minutes.pop(order_id, None)
    processed.append(event_id)
    out['active_order_ids'] = orders
    out['processed_cancellation_ids'] = processed
    return out
