"""SmartDispatch core service: partner eligibility, ETA, assignment, cancellation.

All records are plain dicts produced by models.new_partner()/new_order().
travel is a dict mapping (from_id, to_id) tuples to non-negative minutes.
"""
import math
from copy import deepcopy


def _is_valid_time(value):
    """A usable time value: int/float, not bool, finite, non-negative."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _is_valid_id(value):
    """Identifiers and zone labels must be non-empty strings."""
    return isinstance(value, str) and len(value) > 0


def _order_problem(order):
    """Return a reason string if the order record is invalid, else None."""
    if not isinstance(order, dict):
        return 'order record is not a dict'
    if not _is_valid_id(order.get('order_id')):
        return 'invalid order_id'
    if not _is_valid_id(order.get('restaurant_id')):
        return 'invalid restaurant_id'
    if not _is_valid_id(order.get('destination_zone')):
        return 'invalid destination_zone'
    if not _is_valid_time(order.get('prep_minutes')):
        return 'invalid prep_minutes'
    return None


def _partner_problem(partner):
    """Return a reason string if the partner cannot take an order, else None.

    Checks record shape, the active flag and capacity. Travel feasibility is
    checked separately by estimate_eta because it depends on the order.
    """
    if not isinstance(partner, dict):
        return 'partner record is not a dict'
    if not _is_valid_id(partner.get('partner_id')):
        return 'invalid partner_id'
    if not _is_valid_id(partner.get('zone')):
        return 'invalid zone'
    if partner.get('active') is not True:
        return 'partner inactive'
    capacity = partner.get('capacity')
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
        return 'invalid capacity'
    active_orders = partner.get('active_order_ids')
    if active_orders is None:
        active_orders = []
    if not isinstance(active_orders, list):
        return 'invalid active_order_ids'
    if len(active_orders) >= capacity:
        return 'partner at capacity'
    workload = partner.get('workload_minutes', 0)
    if not _is_valid_time(workload):
        return 'invalid workload_minutes'
    return None


def estimate_eta(order, partner, travel, now=0):
    """Estimate delivery ETA for one (order, partner) pair.

    Returns a dict with partner_id, eligible and eta_minutes. When eligible it
    also contains pickup_minutes; when not, eta_minutes is None and reason
    explains why. Missing travel data is never treated as zero.

    Note: this only measures time feasibility. Dispatch-level checks
    (partner_id validity, active flag, capacity) live in _partner_problem,
    which assign_order applies before trusting any estimate.
    """
    partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
    problem = _order_problem(order)
    if problem is None and not _is_valid_time(now):
        problem = 'invalid current time'
    if problem is None:
        if not isinstance(partner, dict):
            problem = 'partner record is not a dict'
        elif not _is_valid_id(partner.get('zone')):
            problem = 'invalid zone'
        elif not _is_valid_time(partner.get('workload_minutes', 0)):
            problem = 'invalid workload_minutes'
    if problem is not None:
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False, 'reason': problem}

    if not isinstance(travel, dict):
        travel = {}
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    if not _is_valid_time(leg1):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False,
                'reason': 'missing or invalid partner-to-restaurant travel time'}
    if not _is_valid_time(leg2):
        return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False,
                'reason': 'missing or invalid restaurant-to-customer travel time'}

    pickup = now + leg1 + partner.get('workload_minutes', 0)
    return {'partner_id': partner_id, 'pickup_minutes': pickup,
            'eta_minutes': pickup + order.get('prep_minutes', 0) + leg2, 'eligible': True}


def _evaluations(order, partners, travel, now=0):
    """Per-partner evaluation: why each candidate was accepted or rejected."""
    evaluations = []
    if not isinstance(partners, (list, tuple)):
        return evaluations
    for partner in partners:
        partner_id = partner.get('partner_id') if isinstance(partner, dict) else None
        problem = _partner_problem(partner)
        if problem is not None:
            evaluations.append({'partner_id': partner_id, 'eligible': False,
                                'eta_minutes': None, 'reason': problem})
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            evaluations.append({'partner_id': partner_id, 'eligible': True,
                                'pickup_minutes': estimate['pickup_minutes'],
                                'eta_minutes': estimate['eta_minutes'],
                                'reason': 'eligible'})
        else:
            evaluations.append({'partner_id': partner_id, 'eligible': False,
                                'eta_minutes': None,
                                'reason': estimate.get('reason', 'unknown')})
    return evaluations


def evaluate_candidates(order, partners, travel, now=0):
    """Evaluate every partner, returning (candidates, rejection_counts).

    candidates are eligible estimate dicts; rejection_counts maps each
    rejection reason to how many partners failed for it.
    """
    order_problem = _order_problem(order)
    if order_problem is not None:
        return [], {'invalid order: ' + order_problem: 1}
    evaluations = _evaluations(order, partners, travel, now)
    candidates = [e for e in evaluations if e['eligible']]
    rejection_counts = {}
    for e in evaluations:
        if not e['eligible']:
            rejection_counts[e['reason']] = rejection_counts.get(e['reason'], 0) + 1
    return candidates, rejection_counts


def assign_order(order, partners, travel, now=0):
    """Assign the order to the eligible partner with the lowest ETA.

    Ties break by partner_id in ascending lexicographical order. Returns a
    result dict; when no partner is eligible partner_id/eta_minutes are None
    and reason explains the rejection counts.
    """
    order_id = order.get('order_id') if isinstance(order, dict) else None
    order_problem = _order_problem(order)
    if order_problem is not None:
        return {'order_id': order_id, 'partner_id': None, 'pickup_minutes': None,
                'eta_minutes': None, 'reason': 'invalid order: ' + order_problem}
    candidates, rejection_counts = evaluate_candidates(order, partners, travel, now)
    if not candidates:
        if rejection_counts:
            detail = ', '.join(f'{reason} ({count})' for reason, count in sorted(rejection_counts.items()))
            reason = 'no eligible partner: ' + detail
        else:
            reason = 'no partners available'
        return {'order_id': order_id, 'partner_id': None, 'pickup_minutes': None,
                'eta_minutes': None, 'reason': reason}
    chosen = min(candidates, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))
    return {'order_id': order_id, 'partner_id': chosen['partner_id'],
            'pickup_minutes': chosen['pickup_minutes'], 'eta_minutes': chosen['eta_minutes'],
            'reason': 'assigned'}


def explain_assignment(order, partners, travel, now=0):
    """Stretch feature: assign_order result plus a per-candidate explanation.

    Returns the same assignment dict as assign_order, extended with a
    'candidates' list showing each partner's eligibility verdict and either
    its ETA or its rejection reason.
    """
    result = assign_order(order, partners, travel, now)
    result['candidates'] = _evaluations(order, partners, travel, now)
    return result


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation event to a copy of the partner record.

    Idempotent: an event_id already in processed_cancellation_ids is ignored,
    so a duplicated event cannot release workload twice. Valid workload never
    goes below zero; a malformed workload is preserved, not coerced. Unknown
    orders are recorded but change nothing.
    """
    if not isinstance(partner, dict):
        return partner
    out = deepcopy(partner)
    out.setdefault('processed_cancellation_ids', [])
    if not isinstance(out['processed_cancellation_ids'], list):
        out['processed_cancellation_ids'] = []
    if event_id in out['processed_cancellation_ids']:
        return out
    if not isinstance(out.get('active_order_ids'), list):
        out['active_order_ids'] = []
    if order_id in out['active_order_ids']:
        out['active_order_ids'].remove(order_id)
        minutes_by_order = out.get('minutes_by_order')
        release = 0
        if isinstance(minutes_by_order, dict):
            try:
                release = minutes_by_order.pop(order_id, 0)
            except TypeError:
                # Unhashable order_id can never be a dict key; release nothing.
                release = 0
        if not _is_valid_time(release):
            release = 0
        current = out.get('workload_minutes', 0)
        # A malformed workload is left as-is rather than coerced to 0; the
        # partner stays ineligible via _partner_problem until it is corrected.
        if _is_valid_time(current):
            out['workload_minutes'] = max(0, current - release)
    out['processed_cancellation_ids'].append(event_id)
    return out
