"""Deterministic offline delivery dispatch and cancellation operations."""
from copy import deepcopy
from math import isfinite


def _minutes(value):
    return type(value) in (int, float) and isfinite(value) and value >= 0


def _identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_order(order):
    return (isinstance(order, dict) and all(_identifier(order.get(k)) for k in
            ('order_id', 'restaurant_id', 'destination_zone')) and
            _minutes(order.get('prep_minutes')))


def _valid_partner(partner):
    if not isinstance(partner, dict):
        return False
    orders = partner.get('active_order_ids')
    capacity = partner.get('capacity')
    return (partner.get('active') is True and _identifier(partner.get('partner_id'))
            and _identifier(partner.get('zone')) and type(capacity) is int
            and capacity >= 1 and isinstance(orders, list)
            and len(orders) < capacity and _minutes(partner.get('workload_minutes')))


def estimate_eta(order, partner, travel, now=0):
    """Return a valid ETA only when all inputs and route legs are reliable."""
    pid = partner.get('partner_id') if isinstance(partner, dict) else None
    rejected = {'partner_id': pid, 'eta_minutes': None, 'eligible': False}
    if not (_valid_order(order) and _valid_partner(partner) and
            isinstance(travel, dict) and _minutes(now)):
        return rejected
    leg1 = travel.get((partner['zone'], order['restaurant_id']))
    leg2 = travel.get((order['restaurant_id'], order['destination_zone']))
    if not (_minutes(leg1) and _minutes(leg2)):
        return rejected
    pickup = now + leg1 + partner['workload_minutes']
    eta = pickup + order['prep_minutes'] + leg2
    if not (isfinite(pickup) and isfinite(eta)):
        return rejected
    return {'partner_id': pid, 'pickup_minutes': pickup,
            'eta_minutes': eta, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    """Select minimum ETA, breaking ties by lexicographic partner ID."""
    oid = order.get('order_id') if isinstance(order, dict) else None
    failure = {'order_id': oid, 'partner_id': None, 'eta_minutes': None,
               'reason': 'no eligible partner or missing time data'}
    if not _valid_order(order):
        return {**failure, 'reason': 'invalid order'}
    if not isinstance(partners, (list, tuple)) or not isinstance(travel, dict) or not _minutes(now):
        return {**failure, 'reason': 'invalid dispatch input'}
    options = [result for partner in partners
               if (result := estimate_eta(order, partner, travel, now))['eligible']]
    if not options:
        return failure
    chosen = min(options, key=lambda item: (item['eta_minutes'], item['partner_id']))
    return {'order_id': oid, 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'],
            'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    """Apply each cancellation event at most once without mutating the input."""
    if not isinstance(partner, dict):
        return partner
    out = deepcopy(partner)
    processed = out.get('processed_cancellation_ids')
    if not isinstance(processed, list):
        processed = []
        out['processed_cancellation_ids'] = processed
    if not _identifier(event_id) or event_id in processed:
        return out
    active = out.get('active_order_ids')
    if not isinstance(active, list):
        active = []
        out['active_order_ids'] = active
    if order_id in active:
        active.remove(order_id)
        minutes_map = out.get('minutes_by_order')
        minutes = minutes_map.get(order_id, 0) if isinstance(minutes_map, dict) else 0
        workload = out.get('workload_minutes', 0)
        if _minutes(workload) and _minutes(minutes):
            out['workload_minutes'] = max(0, workload - minutes)
        if isinstance(minutes_map, dict):
            minutes_map.pop(order_id, None)
    processed.append(event_id)
    return out
