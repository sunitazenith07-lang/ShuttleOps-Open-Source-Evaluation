import math
from copy import deepcopy


def _is_non_empty_str(val):
    return isinstance(val, str) and bool(val.strip())


def _is_non_neg_num(val):
    return not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {
            'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None,
            'eta_minutes': None,
            'eligible': False
        }

    partner_id = partner.get('partner_id')
    zone = partner.get('zone')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    prep = order.get('prep_minutes')
    workload = partner.get('workload_minutes', 0)

    if not all(_is_non_empty_str(s) for s in (partner_id, zone, restaurant_id, destination_zone)):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))

    if leg1 is None or leg2 is None or not all(_is_non_neg_num(t) for t in (now, leg1, leg2, workload, prep)):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True
    }


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order'}

    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    prep_minutes = order.get('prep_minutes')

    if (
        not _is_non_empty_str(order_id)
        or not _is_non_empty_str(restaurant_id)
        or not _is_non_empty_str(destination_zone)
        or not _is_non_neg_num(prep_minutes)
        or not _is_non_neg_num(now)
        or not isinstance(travel, dict)
        or not isinstance(partners, list)
    ):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order or time data'
        }

    options = []
    for partner in partners:
        if not isinstance(partner, dict):
            continue
        if not _is_non_empty_str(partner.get('partner_id')) or not _is_non_empty_str(partner.get('zone')):
            continue
        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity', 0)
        active_orders = partner.get('active_order_ids', [])
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity <= 0
            or not isinstance(active_orders, list)
            or len(active_orders) >= capacity
        ):
            continue

        if not _is_non_neg_num(partner.get('workload_minutes', 0)):
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return {
            'active_order_ids': [],
            'processed_cancellation_ids': [],
            'workload_minutes': 0
        }

    out = deepcopy(partner)
    if not isinstance(out.get('active_order_ids'), list):
        out['active_order_ids'] = []
    if not isinstance(out.get('processed_cancellation_ids'), list):
        out['processed_cancellation_ids'] = []

    current_workload = out.get('workload_minutes', 0)
    if not _is_non_neg_num(current_workload):
        current_workload = 0
    out['workload_minutes'] = current_workload

    if not _is_non_empty_str(event_id) or event_id in out['processed_cancellation_ids']:
        return out

    if _is_non_empty_str(order_id) and order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        minutes_map = out.get('minutes_by_order', {})
        order_minutes = minutes_map.get(order_id, 0) if isinstance(minutes_map, dict) else 0
        if not _is_non_neg_num(order_minutes):
            order_minutes = 0
        out['workload_minutes'] = max(0, current_workload - order_minutes)

    out['processed_cancellation_ids'].append(event_id)
    return out