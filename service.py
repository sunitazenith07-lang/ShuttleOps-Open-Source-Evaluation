from copy import deepcopy
import math


def estimate_eta(order, partner, travel, now=0):
    """Estimate pickup and delivery time for one partner-order pair.

    Returns an ineligible result when required identifiers, route times, or
    other time inputs are missing or invalid.
    """
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None

    def valid_minutes(value):
        # bool is a subclass of int, so require an exact numeric type.
        if type(value) not in (int, float) or value < 0:
            return False
        # Integers are finite by definition; check floats for NaN/infinity.
        return type(value) is int or math.isfinite(value)

    def ineligible_result():
        return {
            'partner_id': partner_id,
            'eta_minutes': None,
            'eligible': False,
        }

    # Validate record shapes before reading fields or looking up routes.
    if not isinstance(order, dict) or not isinstance(partner, dict) or not isinstance(travel, dict):
        return ineligible_result()

    # Identifiers must be present and non-empty before route lookup.
    required_ids = (
        order.get('order_id'),
        order.get('restaurant_id'),
        order.get('destination_zone'),
        partner.get('partner_id'),
        partner.get('zone'),
    )
    if any(not isinstance(value, str) or not value.strip() for value in required_ids):
        return ineligible_result()

    prep_minutes = order.get('prep_minutes', 0)
    workload_minutes = partner.get('workload_minutes', 0)
    if not all(valid_minutes(value) for value in (now, prep_minutes, workload_minutes)):
        return ineligible_result()

    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if not valid_minutes(leg1) or not valid_minutes(leg2):
        return ineligible_result()

    pickup = now + leg1 + workload_minutes
    eta = pickup + prep_minutes + leg2

    # Guard against floating-point overflow in the calculated results.
    if not valid_minutes(pickup) or not valid_minutes(eta):
        return ineligible_result()

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def assign_order(order, partners, travel, now=0):
    """Assign an order to the best active partner with remaining capacity.

    Candidates need valid ETA inputs, an explicitly active status, a valid
    positive-integer capacity, and fewer active orders than that capacity.
    Lowest ETA wins; partner ID provides deterministic tie-breaking.
    """
    order_id = order.get('order_id') if isinstance(order, dict) else None

    # Malformed top-level inputs cannot produce a safe assignment.
    if not isinstance(order, dict) or not isinstance(travel, dict):
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order or travel data',
        }

    if not isinstance(partners, (list, tuple)):
        partners = []

    options = []
    for partner in partners:
        if not isinstance(partner, dict):
            continue

        # Only the literal Boolean True means that a partner is active.
        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity')
        active_order_ids = partner.get('active_order_ids')
        if type(capacity) is not int or capacity < 1:
            continue
        if not isinstance(active_order_ids, (list, tuple, set, frozenset)):
            continue
        if len(active_order_ids) >= capacity:
            continue

        partner_id = partner.get('partner_id')
        if not isinstance(partner_id, str) or not partner_id.strip():
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get('eligible') is True:
            options.append(estimate)

    if not options:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data',
        }

    chosen = min(
        options,
        key=lambda item: (item['eta_minutes'], item['partner_id']),
    )
    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation once and return an updated partner copy.

    Repeated event IDs are ignored, including when a repeated event carries a
    different order ID. Invalid event/order identifiers are treated as no-ops.
    """
    out = deepcopy(partner)
    if not isinstance(out, dict):
        return out

    active_order_ids = out.get('active_order_ids')
    if isinstance(active_order_ids, tuple):
        active_order_ids = list(active_order_ids)
        out['active_order_ids'] = active_order_ids
    elif not isinstance(active_order_ids, list):
        active_order_ids = []
        out['active_order_ids'] = active_order_ids

    processed_ids = out.get('processed_cancellation_ids')
    if isinstance(processed_ids, tuple):
        processed_ids = list(processed_ids)
        out['processed_cancellation_ids'] = processed_ids
    elif not isinstance(processed_ids, list):
        processed_ids = []
        out['processed_cancellation_ids'] = processed_ids

    # A valid event ID is the idempotency key for the cancellation operation.
    if not isinstance(event_id, str) or not event_id.strip():
        return out
    if event_id in processed_ids:
        return out

    # Record a new event even if its order is unknown, so replaying the same
    # event cannot later apply a different payload.
    processed_ids.append(event_id)

    if not isinstance(order_id, str) or not order_id.strip():
        return out
    if order_id not in active_order_ids:
        return out

    active_order_ids.remove(order_id)

    workload = out.get('workload_minutes', 0)
    minutes_by_order = out.get('minutes_by_order', {})
    if not isinstance(minutes_by_order, dict):
        minutes_by_order = {}
        out['minutes_by_order'] = minutes_by_order

    cancelled_minutes = minutes_by_order.pop(order_id, 0)

    def valid_minutes(value):
        return (
            type(value) in (int, float)
            and value >= 0
            and (type(value) is int or math.isfinite(value))
        )

    if not valid_minutes(workload):
        workload = 0
    if not valid_minutes(cancelled_minutes):
        cancelled_minutes = 0

    out['workload_minutes'] = max(0, workload - cancelled_minutes)
    return out

