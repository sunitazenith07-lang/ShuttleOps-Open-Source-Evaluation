from copy import deepcopy
from math import isfinite


def _valid_minutes(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value >= 0
    return isinstance(value, float) and isfinite(value) and value >= 0


def _valid_identifier(value):
    return isinstance(value, str) and bool(value)


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None, 'eta_minutes': None, 'eligible': False}
    partner_id = partner.get('partner_id')
    if (not _valid_identifier(order.get('order_id')) or
            not _valid_identifier(order.get('restaurant_id')) or
            not _valid_identifier(order.get('destination_zone')) or
            not _valid_identifier(partner.get('zone')) or
            not _valid_minutes(order.get('prep_minutes', 10)) or
            not _valid_minutes(partner.get('workload_minutes', 0)) or
            not _valid_minutes(now)):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if not _valid_minutes(leg1) or not _valid_minutes(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}
    pickup = now + leg1 + partner.get('workload_minutes', 0)
    return {'partner_id': partner_id, 'pickup_minutes': pickup, 'eta_minutes': pickup + order.get('prep_minutes', 10) + leg2, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    options = []
    if not isinstance(partners, (list, tuple)):
        partners = []
    for partner in partners:
        if not isinstance(partner, dict) or partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        active_order_ids = partner.get('active_order_ids', [])
        if (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1 or
                not isinstance(active_order_ids, list) or len(active_order_ids) >= capacity):
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return {'order_id': order.get('order_id') if isinstance(order, dict) else None, 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {'order_id': order.get('order_id'), 'partner_id': chosen['partner_id'], 'pickup_minutes': chosen['pickup_minutes'], 'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    if event_id in out['processed_cancellation_ids']:
        return out
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(0, out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0))
    out['processed_cancellation_ids'].append(event_id)
    return out
