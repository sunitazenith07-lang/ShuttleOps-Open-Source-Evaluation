from copy import deepcopy
import math


def _is_valid_non_negative_number(val):
    if val is None or isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    if val < 0 or not math.isfinite(val):
        return False
    return True


def _is_valid_identifier(val):
    return isinstance(val, str) and len(val.strip()) > 0


def _is_eligible_partner(partner):
    if not isinstance(partner, dict):
        return False
    if partner.get('active') is not True:
        return False
    capacity = partner.get('capacity')
    if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
        return False
    active_orders = partner.get('active_order_ids')
    if not isinstance(active_orders, list):
        return False
    if len(active_orders) >= capacity:
        return False
    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        return False
    zone = partner.get('zone')
    if not _is_valid_identifier(zone):
        return False
    return True


def _is_valid_order(order):
    if not isinstance(order, dict):
        return False
    if not _is_valid_identifier(order.get('order_id')):
        return False
    if not _is_valid_identifier(order.get('restaurant_id')):
        return False
    if not _is_valid_identifier(order.get('destination_zone')):
        return False
    if not _is_valid_non_negative_number(order.get('prep_minutes')):
        return False
    return True


def estimate_eta(order, partner, travel, now=0):
    ineligible = {
        'partner_id': partner.get('partner_id') if isinstance(partner, dict) else None,
        'eta_minutes': None,
        'eligible': False,
    }

    if not isinstance(order, dict) or not isinstance(partner, dict) or not hasattr(travel, 'get'):
        return ineligible

    if not _is_valid_non_negative_number(now):
        return ineligible

    prep = order.get('prep_minutes')
    if not _is_valid_non_negative_number(prep):
        return ineligible

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        return ineligible

    p_zone = partner.get('zone')
    r_id = order.get('restaurant_id')
    d_zone = order.get('destination_zone')

    if not _is_valid_identifier(p_zone) or not _is_valid_identifier(r_id) or not _is_valid_identifier(d_zone):
        return ineligible

    leg1 = travel.get((p_zone, r_id))
    leg2 = travel.get((r_id, d_zone))

    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return ineligible

    pickup = now + leg1 + workload
    eta = pickup + prep + leg2
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    if not _is_valid_order(order) or not _is_valid_non_negative_number(now):
        return {
            'order_id': order.get('order_id') if isinstance(order, dict) else None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order or time data',
        }

    if not isinstance(partners, (list, tuple)) or not hasattr(travel, 'get'):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    options = []
    for partner in partners:
        if not _is_eligible_partner(partner):
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


def explain_candidates(order, partners, travel, now=0):
    """Optional stretch feature: return detailed eligibility explanations for each candidate partner."""
    explanations = []
    if not isinstance(partners, (list, tuple)):
        return explanations

    for partner in partners:
        if not isinstance(partner, dict):
            explanations.append({'partner_id': None, 'eligible': False, 'reason': 'malformed partner record'})
            continue
        pid = partner.get('partner_id')
        if partner.get('active') is not True:
            explanations.append({'partner_id': pid, 'eligible': False, 'reason': 'partner is inactive'})
            continue
        capacity = partner.get('capacity')
        if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
            explanations.append({'partner_id': pid, 'eligible': False, 'reason': f'invalid partner capacity: {capacity}'})
            continue
        active_orders = partner.get('active_order_ids')
        if not isinstance(active_orders, list) or len(active_orders) >= capacity:
            cnt = len(active_orders) if isinstance(active_orders, list) else 0
            explanations.append({'partner_id': pid, 'eligible': False, 'reason': f'partner at capacity ({cnt}/{capacity})'})
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if not estimate.get('eligible'):
            explanations.append({'partner_id': pid, 'eligible': False, 'reason': 'missing or invalid travel time data'})
            continue
        explanations.append({
            'partner_id': pid,
            'eligible': True,
            'pickup_minutes': estimate['pickup_minutes'],
            'eta_minutes': estimate['eta_minutes'],
            'reason': 'eligible candidate',
        })
    return explanations


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return partner

    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    if not isinstance(out['active_order_ids'], list):
        out['active_order_ids'] = list(out['active_order_ids']) if hasattr(out['active_order_ids'], '__iter__') else []
    if not isinstance(out['processed_cancellation_ids'], list):
        out['processed_cancellation_ids'] = list(out['processed_cancellation_ids']) if hasattr(out['processed_cancellation_ids'], '__iter__') else []

    if event_id is not None and event_id in out['processed_cancellation_ids']:
        return out

    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        minutes_map = out.get('minutes_by_order') if isinstance(out.get('minutes_by_order'), dict) else {}
        released = minutes_map.get(order_id, 0)
        if not isinstance(released, (int, float)) or isinstance(released, bool) or not math.isfinite(released) or released < 0:
            released = 0
        current_workload = out.get('workload_minutes', 0)
        if not isinstance(current_workload, (int, float)) or isinstance(current_workload, bool) or not math.isfinite(current_workload) or current_workload < 0:
            current_workload = 0
        out['workload_minutes'] = max(0, current_workload - released)

    if event_id is not None:
        out['processed_cancellation_ids'].append(event_id)

    return out
