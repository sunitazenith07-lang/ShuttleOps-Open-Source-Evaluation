import math
from copy import deepcopy


def _is_minutes(value):
    """A usable time value: a real, finite, non-negative int/float (bool is rejected)."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def _is_id(value):
    """IDs and zones must be non-empty strings so lookups and tie-breaks are well defined."""
    return isinstance(value, str) and value.strip() != ''


def _is_capacity(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def validate_order(order):
    """Return None for a valid order, otherwise a short reason string."""
    if not isinstance(order, dict):
        return 'order record is not a mapping'
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        if not _is_id(order.get(field)):
            return f'invalid or missing {field}'
    if not _is_minutes(order.get('prep_minutes')):
        return 'invalid or missing prep_minutes'
    return None


def partner_rejection(partner):
    """Return None if the partner may take a new order, otherwise why it may not."""
    if not isinstance(partner, dict):
        return 'partner record is not a mapping'
    if not _is_id(partner.get('partner_id')):
        return 'invalid or missing partner_id'
    if partner.get('active') is not True:
        return 'partner is not active'
    capacity = partner.get('capacity')
    if not _is_capacity(capacity):
        return 'invalid capacity'
    active_orders = partner.get('active_order_ids', [])
    if not isinstance(active_orders, (list, tuple)):
        return 'invalid active_order_ids'
    if len(active_orders) >= capacity:
        return 'partner at capacity'
    return None


def _ineligible(partner, reason):
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False, 'reason': reason}


def estimate_eta(order, partner, travel, now=0):
    """pickup = now + leg1 + workload; eta = pickup + prep + leg2.

    Any missing or invalid input makes the estimate ineligible; nothing defaults to zero.
    """
    if not _is_minutes(now):
        return _ineligible(partner, 'invalid current time')
    order_problem = validate_order(order)
    if order_problem:
        return _ineligible(partner, order_problem)
    if not isinstance(partner, dict):
        return _ineligible(partner, 'partner record is not a mapping')
    if not _is_id(partner.get('zone')):
        return _ineligible(partner, 'invalid or missing partner zone')
    workload = partner.get('workload_minutes')
    if not _is_minutes(workload):
        return _ineligible(partner, 'invalid or missing workload_minutes')
    if not isinstance(travel, dict):
        return _ineligible(partner, 'travel-time data is not a mapping')

    restaurant = order['restaurant_id']
    leg1 = travel.get((partner['zone'], restaurant))
    leg2 = travel.get((restaurant, order['destination_zone']))
    if leg1 is None or leg2 is None:
        return _ineligible(partner, 'missing travel-time data')
    if not (_is_minutes(leg1) and _is_minutes(leg2)):
        return _ineligible(partner, 'invalid travel-time data')

    pickup = now + leg1 + workload
    return {'partner_id': partner.get('partner_id'), 'pickup_minutes': pickup,
            'eta_minutes': pickup + order['prep_minutes'] + leg2, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    order_id = order.get('order_id') if isinstance(order, dict) else None
    unassigned = {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'rejected': []}

    order_problem = validate_order(order)
    if order_problem:
        return {**unassigned, 'reason': f'invalid order: {order_problem}'}
    if not _is_minutes(now):
        return {**unassigned, 'reason': 'invalid current time'}
    if not isinstance(partners, (list, tuple)) or not partners:
        return {**unassigned, 'reason': 'no delivery partners supplied'}

    options, rejected = [], []
    for partner in partners:
        reason = partner_rejection(partner)
        if reason is None:
            estimate = estimate_eta(order, partner, travel, now)
            if estimate['eligible']:
                options.append(estimate)
                continue
            reason = estimate['reason']
        partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
        rejected.append({'partner_id': partner_id, 'reason': reason})

    if not options:
        summary = '; '.join(sorted({item['reason'] for item in rejected}))
        return {**unassigned, 'rejected': rejected, 'reason': f'no eligible partner ({summary})'}

    # partner_id is validated as str, so (eta, partner_id) is a total, input-order-independent key.
    chosen = min(options, key=lambda item: (item['eta_minutes'], item['partner_id']))
    return {'order_id': order_id, 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'], 'eta_minutes': chosen['eta_minutes'],
            'reason': 'assigned', 'rejected': rejected}


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation at most once per event_id; returns a new partner record."""
    if not isinstance(partner, dict):
        raise TypeError('partner record must be a mapping')
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    out.setdefault('minutes_by_order', {})

    # An event without an ID cannot be de-duplicated, so it is not applied.
    if not _is_id(event_id) or event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        released = out['minutes_by_order'].pop(order_id, 0)
        workload = out.get('workload_minutes', 0)
        if _is_minutes(released) and _is_minutes(workload):
            out['workload_minutes'] = max(0, workload - released)
    out['processed_cancellation_ids'].append(event_id)
    return out
