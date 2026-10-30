from copy import deepcopy


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_valid_time(value):
    """Return True only if value is a usable non-negative real number.

    A valid time (travel time, prep time, workload, or 'now') must be:
    - A number (int or float), not None, not a string
    - NOT a boolean (True/False are secretly ints in Python, but not valid times)
    - NOT NaN  (Not a Number — any math with NaN produces more NaN)
    - NOT infinite (float('inf') is not a usable duration)
    - Zero or positive (negative time is physically impossible)
    """
    # Booleans are a subclass of int in Python (True == 1, False == 0).
    # We must check for bool BEFORE checking isinstance(..., int) or True/False
    # would slip through as valid time values of 1 and 0.
    if isinstance(value, bool):
        return False

    # Must be a real number — rejects None, strings, lists, etc.
    if not isinstance(value, (int, float)):
        return False

    # NaN is the only value in Python that is not equal to itself.
    # This single line detects it without needing to import math.
    if value != value:
        return False

    # Positive and negative infinity are not usable time values.
    if value == float('inf') or value == float('-inf'):
        return False

    # Time cannot be negative.
    if value < 0:
        return False

    return True


def is_valid_id(value):
    """Return True only if value is a non-empty string.

    Order IDs, restaurant IDs, and zone names must be real, non-empty text.
    Rejects: None, empty string '', integers (like 0), booleans.
    """
    return isinstance(value, str) and len(value) > 0


def is_valid_capacity(value):
    """Return True only if value is a positive integer (not a boolean).

    A capacity of 0 or below means the partner can never take orders.
    Floats (like 1.5) and booleans (True/False) are not valid capacities.
    """
    # Booleans must be checked first — isinstance(True, int) is True in Python.
    if isinstance(value, bool):
        return False

    # Must be a whole integer — float like 1.5 is not valid.
    if not isinstance(value, int):
        return False

    # Must be at least 1 — a capacity of 0 means no orders can ever be taken.
    if value < 1:
        return False

    return True


# ---------------------------------------------------------------------------
# Core service functions
# ---------------------------------------------------------------------------

def estimate_eta(order, partner, travel, now=0):
    """Calculate the estimated delivery time for one partner on one order.

    Returns a dict with:
    - eligible (bool): whether this partner can be used for this order
    - eta_minutes: the full ETA, or None if ineligible
    - pickup_minutes: when the partner arrives at the restaurant, or None
    - partner_id: the partner's ID

    Formula (when eligible):
        pickup = now + leg1 + partner_workload
        ETA    = pickup + prep_minutes + leg2
    """
    # --- Validate 'now' (current time) ---
    # 'now' must be a non-negative real number. A negative, string, bool,
    # or None value for the current time makes no sense.
    if not is_valid_time(now):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # --- Validate prep_minutes ---
    # The food preparation time must be a non-negative real number.
    # A string, negative value, boolean, NaN, or infinity is invalid.
    prep = order.get('prep_minutes')
    if not is_valid_time(prep):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # --- Look up travel times ---
    # leg1: from the partner's current zone to the restaurant
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    # leg2: from the restaurant to the customer's destination zone
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))

    # --- Validate both travel legs ---
    # If either route is missing (None) or holds an invalid value (negative,
    # boolean, string, NaN, infinity), the partner cannot be given a reliable ETA.
    # Missing travel data must NEVER be treated as zero.
    if not is_valid_time(leg1) or not is_valid_time(leg2):
        return {'partner_id': partner.get('partner_id'), 'eta_minutes': None, 'eligible': False}

    # --- Calculate pickup time and ETA ---
    # pickup: the moment the partner physically arrives at the restaurant.
    # They must first finish their remaining workload, then travel to the restaurant.
    pickup = now + leg1 + partner.get('workload_minutes', 0)

    # Full ETA: pickup time + food prep time + travel from restaurant to customer.
    return {
        'partner_id': partner.get('partner_id'),
        'pickup_minutes': pickup,
        'eta_minutes': pickup + prep + leg2,
        'eligible': True
    }


def assign_order(order, partners, travel, now=0):
    """Choose the best eligible delivery partner for an order.

    Eligibility rules for partners:
    1. Must be active (active == True or any truthy value that is literally True)
    2. Must have a valid capacity (positive integer, not bool)
    3. Must not have reached their capacity (current orders < capacity)
    4. Must have valid travel routes for both legs

    Eligibility rules for the order:
    1. order_id, restaurant_id, destination_zone must be non-empty strings
    2. prep_minutes must be a non-negative real number

    Selection: pick the partner with the lowest ETA.
    Tie-breaking: if two partners have identical ETAs, pick the one whose
    partner_id is alphabetically smaller (lexicographic ascending order).
    """
    # --- Validate the order first ---
    # If the order itself is malformed, we cannot assign anyone.
    # We check all identifying fields before touching the partner list.
    if not is_valid_id(order.get('order_id')):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order'
        }
    if not is_valid_id(order.get('restaurant_id')):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order'
        }
    if not is_valid_id(order.get('destination_zone')):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order'
        }
    if not is_valid_time(order.get('prep_minutes')):
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'invalid order'
        }

    # --- Filter and score each partner ---
    options = []
    for partner in partners:

        # Rule 1: Partner must be active.
        # 'not partner.get("active")' is True for False, 0, None, and missing key.
        # Only True (the boolean) passes without being skipped.
        if not partner.get('active'):
            continue

        # Rule 2: Capacity must be a valid positive integer.
        if not is_valid_capacity(partner.get('capacity')):
            continue

        # Rule 3: Partner must not be at or over their capacity limit.
        # Example: capacity=2, active_order_ids=['A','B'] → 2 >= 2 → FULL → skip.
        active_count = len(partner.get('active_order_ids', []))
        if active_count >= partner.get('capacity'):
            continue

        # Rules 1-3 passed. Now calculate ETA (travel validation happens inside).
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    # --- No eligible partner found ---
    if not options:
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }

    # --- Pick the best partner ---
    # min() with a tuple key: first sort by ETA (lower is better),
    # then by partner_id as string if ETAs are equal (alphabetically first wins).
    chosen = min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))

    return {
        'order_id': order.get('order_id'),
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation event to a partner's state.

    This function is idempotent: calling it with the same event_id twice
    produces exactly the same result as calling it once. The second call
    is a complete no-op — it changes nothing.

    Steps:
    1. If this event_id has already been processed, return immediately.
    2. If the order is in the partner's active list, remove it and reduce workload.
    3. Record the event_id so future duplicate calls are ignored.
    """
    # deepcopy creates a fully independent copy of the partner dict.
    # This ensures we never modify the caller's original data.
    out = deepcopy(partner)
    out.setdefault('active_order_ids', [])
    out.setdefault('processed_cancellation_ids', [])

    # --- Idempotency guard ---
    # If we have already processed this exact event_id, do absolutely nothing.
    # Return the unchanged copy immediately. This prevents:
    #   - Double-removal of the order from active_order_ids
    #   - Double-reduction of workload_minutes
    #   - Duplicate entries in processed_cancellation_ids
    if event_id in out['processed_cancellation_ids']:
        return out

    # --- Apply the cancellation ---
    # Only remove the order and reduce workload if the order is actually present.
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        # max(0, ...) ensures workload never goes below zero (clamps to zero floor).
        out['workload_minutes'] = max(
            0,
            out.get('workload_minutes', 0) - out.get('minutes_by_order', {}).get(order_id, 0)
        )

    # Record the event so any future duplicate call is caught by the guard above.
    out['processed_cancellation_ids'].append(event_id)
    return out
