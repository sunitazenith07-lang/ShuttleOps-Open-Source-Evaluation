from copy import deepcopy
import math


def _is_valid_non_negative_number(val):
    if val is None or isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    return val >= 0 and math.isfinite(val)


def _is_valid_string_id(val):
    return isinstance(val, str) and len(val) > 0


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    partner_id = partner.get('partner_id')

    if not _is_valid_non_negative_number(now):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    prep_minutes = order.get('prep_minutes')
    if not _is_valid_non_negative_number(prep_minutes):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    partner_zone = partner.get('zone')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')

    leg1 = travel.get((partner_zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))

    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    eta = pickup + prep_minutes + leg2

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {
            'order_id': None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order format',
        }

    order_id = order.get('order_id')
    if not _is_valid_string_id(order_id):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order ID',
        }

    restaurant_id = order.get('restaurant_id')
    if not _is_valid_string_id(restaurant_id):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid restaurant ID',
        }

    destination_zone = order.get('destination_zone')
    if not _is_valid_string_id(destination_zone):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid destination zone',
        }

    prep_minutes = order.get('prep_minutes')
    if not _is_valid_non_negative_number(prep_minutes):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid preparation time',
        }

    if not _is_valid_non_negative_number(now):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid current time',
        }

    if partners is None or not isinstance(travel, dict):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    try:
        partners_iter = iter(partners)
    except TypeError:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    options = []
    for partner in partners_iter:
        if not isinstance(partner, dict):
            continue

        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity')
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue

        active_orders = partner.get('active_order_ids')
        active_count = len(active_orders) if isinstance(active_orders, (list, tuple, set)) else 0
        if active_count >= capacity:
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
        return {}

    out = deepcopy(partner)
    if not isinstance(out.get('active_order_ids'), list):
        out['active_order_ids'] = []
    if not isinstance(out.get('processed_cancellation_ids'), list):
        out['processed_cancellation_ids'] = []
    if not isinstance(out.get('minutes_by_order'), dict):
        out['minutes_by_order'] = {}

    if event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        current_workload = out.get('workload_minutes', 0)
        if not isinstance(current_workload, (int, float)) or isinstance(current_workload, bool):
            current_workload = 0
        deduct = out['minutes_by_order'].get(order_id, 0)
        if not isinstance(deduct, (int, float)) or isinstance(deduct, bool):
            deduct = 0
        out['workload_minutes'] = max(0, current_workload - deduct)

    out['processed_cancellation_ids'].append(event_id)
    return out


def batch_assign_orders(orders, partners, travel, now=0):
    """Optional stretch item: Batch-assign orders in supplied priority order.

    Maintains capacity and workload state dynamically across assignments.
    """
    if not isinstance(orders, (list, tuple)):
        return []

    current_partners = deepcopy(partners) if partners is not None else []
    results = []

    for order in orders:
        assignment = assign_order(order, current_partners, travel, now)
        results.append(assignment)

        assigned_id = assignment.get('partner_id')
        if assigned_id is not None:
            for p in current_partners:
                if isinstance(p, dict) and p.get('partner_id') == assigned_id:
                    active_ids = p.setdefault('active_order_ids', [])
                    active_ids.append(order.get('order_id'))
                    order_minutes = (assignment.get('pickup_minutes', 0) - now) + order.get('prep_minutes', 0)
                    p.setdefault('minutes_by_order', {})[order.get('order_id')] = order_minutes
                    p['workload_minutes'] = p.get('workload_minutes', 0) + order_minutes
                    break

    return results
