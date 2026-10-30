"""Pure dispatch decisions and copy-on-cancel partner updates."""

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite


def _identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _minutes(value):
    # bool is an int subclass, but is not a time value. Avoid converting large ints.
    return (isinstance(value, int) and not isinstance(value, bool) and value >= 0) or (
        isinstance(value, float) and isfinite(value) and value >= 0
    )


def _identifiers(value):
    return (isinstance(value, list) and all(_identifier(item) for item in value)
            and len(value) == len(set(value)))


def _valid_order(order):
    return (isinstance(order, Mapping)
            and all(_identifier(order.get(field)) for field in
                    ('order_id', 'restaurant_id', 'destination_zone'))
            and _minutes(order.get('prep_minutes')))


def estimate_eta(order, partner, travel, now=0):
    """Return a validated candidate estimate, including a rejection reason."""
    result = {
        'partner_id': partner.get('partner_id') if isinstance(partner, Mapping) else None,
        'eta_minutes': None, 'eligible': False,
    }

    def reject(reason):
        return dict(result, reason=reason)

    if not _valid_order(order):
        return reject('invalid order')
    if not _minutes(now):
        return reject('invalid current time')
    if not isinstance(partner, Mapping) or not all(
        _identifier(partner.get(field)) for field in ('partner_id', 'zone')
    ):
        return reject('invalid partner')
    if partner.get('active') is not True:
        return reject('inactive partner')
    capacity = partner.get('capacity')
    active_orders = partner.get('active_order_ids', [])
    if (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1
            or not _identifiers(active_orders)):
        return reject('invalid capacity or active orders')
    if len(active_orders) >= capacity:
        return reject('partner at capacity')
    workload = partner.get('workload_minutes', 0)
    if not _minutes(workload):
        return reject('invalid workload')
    if not isinstance(travel, Mapping):
        return reject('invalid travel data')
    leg1 = travel.get((partner['zone'], order['restaurant_id']))
    leg2 = travel.get((order['restaurant_id'], order['destination_zone']))
    if leg1 is None or leg2 is None:
        return reject('missing travel time')
    if not _minutes(leg1) or not _minutes(leg2):
        return reject('invalid travel time')
    try:
        pickup = now + leg1 + workload
        eta = pickup + order['prep_minutes'] + leg2
    except OverflowError:
        return reject('time calculation overflow')
    if not _minutes(pickup) or not _minutes(eta):
        return reject('time calculation overflow')
    return {'partner_id': partner['partner_id'], 'pickup_minutes': pickup,
            'eta_minutes': eta, 'eligible': True}


def assign_order(order, partners, travel, now=0):
    """Select a partner without reserving capacity or changing caller inputs."""
    unassigned = {
        'order_id': order.get('order_id') if isinstance(order, Mapping) else None,
        'partner_id': None, 'eta_minutes': None,
        'reason': 'no eligible partner or missing time data',
    }
    if not _valid_order(order):
        return dict(unassigned, reason='invalid order')
    if not _minutes(now):
        return dict(unassigned, reason='invalid current time')
    if not isinstance(partners, (list, tuple)):
        return dict(unassigned, reason='invalid partner collection')
    options = []
    for partner in partners:
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)
    if not options:
        return unassigned
    chosen = min(options, key=lambda item: (item['eta_minutes'], item['partner_id']))
    return {'order_id': order['order_id'], 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'],
            'eta_minutes': chosen['eta_minutes'], 'reason': 'assigned'}


def explain_assignment(order, partners, travel, now=0):
    """Add one explanation per input candidate without changing assign_order.

    Rows retain input order. ``eligible`` describes validation, while ``selected``
    identifies the winner. Only the first row wins an identical ID/ETA tie.
    """
    assignment = assign_order(order, partners, travel, now)
    candidates = []
    if isinstance(partners, (list, tuple)):
        candidates = [
            dict(estimate_eta(order, partner, travel, now),
                 candidate_index=index, selected=False)
            for index, partner in enumerate(partners)
        ]
    winner_recorded = False
    for candidate in candidates:
        if not candidate['eligible']:
            continue
        if (not winner_recorded
                and candidate['partner_id'] == assignment['partner_id']
                and candidate['eta_minutes'] == assignment['eta_minutes']):
            candidate.update(selected=True, reason='selected by ETA and partner ID')
            winner_recorded = True
        elif candidate['eta_minutes'] > assignment['eta_minutes']:
            candidate['reason'] = 'higher ETA than selected partner'
        elif candidate['partner_id'] != assignment['partner_id']:
            candidate['reason'] = 'equal ETA; earlier partner ID selected'
        else:
            candidate['reason'] = 'equal ETA and partner ID; earlier candidate selected'
    return dict(assignment, candidates=candidates)


def process_cancellation(partner, order_id, event_id):
    """Apply a valid event once; malformed events/state leave a copy unchanged.

    Event IDs are scoped to this partner's supplied history. Unknown-order events
    are recorded, so their ID cannot later cancel a different order.
    """
    out = deepcopy(partner)
    if not isinstance(out, dict) or not _identifier(order_id) or not _identifier(event_id):
        return out
    processed = out.get('processed_cancellation_ids', [])
    if not _identifiers(processed) or event_id in processed:
        return out
    active_orders = out.get('active_order_ids', [])
    workload = out.get('workload_minutes', 0)
    minutes_by_order = out.get('minutes_by_order', {})
    if (not _identifiers(active_orders) or not _minutes(workload)
            or not isinstance(minutes_by_order, dict)):
        return out
    if order_id in active_orders:
        released = minutes_by_order.get(order_id)
        if not _minutes(released):
            return out
        try:
            remaining = max(0, workload - released)
        except OverflowError:
            return out
        active_orders.remove(order_id)
        out['workload_minutes'] = remaining
        minutes_by_order.pop(order_id)
    out['active_order_ids'] = active_orders
    out['processed_cancellation_ids'] = processed + [event_id]
    return out
