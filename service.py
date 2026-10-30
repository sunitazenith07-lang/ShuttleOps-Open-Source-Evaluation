from collections.abc import Mapping
from copy import deepcopy
import math
from numbers import Real


def _is_non_negative_number(value):
    """Batata hai ki value finite, non-negative number hai aur bool nahi."""
    # bool Python mein int ka subtype hai, isliye True ko 1 minute na maan lein.
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        # NaN, infinity aur negative durations ko ETA mein use nahi karna.
        return math.isfinite(value) and value >= 0
    except (OverflowError, TypeError):
        # Bahut bade ya unsupported numeric input par crash karne ke bajay reject.
        return False


def _is_identifier(value):
    """ID/zone non-empty string hai ya nahi, yeh check karta hai."""
    return isinstance(value, str) and bool(value.strip())


def _invalid_estimate(partner_id=None):
    """Invalid candidate ka ek consistent result format deta hai."""
    return {'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}


def estimate_eta(order, partner, travel, now=0):
    """Ek partner ke liye pickup aur delivery ETA calculate karta hai."""
    # Pehle check karo ki order aur partner record hain; tabhi unse values lena safe hai.
    if not isinstance(order, Mapping) or not isinstance(partner, Mapping):
        return _invalid_estimate()

    partner_id = partner.get('partner_id')
    # IDs aur zones valid strings hone chahiye; ye travel lookup keys bhi bante hain.
    if not all(
        _is_identifier(value)
        for value in (
            order.get('order_id'),
            order.get('restaurant_id'),
            order.get('destination_zone'),
            partner_id,
            partner.get('zone'),
        )
    ):
        return _invalid_estimate(partner_id)

    prep_minutes = order.get('prep_minutes')
    workload_minutes = partner.get('workload_minutes', 0)
    # ETA arithmetic se pehle har time value validate kar lo.
    if not all(
        _is_non_negative_number(value)
        for value in (now, prep_minutes, workload_minutes)
    ):
        return _invalid_estimate(partner_id)

    if not isinstance(travel, Mapping):
        return _invalid_estimate(partner_id)

    # Travel map mein route ko (shuru, end) zone pair se dhoondhte hain.
    leg1 = travel.get((partner.get('zone'), order.get('restaurant_id')))
    leg2 = travel.get((order.get('restaurant_id'), order.get('destination_zone')))
    # Route missing ho to zero maan kar guess nahi karte; candidate ko reject karte hain.
    if not all(_is_non_negative_number(value) for value in (leg1, leg2)):
        return _invalid_estimate(partner_id)

    # Pickup: abhi ka time + restaurant tak travel + partner ka remaining workload.
    pickup = now + leg1 + workload_minutes
    # ETA: pickup ke baad restaurant preparation aur customer tak travel.
    eta = pickup + prep_minutes + leg2
    if not _is_non_negative_number(pickup) or not _is_non_negative_number(eta):
        return _invalid_estimate(partner_id)

    return {
        'partner_id': partner_id,
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
    }


def _valid_partner_capacity(partner):
    """Partner active hai aur uske paas order capacity bachi hai ya nahi."""
    if not isinstance(partner, Mapping) or partner.get('active') is not True:
        return False

    capacity = partner.get('capacity')
    active_order_ids = partner.get('active_order_ids')
    return (
        isinstance(capacity, int)
        and not isinstance(capacity, bool)
        and capacity > 0
        and isinstance(active_order_ids, list)
        and len(active_order_ids) < capacity
    )


def assign_order(order, partners, travel, now=0):
    """Eligible partners mein se sabse kam ETA wala partner assign karta hai."""
    order_id = order.get('order_id') if isinstance(order, Mapping) else None
    # Partners ki list na mile to safely maan lo ki assign karne ke liye koi nahi.
    if not isinstance(partners, (list, tuple)):
        partners = ()

    options = []
    for partner in partners:
        # Inactive ya full partner ko pehle chhod do; uska ETA nikalne ka fayda nahi.
        if not _valid_partner_capacity(partner):
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate['eligible']:
            options.append(estimate)

    # Koi candidate eligible na ho ya required data na mile to unassigned result.
    if not options:
        return {
            'order_id': order_id,
            'partner_id': None,
            'eta_minutes': None,
            'reason': 'no eligible partner or missing/invalid time data',
        }

    # Sabse chhoti ETA chuno; barabar ho to chhota partner ID winner hai.
    chosen = min(options, key=lambda item: (item['eta_minutes'], item['partner_id']))
    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned',
    }


def process_cancellation(partner, order_id, event_id):
    """Cancellation ko ek baar apply karke updated partner ki copy return karta hai."""
    # Original partner ko jaisa hai waisa chhod kar uski copy update karo.
    out = deepcopy(partner)
    if not isinstance(out, dict):
        return out

    active_order_ids = out.get('active_order_ids')
    if not isinstance(active_order_ids, list):
        active_order_ids = []
        out['active_order_ids'] = active_order_ids

    processed_ids = out.get('processed_cancellation_ids')
    if not isinstance(processed_ids, list):
        processed_ids = []
        out['processed_cancellation_ids'] = processed_ids

    # Duplicate event pehle aa chuka hai: workload dobara release na karo.
    if event_id in processed_ids:
        return out

    if order_id in active_order_ids:
        active_order_ids.remove(order_id)
        workload = out.get('workload_minutes', 0)
        minutes_by_order = out.get('minutes_by_order', {})
        order_minutes = (
            minutes_by_order.get(order_id, 0)
            if isinstance(minutes_by_order, Mapping)
            else 0
        )
        # Valid numbers hon tabhi workload ghatao, aur use zero se neeche mat jaane do.
        if _is_non_negative_number(workload) and _is_non_negative_number(order_minutes):
            out['workload_minutes'] = max(0, workload - order_minutes)

    # Event ko record karo taaki wahi cancellation agali baar duplicate maana jaaye.
    processed_ids.append(event_id)
    return out
