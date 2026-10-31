import math
from copy import deepcopy


def _is_valid_non_negative_number(val):
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return val >= 0
    if isinstance(val, float):
        return math.isfinite(val) and val >= 0
    return False


def _is_valid_non_empty_str(val):
    return isinstance(val, str) and len(val.strip()) > 0


def _is_valid_capacity(val):
    return isinstance(val, int) and not isinstance(val, bool) and val >= 1


def estimate_eta(order, partner, travel, now=0):
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    ineligible = {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    if not _is_valid_non_negative_number(now):
        return ineligible

    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return ineligible

    if (
        not _is_valid_non_empty_str(order.get('order_id'))
        or not _is_valid_non_empty_str(order.get('restaurant_id'))
        or not _is_valid_non_empty_str(order.get('destination_zone'))
        or not _is_valid_non_empty_str(partner.get('zone'))
    ):
        return ineligible

    prep = order.get('prep_minutes', 0)
    if not _is_valid_non_negative_number(prep):
        return ineligible

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        return ineligible

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))

    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return ineligible

    pickup = now + leg1 + workload
    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    order_id = order.get('order_id') if isinstance(order, dict) else None
    options = []
    if not hasattr(partners, '__iter__') or isinstance(partners, (str, bytes, dict)):
        partners = []

    for partner in partners:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        if not _is_valid_capacity(capacity):
            continue
        active_orders = partner.get('active_order_ids')
        if not isinstance(active_orders, list):
            continue
        if len(active_orders) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
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
    if not isinstance(out.get('active_order_ids'), list):
        out['active_order_ids'] = []
    if not isinstance(out.get('processed_cancellation_ids'), list):
        out['processed_cancellation_ids'] = []

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
