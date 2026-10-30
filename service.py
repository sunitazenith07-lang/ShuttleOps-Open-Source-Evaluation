import math
from copy import deepcopy


def _is_valid_id(v):
    return isinstance(v, str) and v.strip() != ""


def _is_valid_time(v):
    """Finite, non-negative real number. Rejects bool, None, str, nan, inf, negatives."""
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v) and v >= 0)


def _is_valid_capacity(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


def estimate_eta(order, partner, travel, now=0):
    pid = partner.get('partner_id')

    def ineligible(reason):
        return {'partner_id': pid, 'eta_minutes': None,
                'eligible': False, 'reason': reason}

    if not _is_valid_time(now):
        return ineligible('invalid current time')
    prep = order.get('prep_minutes')
    if not _is_valid_time(prep):
        return ineligible('invalid preparation time')
    workload = partner.get('workload_minutes', 0)
    if not _is_valid_time(workload):
        return ineligible('invalid partner workload')

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if leg1 is None or leg2 is None:
        return ineligible('missing travel-time entry')   # never treated as 0
    if not (_is_valid_time(leg1) and _is_valid_time(leg2)):
        return ineligible('invalid travel time')

    pickup = now + leg1 + workload
    return {'partner_id': pid, 'pickup_minutes': pickup,
            'eta_minutes': pickup + prep + leg2, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    def unassigned(oid, reason, details=()):
        return {'order_id': oid, 'partner_id': None, 'eta_minutes': None,
                'reason': reason, 'details': list(details)}

    if not isinstance(order, dict):
        return unassigned(None, 'invalid order: malformed record')
    oid = order.get('order_id')
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        if not _is_valid_id(order.get(field)):
            return unassigned(oid, f'invalid order: {field}')
    if not _is_valid_time(order.get('prep_minutes')):
        return unassigned(oid, 'invalid order: preparation time')
    if not _is_valid_time(now):
        return unassigned(oid, 'invalid current time')

    travel = travel if isinstance(travel, dict) else {}
    options, rejected = [], []
    for partner in (partners or []):
        if not isinstance(partner, dict):
            rejected.append('malformed partner record')
            continue
        pid = partner.get('partner_id')
        if not partner.get('active'):
            rejected.append(f'{pid}: inactive')
            continue
        capacity = partner.get('capacity')
        if not _is_valid_capacity(capacity):
            rejected.append(f'{pid}: invalid capacity')
            continue
        if len(partner.get('active_order_ids') or []) >= capacity:
            rejected.append(f'{pid}: at capacity')
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if not estimate['eligible']:
            rejected.append(f"{pid}: {estimate['reason']}")
            continue
        options.append(estimate)

    if not options:
        return unassigned(oid, 'no eligible partner or missing time data', rejected)

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {'order_id': oid, 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'],
            'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    if event_id in out['processed_cancellation_ids']:
        return out                      # duplicate event: release nothing twice
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        out['workload_minutes'] = max(
            0, out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0))
    out['processed_cancellation_ids'].append(event_id)
    return out