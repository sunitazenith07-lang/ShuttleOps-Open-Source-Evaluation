import math
from copy import deepcopy


def _is_valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _is_valid_order_field(value):
    return isinstance(value, str) and value != ""


def estimate_eta(order, partner, travel, now=0):
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    if not isinstance(order, dict):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    prep_minutes = order.get('prep_minutes', 0)

    if not _is_valid_order_field(order_id) or not _is_valid_order_field(restaurant_id) or not _is_valid_order_field(destination_zone):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_number(prep_minutes):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not _is_valid_number(now):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    if not isinstance(partner, dict):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_number(workload):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))
    if not _is_valid_number(leg1) or not _is_valid_number(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    pickup_minutes = now + leg1 + workload
    eta_minutes = pickup_minutes + prep_minutes + leg2
    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup_minutes,
        'eta_minutes': eta_minutes,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order data'}

    order_id = order.get('order_id')
    if not _is_valid_order_field(order_id):
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order data'}

    options = []
    for partner in partners or []:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue

        active_order_ids = partner.get('active_order_ids') or []
        if not isinstance(active_order_ids, list):
            active_order_ids = list(active_order_ids) if active_order_ids is not None else []
        if len(active_order_ids) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now=now)
        if estimate.get('eligible'):
            options.append(estimate)

    if not options:
        return {'order_id': order_id, 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    if not isinstance(out, dict):
        return out

    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    processed = out.get('processed_cancellation_ids') or []
    if event_id in processed:
        return out

    active_order_ids = out.get('active_order_ids') or []
    if isinstance(order_id, str) and order_id in active_order_ids:
        out['active_order_ids'] = [item for item in active_order_ids if item != order_id]
        minutes_by_order = out.get('minutes_by_order') or {}
        released_minutes = minutes_by_order.get(order_id, 0)
        if _is_valid_number(released_minutes):
            current_workload = out.get('workload_minutes', 0)
            out['workload_minutes'] = max(0, current_workload - released_minutes)

    out['processed_cancellation_ids'] = list(processed)
    out['processed_cancellation_ids'].append(event_id)
    return out
