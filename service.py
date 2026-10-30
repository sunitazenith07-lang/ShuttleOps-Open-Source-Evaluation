from copy import deepcopy
import math


def _valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_time(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def _valid_order(order):
    return isinstance(order, dict) and _valid_id(order.get('order_id')) and _valid_id(order.get('restaurant_id')) and _valid_id(order.get('destination_zone')) and _valid_time(order.get('prep_minutes'))


def estimate_eta(order, partner, travel, now=0):
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    if (not _valid_order(order) or not isinstance(partner, dict)
            or not _valid_id(partner.get('partner_id')) or not _valid_id(partner.get('zone'))
            or not isinstance(travel, dict) or not _valid_time(now)):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    workload = partner.get('workload_minutes', 0)
    if not _valid_time(leg1) or not _valid_time(leg2) or not _valid_time(workload):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    return {'partner_id': partner_id, 'pickup_minutes': pickup,
            'eta_minutes': pickup + order['prep_minutes'] + leg2, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    options = []
    if not isinstance(partners, list) or not isinstance(travel, dict) or not _valid_order(order):
        return {'order_id': order.get('order_id') if isinstance(order, dict) else None,
                'partner_id': None, 'eta_minutes': None,
                'reason': 'no eligible partner or missing time data'}

    for partner in partners:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        active_orders = partner.get('active_order_ids', [])
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue
        if not isinstance(active_orders, list) or len(active_orders) >= capacity:
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None,
                'reason': 'no eligible partner or missing time data'}
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {'order_id': order.get('order_id'), 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'], 'eta_minutes': chosen['eta_minutes'],
            'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner) if isinstance(partner, dict) else {}
    active_orders = out.setdefault('active_order_ids', [])
    if not isinstance(active_orders, list):
        active_orders = []
        out['active_order_ids'] = active_orders
    processed = out.setdefault('processed_cancellation_ids', [])
    if not isinstance(processed, list):
        processed = []
        out['processed_cancellation_ids'] = processed

    if event_id in processed:
        return out
    processed.append(event_id)
    if order_id in active_orders:
        active_orders.remove(order_id)
        minutes_by_order = out.get('minutes_by_order', {})
        cancelled_minutes = minutes_by_order.get(order_id, 0) if isinstance(minutes_by_order, dict) else 0
        workload = out.get('workload_minutes', 0)
        if not _valid_time(workload):
            workload = 0
        if not _valid_time(cancelled_minutes):
            cancelled_minutes = 0
        out['workload_minutes'] = max(0, workload - cancelled_minutes)
    return out
