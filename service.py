from copy import deepcopy
import math


def _is_valid_non_negative_number(val):
    if val is None or isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    if not math.isfinite(val):
        return False
    return val >= 0


def _is_valid_id(val):
    return isinstance(val, str) and len(val.strip()) > 0


def estimate_eta(order, partner, travel, now=0):
    if not _is_valid_non_negative_number(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    prep = order.get('prep_minutes', 0) if order else 0
    if not _is_valid_non_negative_number(prep):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0) if partner else 0
    if not _is_valid_non_negative_number(workload):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    partner_zone = partner.get('zone') if partner else None
    rest_id = order.get('restaurant_id') if order else None
    dest_zone = order.get('destination_zone') if order else None

    leg1 = travel.get((partner_zone, rest_id)) if travel is not None else None
    leg2 = travel.get((rest_id, dest_zone)) if travel is not None else None

    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    pickup = now + leg1 + workload
    eta = pickup + prep + leg2
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not order or not isinstance(order, dict):
        return {'order_id': None, 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order'}

    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    prep_minutes = order.get('prep_minutes', 0)

    if (
        not _is_valid_id(order_id)
        or not _is_valid_id(restaurant_id)
        or not _is_valid_id(destination_zone)
        or not _is_valid_non_negative_number(prep_minutes)
        or not _is_valid_non_negative_number(now)
    ):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order or time data',
        }

    options = []
    for partner in (partners or []):
        if not partner or not isinstance(partner, dict):
            continue

        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity', 2)
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            continue

        active_orders = partner.get('active_order_ids')
        if not isinstance(active_orders, list):
            active_orders = []
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
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])
    out.setdefault('minutes_by_order', {})
    out.setdefault('workload_minutes', 0)

    if event_id in out['processed_cancellation_ids']:
        return out

    out['processed_cancellation_ids'].append(event_id)

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        deduct = out.get('minutes_by_order', {}).get(order_id, 0)
        if not _is_valid_non_negative_number(deduct):
            deduct = 0
        current_workload = out.get('workload_minutes', 0)
        if not _is_valid_non_negative_number(current_workload):
            current_workload = 0
        out['workload_minutes'] = max(0, current_workload - deduct)

    return out


def explain_candidates(order, partners, travel, now=0):
    """Optional stretch feature: return structured explanation for each candidate partner.
    
    Explains why each partner is eligible (with pickup and ETA) or why they were
    filtered out (e.g. inactive, at capacity, missing travel routes).
    """
    explanations = {}
    if not partners:
        return explanations

    assignment = assign_order(order, partners, travel, now)
    selected_partner_id = assignment.get('partner_id')

    for partner in partners:
        if not partner or not isinstance(partner, dict):
            continue
        pid = partner.get('partner_id', 'UNKNOWN')

        if partner.get('active') is not True:
            explanations[pid] = {
                'eligible': False,
                'reason': 'partner is inactive',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        cap = partner.get('capacity', 2)
        if not (isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1):
            explanations[pid] = {
                'eligible': False,
                'reason': f'invalid capacity: {cap}',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        active_orders = partner.get('active_order_ids') or []
        if len(active_orders) >= cap:
            explanations[pid] = {
                'eligible': False,
                'reason': f'capacity reached ({len(active_orders)}/{cap})',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        workload = partner.get('workload_minutes', 0)
        if not _is_valid_non_negative_number(workload):
            explanations[pid] = {
                'eligible': False,
                'reason': 'invalid partner workload',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        partner_zone = partner.get('zone')
        rest_id = order.get('restaurant_id') if order else None
        dest_zone = order.get('destination_zone') if order else None

        leg1 = travel.get((partner_zone, rest_id)) if travel is not None else None
        leg2 = travel.get((rest_id, dest_zone)) if travel is not None else None

        if not _is_valid_non_negative_number(leg1):
            explanations[pid] = {
                'eligible': False,
                'reason': f'missing or invalid travel route ({partner_zone} -> {rest_id})',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        if not _is_valid_non_negative_number(leg2):
            explanations[pid] = {
                'eligible': False,
                'reason': f'missing or invalid travel route ({rest_id} -> {dest_zone})',
                'eta_minutes': None,
                'is_selected': False,
            }
            continue

        est = estimate_eta(order, partner, travel, now)
        if est.get('eligible'):
            is_winner = (pid == selected_partner_id)
            explanations[pid] = {
                'eligible': True,
                'reason': 'eligible candidate (selected - lowest ETA)' if is_winner else 'eligible candidate',
                'pickup_minutes': est['pickup_minutes'],
                'eta_minutes': est['eta_minutes'],
                'is_selected': is_winner,
            }
        else:
            explanations[pid] = {
                'eligible': False,
                'reason': 'ineligible due to order or timing constraints',
                'eta_minutes': None,
                'is_selected': False,
            }

    return explanations
