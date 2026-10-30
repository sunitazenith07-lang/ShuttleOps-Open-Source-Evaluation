from copy import deepcopy
import math


def _num(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v) and v >= 0)


def _nonempty(v):
    return v is not None and v != ''


def _id(v):
    return isinstance(v, str) and v.strip() != ''


def estimate_eta(order, partner, travel, now=0):
    pid = partner.get('partner_id') if isinstance(partner, dict) else None
    bad = {'partner_id': pid, 'eta_minutes': None, 'eligible': False}
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return bad
    if not _num(now):
        return bad
    rid, dest = order.get('restaurant_id'), order.get('destination_zone')
    prep = order.get('prep_minutes')
    work = partner.get('workload_minutes', 0)
    if not (_id(rid) and _id(dest) and _num(prep) and _num(work)):
        return bad
    try:
        leg1 = travel.get((partner.get('zone'), rid))
        leg2 = travel.get((rid, dest))
    except TypeError:
        return bad
    if not _num(leg1) or not _num(leg2):
        return bad
    pickup = now + leg1 + work
    return {'partner_id': pid, 'pickup_minutes': pickup,
            'eta_minutes': pickup + prep + leg2, 'eligible': True}


def _available(partner):
    if not isinstance(partner, dict) or not _nonempty(partner.get('partner_id')):
        return False
    if not partner.get('active', False):
        return False
    cap = partner.get('capacity')
    if not (isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1):
        return False
    active = partner.get('active_order_ids') or []
    return len(active) < cap


def assign_order(order, partners, travel, now=0):
    oid = order.get('order_id') if isinstance(order, dict) else None
    fail = lambda r: {'order_id': oid, 'partner_id': None, 'eta_minutes': None, 'reason': r}
    if not isinstance(order, dict) or not _id(oid) or not _id(order.get('restaurant_id')) \
            or not _id(order.get('destination_zone')) or not _num(order.get('prep_minutes')):
        return fail('invalid order')
    if not _num(now):
        return fail('invalid current time')
    options = []
    for partner in (partners or []):
        if not _available(partner):
            continue
        est = estimate_eta(order, partner, travel, now)
        if est['eligible']:
            options.append(est)
    if not options:
        return fail('no eligible partner or missing time data')
    chosen = min(options, key=lambda i: (i['eta_minutes'], str(i['partner_id'])))
    return {'order_id': oid, 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'],
            'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner) if isinstance(partner, dict) else {}
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    if event_id is None or event_id in out['processed_cancellation_ids']:
        return out
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        released = out.get('minutes_by_order', {}).get(order_id, 0)
        released = released if _num(released) else 0
        out['workload_minutes'] = max(0, out.get('workload_minutes', 0) - released)
    out['processed_cancellation_ids'].append(event_id)
    return out