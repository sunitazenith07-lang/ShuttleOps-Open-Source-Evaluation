"""Pure offline dispatch recommendations and cancellation handling."""
from copy import deepcopy
from math import isfinite


def _identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _time(value):
    return type(value) in (int, float) and value >= 0 and (type(value) is int or isfinite(value))


def _ids(value):
    return isinstance(value, list) and all(_identifier(i) for i in value) and len(set(value)) == len(value)


def _order_error(order, now):
    if not isinstance(order, dict):
        return 'invalid order record'
    if not all(_identifier(order.get(k)) for k in ('order_id', 'restaurant_id', 'destination_zone')):
        return 'invalid or missing order identifier, restaurant or destination'
    if not _time(order.get('prep_minutes')) or not _time(now):
        return 'invalid preparation or current time'
    return None


def estimate_eta(order, partner, travel, now=0):
    """Validate eligibility and return an ETA; missing routes are never zero."""
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    result = dict(partner_id=partner_id, pickup_minutes=None, eta_minutes=None, eligible=False)

    def reject(reason):
        return {**result, 'reason': reason}

    error = _order_error(order, now)
    if error:
        return reject(error)
    if not isinstance(partner, dict) or not _identifier(partner_id) or not _identifier(partner.get('zone')):
        return reject('invalid partner record or identifier')
    if partner.get('active') is not True:
        return reject('partner is inactive')
    capacity = partner.get('capacity')
    active_ids = partner.get('active_order_ids')
    if type(capacity) is not int or capacity < 1 or not _ids(active_ids):
        return reject('invalid partner capacity or active orders')
    if order['order_id'] in active_ids:
        return reject('order already active for partner')
    if len(active_ids) >= capacity:
        return reject('partner is at capacity')
    workload = partner.get('workload_minutes')
    if not _time(workload):
        return reject('invalid partner workload')
    if not isinstance(travel, dict):
        return reject('invalid travel data')
    leg1 = travel.get((partner['zone'], order['restaurant_id']))
    leg2 = travel.get((order['restaurant_id'], order['destination_zone']))
    if leg1 is None or leg2 is None:
        return reject('missing required travel time')
    if not _time(leg1) or not _time(leg2):
        return reject('invalid required travel time')
    try:
        pickup = now + leg1 + workload
        eta = pickup + order['prep_minutes'] + leg2
    except OverflowError:
        return reject('time calculation overflow')
    if not _time(pickup) or not _time(eta):
        return reject('time calculation overflow')
    return dict(partner_id=partner_id, pickup_minutes=pickup, eta_minutes=eta,
                eligible=True, reason='eligible')


def assign_order(order, partners, travel, now=0):
    """Recommend one partner without mutating inputs or reserving capacity.

    Ambiguous duplicate partner IDs are excluded rather than selected by input order.
    """
    result = dict(order_id=order.get('order_id') if isinstance(order, dict) else None,
                  partner_id=None, pickup_minutes=None, eta_minutes=None)
    error = _order_error(order, now)
    if error:
        return {**result, 'reason': error}
    if not isinstance(partners, (list, tuple)):
        return {**result, 'reason': 'invalid partner collection'}
    counts = {}
    for p in partners:
        if isinstance(p, dict) and _identifier(p.get('partner_id')):
            pid = p['partner_id']
            counts[pid] = counts.get(pid, 0) + 1
    chosen = None
    for partner in partners:
        if isinstance(partner, dict) and _identifier(partner.get('partner_id')) and counts[partner['partner_id']] > 1:
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible'] and (chosen is None or
                (estimate['eta_minutes'], estimate['partner_id']) < (chosen['eta_minutes'], chosen['partner_id'])):
            chosen = estimate
    if chosen is None:
        return {**result, 'reason': 'no eligible partner: check activity, capacity, workload, identifiers and required travel times'}
    return {**result, 'partner_id': chosen['partner_id'], 'pickup_minutes': chosen['pickup_minutes'],
            'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    """Release only an active order, once per event ID; preserve caller input.

    Malformed state/events and unknown order IDs are exact no-ops. If the active
    order has no per-order minutes, release capacity while retaining workload.
    """
    out = deepcopy(partner)
    if not isinstance(partner, dict) or not _identifier(order_id) or not _identifier(event_id):
        return out
    if not _identifier(partner.get('partner_id')):
        return out
    history = partner.get('processed_cancellation_ids', [])
    active = partner.get('active_order_ids')
    workload = partner.get('workload_minutes')
    minutes = partner.get('minutes_by_order', {})
    if (not _ids(history) or event_id in history or not _ids(active)
            or order_id not in active or not _time(workload) or not isinstance(minutes, dict)):
        return out
    released = minutes.get(order_id, 0)
    if not _time(released):
        return out
    try:
        remaining = max(0, workload - released)
    except OverflowError:
        return out
    if not _time(remaining):
        return out
    out['active_order_ids'].remove(order_id)
    out['workload_minutes'] = remaining
    out.setdefault('minutes_by_order', {}).pop(order_id, None)
    out['processed_cancellation_ids'] = [*history, event_id]
    return out
