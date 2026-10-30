import math
from copy import deepcopy


def is_valid_time(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
        and math.isfinite(value)
    )


def is_valid_id(value):
    return isinstance(value, str) and value.strip() != ""


def estimate_eta(order, partner, travel, now=0):
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None

    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    if not is_valid_time(now):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    prep = order.get('prep_minutes', 0)
    if not is_valid_time(prep):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    if not is_valid_time(workload):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))

    if not is_valid_time(leg1) or not is_valid_time(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {
            'order_id': None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    order_id = order.get('order_id')
    if (
        not is_valid_id(order_id)
        or not is_valid_id(order.get('restaurant_id'))
        or not is_valid_id(order.get('destination_zone'))
        or not is_valid_time(order.get('prep_minutes'))
        or not is_valid_time(now)
    ):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    if not isinstance(partners, (list, tuple)):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    options = []
    for partner in partners:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue
        capacity = partner.get('capacity')
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue
        active_orders = partner.get('active_order_ids')
        if active_orders is None:
            active_orders = []
        if not isinstance(active_orders, (list, tuple, set)):
            continue
        if len(active_orders) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get('eligible'):
            options.append(estimate)

    if not options:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return partner
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    if event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        deduction = out.get('minutes_by_order', {}).get(order_id, 0)
        current_workload = out.get('workload_minutes', 0)
        if isinstance(deduction, (int, float)) and not isinstance(deduction, bool):
            out['workload_minutes'] = max(0, current_workload - deduction)
        else:
            out['workload_minutes'] = max(0, current_workload)

    out['processed_cancellation_ids'].append(event_id)
    return out
