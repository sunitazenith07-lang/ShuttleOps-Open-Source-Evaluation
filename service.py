
from copy import deepcopy
import math


def _valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_time(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def estimate_eta(order, partner, travel, now=0):

    def rejected(reason):
        return {
            'partner_id': partner.get('partner_id')
            if isinstance(partner, dict) else None,
            'pickup_minutes': None,
            'eta_minutes': None,
            'eligible': False,
            'reason': reason
        }

    if not isinstance(order, dict) or not isinstance(partner, dict):
        return rejected('malformed order or partner')

    if not isinstance(travel, dict):
        return rejected('invalid travel data')

    if not _valid_id(order.get('order_id')):
        return rejected('invalid order ID')

    if not _valid_id(order.get('restaurant_id')):
        return rejected('invalid restaurant ID')

    if not _valid_id(order.get('destination_zone')):
        return rejected('invalid destination zone')

    if not _valid_id(partner.get('partner_id')):
        return rejected('invalid partner ID')

    if not _valid_id(partner.get('zone')):
        return rejected('invalid partner zone')

    prep = order.get('prep_minutes')
    workload = partner.get('workload_minutes', 0)

    if not _valid_time(now):
        return rejected('invalid current time')

    if not _valid_time(prep):
        return rejected('invalid preparation time')

    if not _valid_time(workload):
        return rejected('invalid workload time')

    leg1_key = (partner['zone'], order['restaurant_id'])
    leg2_key = (order['restaurant_id'], order['destination_zone'])

    if leg1_key not in travel:
        return rejected('missing partner-to-restaurant travel data')

    if leg2_key not in travel:
        return rejected('missing restaurant-to-customer travel data')

    leg1 = travel[leg1_key]
    leg2 = travel[leg2_key]

    if not _valid_time(leg1):
        return rejected('invalid partner-to-restaurant travel time')

    if not _valid_time(leg2):
        return rejected('invalid restaurant-to-customer travel time')

    pickup = now + leg1 + workload
    eta = pickup + prep + leg2

    return {
        'partner_id': partner['partner_id'],
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
        'reason': 'eligible'
    }


def assign_order(order, partners, travel, now=0):

    order_id = order.get('order_id') if isinstance(order, dict) else None

    def unassigned(reason):
        return {
            'order_id': order_id,
            'partner_id': None,
            'pickup_minutes': None,
            'eta_minutes': None,
            'reason': reason
        }

    if not isinstance(order, dict):
        return unassigned('malformed order')

    if not _valid_id(order.get('order_id')):
        return unassigned('invalid order ID')

    if not _valid_id(order.get('restaurant_id')):
        return unassigned('invalid restaurant ID')

    if not _valid_id(order.get('destination_zone')):
        return unassigned('invalid destination zone')

    if not _valid_time(order.get('prep_minutes')):
        return unassigned('invalid preparation time')

    if not _valid_time(now):
        return unassigned('invalid current time')

    if not isinstance(partners, (list, tuple)):
        return unassigned('invalid partners list')

    if not isinstance(travel, dict):
        return unassigned('invalid travel data')

    if not partners:
        return unassigned('no partners available')

    # Count partner IDs first so duplicate IDs cannot
    # produce ambiguous assignments.
    id_counts = {}

    for partner in partners:
        if isinstance(partner, dict):
            partner_id = partner.get('partner_id')

            if _valid_id(partner_id):
                id_counts[partner_id] = id_counts.get(partner_id, 0) + 1

    options = []
    reasons = set()

    for partner in partners:

        if not isinstance(partner, dict):
            reasons.add('malformed partner')
            continue

        partner_id = partner.get('partner_id')

        if not _valid_id(partner_id):
            reasons.add('invalid partner ID')
            continue

        if id_counts.get(partner_id) != 1:
            reasons.add('duplicate partner ID')
            continue

        if partner.get('active') is not True:
            reasons.add('inactive partner')
            continue

        capacity = partner.get('capacity')
        active_orders = partner.get('active_order_ids')

        if (
            not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity < 0
        ):
            reasons.add('invalid partner capacity')
            continue

        if (
            not isinstance(active_orders, list)
            or any(not _valid_id(item) for item in active_orders)
            or len(set(active_orders)) != len(active_orders)
        ):
            reasons.add('invalid active order list')
            continue

        if len(active_orders) >= capacity:
            reasons.add('partner capacity reached')
            continue

        estimate = estimate_eta(order, partner, travel, now)

        if estimate['eligible']:
            options.append(estimate)
        else:
            reasons.add(estimate['reason'])

    if not options:
        reason = (
            'no eligible partner: ' + '; '.join(sorted(reasons))
            if reasons else 'no eligible partner'
        )

        return unassigned(reason)

    chosen = min(
        options,
        key=lambda item: (
            item['eta_minutes'],
            item['partner_id']
        )
    )

    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner, order_id, event_id):

    if not isinstance(partner, dict):
        return deepcopy(partner)

    out = deepcopy(partner)

    if not _valid_id(order_id) or not _valid_id(event_id):
        return out

    active_orders = out.get('active_order_ids')
    processed_events = out.get('processed_cancellation_ids')
    minutes_by_order = out.get('minutes_by_order')
    workload = out.get('workload_minutes')

    if not isinstance(active_orders, list):
        return out

    if not isinstance(processed_events, list):
        return out

    if not isinstance(minutes_by_order, dict):
        return out

    if not _valid_time(workload):
        return out

    if event_id in processed_events:
        return out

    # Record the cancellation event.
    out['processed_cancellation_ids'].append(event_id)

    if order_id not in active_orders:
        return out

    released = minutes_by_order.get(order_id, 0)

    if not _valid_time(released):
        # Do not partially release an invalid workload.
        return out

    out['active_order_ids'] = [
        item for item in active_orders
        if item != order_id
    ]

    out['workload_minutes'] = max(
        0,
        workload - released
    )

    out['minutes_by_order'].pop(order_id, None)

    return out
