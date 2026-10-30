from copy import deepcopy


def _is_valid_id(value):
    return isinstance(value, str) and value.strip() != ""


def _is_valid_non_negative_number(value):
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    if value != value or value in (float("inf"), float("-inf")):
        return False
    return value >= 0


def _is_valid_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return {'partner_id': None, 'eta_minutes': None, 'eligible': False}

    if not _is_valid_id(partner.get('partner_id')):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not _is_valid_id(order.get('order_id')) or not _is_valid_id(order.get('restaurant_id')):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not _is_valid_id(order.get('destination_zone')) or not _is_valid_id(partner.get('zone')):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not _is_valid_non_negative_number(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}
    if not _is_valid_non_negative_number(order.get('prep_minutes', 0)):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + order.get('prep_minutes', 0) + leg2,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order data'}

    if not _is_valid_id(order.get('order_id')) or not _is_valid_id(order.get('restaurant_id')) or not _is_valid_id(order.get('destination_zone')):
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order data'}
    if not _is_valid_non_negative_number(now):
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid current time'}
    if not _is_valid_non_negative_number(order.get('prep_minutes', 0)):
        return {'order_id': order.get('order_id'), 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid prep time'}

    options = []
    for partner in partners or []:
        if not isinstance(partner, dict):
            continue
        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity', 2)
        if not _is_valid_positive_int(capacity):
            continue

        active_order_ids = partner.get('active_order_ids', [])
        if not isinstance(active_order_ids, list):
            continue
        if len(active_order_ids) >= capacity:
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get('eligible'):
            options.append(estimate)

    if not options:
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {
        'order_id': order.get('order_id'),
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('minutes_by_order', {})
    out.setdefault('processed_cancellation_ids', [])

    if not isinstance(out.get('active_order_ids'), list):
        out['active_order_ids'] = []
    if not isinstance(out.get('minutes_by_order'), dict):
        out['minutes_by_order'] = {}
    if not isinstance(out.get('processed_cancellation_ids'), list):
        out['processed_cancellation_ids'] = []

    if event_id in out['processed_cancellation_ids']:
        return out

    if order_id not in out['active_order_ids']:
        return out

    out['active_order_ids'].remove(order_id)
    released_minutes = out.get('minutes_by_order', {}).get(order_id, 0)
    if not _is_valid_non_negative_number(released_minutes):
        released_minutes = 0

    workload = out.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        workload = 0
    out['workload_minutes'] = max(0, workload - released_minutes)
    out['minutes_by_order'].pop(order_id, None)
    out['processed_cancellation_ids'].append(event_id)
    return out
