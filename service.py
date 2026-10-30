
from copy import deepcopy
import math


def is_valid_time(value):
    """Check for finite, non-negative integer or float time values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    try:
        return math.isfinite(value) and value >= 0
    except (OverflowError, ValueError):
        return False


def is_valid_identifier(value):
    """Check whether an identifier is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def _ineligible_estimate(partner_id=None):
    return {
        'partner_id': partner_id,
        'eta_minutes': None,
        'eligible': False,
    }


def estimate_eta(order, partner, travel, now=0):
    """Calculate pickup time and ETA safely."""

    if (
        not isinstance(order, dict)
        or not isinstance(partner, dict)
        or not isinstance(travel, dict)
    ):
        partner_id = (
            partner.get('partner_id')
            if isinstance(partner, dict) else None
        )
        return _ineligible_estimate(partner_id)

    partner_id = partner.get('partner_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    partner_zone = partner.get('zone')

    if not all(is_valid_identifier(value) for value in (
        order.get('order_id'),
        restaurant_id,
        destination_zone,
        partner_id,
        partner_zone,
    )):
        return _ineligible_estimate(partner_id)

    prep_minutes = order.get('prep_minutes')
    workload_minutes = partner.get('workload_minutes', 0)

    if not is_valid_time(now):
        return _ineligible_estimate(partner_id)

    if not is_valid_time(prep_minutes):
        return _ineligible_estimate(partner_id)

    if not is_valid_time(workload_minutes):
        return _ineligible_estimate(partner_id)

    leg1 = travel.get((partner_zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))

    if not is_valid_time(leg1) or not is_valid_time(leg2):
        return _ineligible_estimate(partner_id)

    pickup = now + leg1 + workload_minutes
    eta = pickup + prep_minutes + leg2

    if not is_valid_time(pickup) or not is_valid_time(eta):
        return _ineligible_estimate(partner_id)

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    """Choose the eligible active partner with the lowest ETA."""

    order_id = (
        order.get('order_id')
        if isinstance(order, dict) else None
    )

    options = []

    if not isinstance(partners, (list, tuple)):
        partners = []

    for partner in partners:

        if not isinstance(partner, dict):
            continue

        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity')

        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            continue

        active_order_ids = partner.get('active_order_ids', [])

        if not isinstance(active_order_ids, list):
            continue

        if len(active_order_ids) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now)

        if estimate['eligible']:
            options.append(estimate)

    if not options:
        if not isinstance(order, dict) or not all(
            is_valid_identifier(order.get(field))
            for field in (
                'order_id',
                'restaurant_id',
                'destination_zone',
            )
        ):
            reason = 'invalid order data'

        elif not partners:
            reason = 'no partners available'

        else:
            reason = 'no eligible partner or missing/invalid time data'

        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': reason,
        }

    chosen = min(
        options,
        key=lambda item: (
            item['eta_minutes'],
            item['partner_id']
        )
    )

    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation only once."""

    if not isinstance(partner, dict):
        return {}

    out = deepcopy(partner)

    active_order_ids = out.get('active_order_ids', [])

    if not isinstance(active_order_ids, list):
        active_order_ids = []

    out['active_order_ids'] = active_order_ids

    processed_ids = out.get('processed_cancellation_ids', [])

    if not isinstance(processed_ids, list):
        processed_ids = []

    out['processed_cancellation_ids'] = processed_ids

    if not is_valid_identifier(event_id):
        return out

    if event_id in processed_ids:
        return out

    minutes_by_order = out.get('minutes_by_order', {})

    if not isinstance(minutes_by_order, dict):
        minutes_by_order = {}

    if (
        is_valid_identifier(order_id)
        and order_id in active_order_ids
    ):
        active_order_ids.remove(order_id)

        workload_minutes = out.get('workload_minutes', 0)

        if not is_valid_time(workload_minutes):
            workload_minutes = 0

        released_minutes = minutes_by_order.get(order_id, 0)

        if not is_valid_time(released_minutes):
            released_minutes = 0

        out['workload_minutes'] = max(
            0,
            workload_minutes - released_minutes
        )

    processed_ids.append(event_id)

    return out
