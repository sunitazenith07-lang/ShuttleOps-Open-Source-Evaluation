"""SmartDispatch core service.

Implements delivery partner ETA estimation, order assignment,
capacity validation, and idempotent cancellation processing.
"""
from copy import deepcopy
import math


def _is_valid_non_negative_number(val):
    """Check if a value is a valid non-negative integer or float."""
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        return False
    if math.isnan(val) or math.isinf(val):
        return False
    return val >= 0


def _is_valid_id(val):
    """Check if an identifier is a non-empty string."""
    return isinstance(val, str) and len(val.strip()) > 0


def estimate_eta(order, partner, travel, now=0):
    """Estimate delivery pickup time and ETA for a given order and partner.

    Formula:
      Pickup time = now + partner_to_restaurant_travel + partner_workload
      ETA = Pickup time + restaurant_prep_time + restaurant_to_customer_travel
    """
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    partner_id = partner.get('partner_id')

    # Validate current simulation time
    if not _is_valid_non_negative_number(now):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    # Validate restaurant preparation time
    prep = order.get('prep_minutes', 0)
    if not _is_valid_non_negative_number(prep):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    # Retrieve travel times for both legs
    partner_zone = partner.get('zone')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')

    leg1 = travel.get((partner_zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))

    # Travel time data must exist and be valid non-negative numbers
    if not _is_valid_non_negative_number(leg1) or not _is_valid_non_negative_number(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}

    workload = partner.get('workload_minutes', 0)
    if not _is_valid_non_negative_number(workload):
        workload = 0

    pickup = now + leg1 + workload
    eta = pickup + prep + leg2

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    """Assign an order to the eligible partner with the lowest ETA.

    Breaks ties by partner ID in ascending lexicographic order.
    Returns an unassigned explanation if no partner is eligible.
    """
    if not isinstance(order, dict):
        return {
            'order_id': None,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order input',
        }

    order_id = order.get('order_id')
    restaurant_id = order.get('restaurant_id')
    destination_zone = order.get('destination_zone')
    prep = order.get('prep_minutes', 0)

    # Validate order fields
    if (
        not _is_valid_id(order_id)
        or not _is_valid_id(restaurant_id)
        or not _is_valid_id(destination_zone)
        or not _is_valid_non_negative_number(prep)
        or not _is_valid_non_negative_number(now)
    ):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order or time fields',
        }

    if not partners or not isinstance(partners, (list, tuple)):
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

        # 1. Partner must be active (explicitly boolean True)
        if partner.get('active') is not True:
            continue

        # 2. Capacity must be a valid integer >= 1 (not boolean)
        capacity = partner.get('capacity', 2)
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            continue

        # 3. Partner must have remaining capacity (current orders < capacity)
        active_orders = partner.get('active_order_ids', [])
        if not isinstance(active_orders, list) or len(active_orders) >= capacity:
            continue

        # 4. Check route availability and estimate ETA
        estimate = estimate_eta(order, partner, travel, now=now)
        if estimate.get('eligible'):
            options.append(estimate)

    if not options:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    # Deterministic tie-breaking: lowest ETA first, then partner_id ascending lexicographically
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))

    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    """Process an order cancellation event idempotently.

    Releases the order from partner active orders and decrements workload once.
    Duplicate cancellation events are ignored.
    """
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    # Idempotency check: event_id must be processed only once
    if event_id in out['processed_cancellation_ids']:
        return out

    # If the cancelled order is active, release workload and capacity
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        deduction = out.get('minutes_by_order', {}).get(order_id, 0)
        current_workload = out.get('workload_minutes', 0)
        out['workload_minutes'] = max(0, current_workload - deduction)

    # Record the cancellation event ID
    out['processed_cancellation_ids'].append(event_id)
    return out
