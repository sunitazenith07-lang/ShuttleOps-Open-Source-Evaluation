import math

def is_valid_number(value):
    """Accept finite, non-negative integers and floats, excluding bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    if isinstance(value, float):
        return math.isfinite(value) and value >= 0

    return value >= 0

def invalid_eta(partner):
    return{
        'partner_id': partner.get('partner_id'),
        'eta_minutes': None,
        'eligible': False
    }

def estimate_eta(order, partner, travel, now=0):

    # validate order fields
    for field in ('order_id', 'restaurant_id', 'destination_zone'):
        if not isinstance(order.get(field), str) or not order.get(field).strip():
            return invalid_eta(partner)
    prep = order.get('prep_minutes')
    if not is_valid_number(prep):
        return invalid_eta(partner)
    if not is_valid_number(now):
        return invalid_eta(partner)

    leg1=travel.get((partner.get('zone'),order.get('restaurant_id')))
    leg2=travel.get((order.get('restaurant_id'),order.get('destination_zone')))

    if not is_valid_number(leg1) or not is_valid_number(leg2):
        return invalid_eta(partner)

    workload = partner.get('workload_minutes', 0)

    if not is_valid_number(workload):
        return invalid_eta(partner)

    pickup=now+leg1+workload
    return {'partner_id':partner.get('partner_id'),'pickup_minutes':pickup,'eta_minutes':pickup+prep+leg2,'eligible':True}



def assign_order(order, partners, travel, now=0):
    options = []

    for partner in partners:
        if partner.get('active') is not True:
            continue

        capacity = partner.get('capacity')
        active_orders = partner.get('active_order_ids', [])

        if (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1 or not isinstance(active_orders, list) or len(active_orders) >= capacity):
            continue

        estimate = estimate_eta(order, partner, travel, now)

        if estimate['eligible']:
            options.append(estimate)

    if not options:
        return {
            'order_id': order.get('order_id'),
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing time data'
        }

    chosen = min(options, key=lambda x: (x['eta_minutes'], str(x['partner_id']))
    )

    return {
        'order_id': order.get('order_id'),
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner, order_id, cancellation_id):

    # Copy data to avoid modifying the original dictionary
    partner = partner.copy()

    processed = partner.get('processed_cancellation_ids', [])

    if cancellation_id in processed:
        return partner

    active_orders = partner.get('active_order_ids', []).copy()
    minutes_by_order = partner.get('minutes_by_order', {}).copy()

    if order_id in active_orders:

        active_orders.remove(order_id)

        workload = minutes_by_order.pop(order_id, 0)

        partner['workload_minutes'] = max(
            0,
            partner.get('workload_minutes', 0) - workload
        )

    processed = processed.copy()
    processed.append(cancellation_id)

    partner['active_order_ids'] = active_orders
    partner['minutes_by_order'] = minutes_by_order
    partner['processed_cancellation_ids'] = processed

    return partner
