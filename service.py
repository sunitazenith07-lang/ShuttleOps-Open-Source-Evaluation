from copy import deepcopy
import math


def _is_valid_number(value):
    """A usable time value: a real (non-bool) int/float, finite and >= 0.

    Missing data, negative values, booleans, strings, NaN and infinity are all
    rejected. Missing travel data is never treated as zero.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value):
        return False
    return value >= 0


def _is_valid_identifier(value):
    """Order/restaurant/destination identifiers must be non-empty strings."""
    return isinstance(value, str) and len(value) > 0


def _unassigned(order, reason):
    return {
        'order_id': order.get('order_id'),
        'partner_id': None,
        'pickup_minutes': None,
        'eta_minutes': None,
        'reason': reason,
    }


def estimate_eta(order, partner, travel, now=0):
    """Calculate the ETA for a single candidate partner.

    Returns a dict with eligible=False (and eta_minutes=None) whenever the
    current time, preparation time or any required travel time is missing or
    invalid. Never raises on malformed input.
    """
    if not _is_valid_number(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if not _is_valid_number(leg1) or not _is_valid_number(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    prep = order.get('prep_minutes', 0)
    if not _is_valid_number(prep):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    workload = workload if _is_valid_number(workload) else 0
    pickup = now + leg1 + workload
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    """Pick the eligible partner with the lowest ETA for an order.

    Validation (requirement contract):
      * order id, restaurant id and destination zone must be non-empty strings
      * preparation time must be a non-negative finite number
      * only active partners below capacity are candidates
      * a candidate with any missing/invalid required travel time is ineligible
      * lowest ETA wins; ETA ties break by partner id ascending
      * if no valid candidate remains, the order is left unassigned with a reason
    """
    if not _is_valid_identifier(order.get('order_id')):
        return _unassigned(order, 'invalid order id')
    if not _is_valid_identifier(order.get('restaurant_id')):
        return _unassigned(order, 'invalid restaurant id')
    if not _is_valid_identifier(order.get('destination_zone')):
        return _unassigned(order, 'invalid destination zone')
    if not _is_valid_number(order.get('prep_minutes', 0)):
        return _unassigned(order, 'invalid preparation time')

    options = []
    for partner in partners:
        # Consider only active partners below their order capacity.
        if partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue
        if len(partner.get('active_order_ids', [])) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return _unassigned(order, 'no eligible partner or missing time data')

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order.get('order_id'),
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    """Release one order's workload for a partner, processing each event once.

    A duplicate cancellation (same event_id) is ignored so workload and capacity
    are never released twice. Workload never drops below zero. Cancelling an
    order that is not active leaves the partner unchanged.
    """
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    # Process each cancellation event only once (idempotency).
    if event_id in out['processed_cancellation_ids']:
        return out

    out['processed_cancellation_ids'].append(event_id)

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(
            0,
            out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0),
        )

    return out
