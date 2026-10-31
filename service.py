from collections.abc import Iterable, Mapping
from copy import deepcopy
from math import isfinite


def _is_identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _is_valid_time(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int):
        return value >= 0
    return isfinite(value) and value >= 0


def _unassigned_result(order, reason):
    order_id = order.get('order_id') if isinstance(order, Mapping) else None
    return {
        'order_id': order_id,
        'partner_id': None,
        'eta_minutes': None,
        'reason': reason,
    }


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, Mapping) or not isinstance(partner, Mapping):
        return {
            'partner_id': None,
            'eta_minutes': None,
            'eligible': False,
        }

    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    partner_id = partner.get('partner_id')
    partner_zone = partner.get('zone')
    prep_minutes = order.get('prep_minutes')
    workload_minutes = partner.get('workload_minutes', 0)

    if not all(map(_is_identifier, (
        order_id, restaurant_id, destination_zone, partner_id, partner_zone
    ))):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not all(map(_is_valid_time, (prep_minutes, workload_minutes, now))):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not isinstance(travel, Mapping):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner_zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))
    if not _is_valid_time(leg1) or not _is_valid_time(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    try:
        pickup = now + leg1 + workload_minutes
        eta = pickup + prep_minutes + leg2
    except OverflowError:
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_time(pickup) or not _is_valid_time(eta):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    candidates = (
        partners
        if isinstance(partners, Iterable)
        and not isinstance(partners, (str, bytes, Mapping))
        else ()
    )
    options = []
    for partner in candidates:
        if not isinstance(partner, Mapping):
            continue
        active_order_ids = partner.get('active_order_ids')
        capacity = partner.get('capacity')
        if (
            partner.get('active') is not True
            or not isinstance(active_order_ids, list)
            or isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
            or len(active_order_ids) >= capacity
        ):
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return _unassigned_result(
            order,
            'no eligible partner or missing time data',
        )

    chosen = min(options, key=lambda item: (item['eta_minutes'], item['partner_id']))
    return {
        'order_id': order.get('order_id') if isinstance(order, Mapping) else None,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, Mapping):
        raise TypeError('partner must be a mapping')

    out = deepcopy(dict(partner))
    active_order_ids = out.setdefault('active_order_ids', [])
    processed_ids = out.setdefault('processed_cancellation_ids', [])
    if not isinstance(active_order_ids, list) or not isinstance(processed_ids, list):
        raise TypeError('partner cancellation state must use lists')
    if event_id in processed_ids:
        return out

    if order_id in active_order_ids:
        minutes_by_order = out.get('minutes_by_order', {})
        workload_minutes = out.get('workload_minutes', 0)
        minutes = (
            minutes_by_order.get(order_id, 0)
            if isinstance(minutes_by_order, Mapping)
            else None
        )
        if not _is_valid_time(workload_minutes) or not _is_valid_time(minutes):
            raise ValueError('partner workload and order minutes must be non-negative numbers')
        active_order_ids.remove(order_id)
        out['workload_minutes'] = max(0, workload_minutes - minutes)

    processed_ids.append(event_id)
    return out
