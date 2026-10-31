"""Optional stretch feature: transparent, deterministic candidate explanations.

Core dispatch return shapes remain unchanged. This module reports the same
eligibility rules and delegates numerical ETA calculation to service.py.
"""
from service import assign_order, estimate_eta, _valid_order, _valid_partner, _minutes


def explain_dispatch(order, partners, travel, now=0):
    """Return a decision and one explanation per candidate, without mutation.

    Each row includes partner_id, eligible, pickup_minutes, eta_minutes,
    status, and reason. Input order does not affect candidate presentation.
    """
    decision = assign_order(order, partners, travel, now)
    candidates = []
    if not isinstance(partners, (list, tuple)):
        return {'decision': decision, 'candidates': candidates}

    for partner in partners:
        pid = partner.get('partner_id') if isinstance(partner, dict) else None
        eta = estimate_eta(order, partner, travel, now)
        reason = None
        if not _valid_order(order):
            reason = 'Invalid order'
        elif not isinstance(travel, dict) or not _minutes(now):
            reason = 'Invalid dispatch input'
        elif not isinstance(partner, dict):
            reason = 'Malformed partner record'
        elif partner.get('active') is not True:
            reason = 'Inactive partner'
        elif not _valid_partner(partner):
            orders = partner.get('active_order_ids')
            capacity = partner.get('capacity')
            if (isinstance(orders, list) and type(capacity) is int
                    and capacity >= 1 and len(orders) >= capacity):
                reason = 'Full capacity'
            else:
                reason = 'Invalid partner data'
        else:
            leg1 = travel.get((partner['zone'], order['restaurant_id']))
            leg2 = travel.get((order['restaurant_id'], order['destination_zone']))
            if leg1 is None or leg2 is None:
                reason = 'Missing travel data'
            elif not (_minutes(leg1) and _minutes(leg2)):
                reason = 'Invalid travel time'
            elif not eta['eligible']:
                reason = 'ETA overflow or invalid data'

        if reason:
            status = 'REJECTED'
        elif pid == decision.get('partner_id'):
            status = 'SELECTED'
            reason = 'Lowest eligible ETA (partner ID breaks ties)'
        else:
            status = 'ELIGIBLE'
            reason = 'Valid candidate; another partner ranks first'
        candidates.append({
            'partner_id': pid, 'eligible': eta['eligible'],
            'pickup_minutes': eta.get('pickup_minutes'),
            'eta_minutes': eta['eta_minutes'], 'status': status,
            'reason': reason,
        })

    # Sorting makes the inspector stable when candidate input order changes.
    candidates.sort(key=lambda c: (c['partner_id'] is None, str(c['partner_id'])))
    return {'decision': decision, 'candidates': candidates}
