"""Delivery-partner assignment, ETA calculation and cancellation handling.

The functions in this module are deliberately side-effect free: ``estimate_eta``
and ``assign_order`` only read their inputs, while ``process_cancellation``
returns a deep copy.  Missing or malformed data makes a candidate ineligible;
it is never silently treated as a zero-minute journey.
"""

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite


_UNASSIGNED_REASON = "no eligible partner or missing time data"


def _is_valid_id(value):
    """Return True for a non-empty identifier string."""
    return isinstance(value, str) and bool(value.strip())


def _is_non_negative_number(value):
    """Return True for a finite, non-negative number (booleans excluded)."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value >= 0
    if isinstance(value, float):
        return isfinite(value) and value >= 0
    return False


def _finite_result(value):
    """Guard against float overflow when adding otherwise valid numbers."""
    return not isinstance(value, float) or isfinite(value)


def _as_order_list(value):
    """Return a deterministic list for a well-formed sequence of order IDs.

    Lists and tuples keep their order.  Sets are sorted by their printable
    representation so that Python's hash randomisation cannot change the
    returned state.  Other malformed values become an empty list.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    return []


def _order_error(order):
    """Return a short validation error for an order, or None when valid."""
    if not isinstance(order, Mapping):
        return "order must be a mapping"
    if not _is_valid_id(order.get("order_id")):
        return "invalid order_id"
    if not _is_valid_id(order.get("restaurant_id")):
        return "invalid restaurant_id"
    if not _is_valid_id(order.get("destination_zone")):
        return "invalid destination_zone"
    if not _is_non_negative_number(order.get("prep_minutes")):
        return "invalid prep_minutes"
    return None


def _ineligible(partner_id):
    return {
        "partner_id": partner_id,
        "eta_minutes": None,
        "eligible": False,
    }


def estimate_eta(order, partner, travel, now=0):
    """Estimate a partner's ETA for one order.

    ``pickup = now + partner-to-restaurant travel + remaining workload``
    ``eta    = pickup + preparation time + restaurant-to-customer travel``

    Every input required by the formula is validated.  A missing, negative or
    non-numeric travel entry makes the result ineligible instead of defaulting
    to zero.
    """
    partner_id = partner.get("partner_id") if isinstance(partner, Mapping) else None

    if _order_error(order) is not None:
        return _ineligible(partner_id)
    if not _is_non_negative_number(now):
        return _ineligible(partner_id)
    if not isinstance(partner, Mapping):
        return _ineligible(partner_id)
    if not _is_valid_id(partner_id) or not _is_valid_id(partner.get("zone")):
        return _ineligible(partner_id)
    if not isinstance(travel, Mapping):
        return _ineligible(partner_id)

    workload = partner.get("workload_minutes", 0)
    if not _is_non_negative_number(workload):
        return _ineligible(partner_id)

    leg1 = travel.get((partner["zone"], order["restaurant_id"]))
    leg2 = travel.get((order["restaurant_id"], order["destination_zone"]))
    if not _is_non_negative_number(leg1) or not _is_non_negative_number(leg2):
        return _ineligible(partner_id)

    pickup = now + leg1 + workload
    eta = pickup + order["prep_minutes"] + leg2
    if not _finite_result(pickup) or not _finite_result(eta):
        return _ineligible(partner_id)

    return {
        "partner_id": partner_id,
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def _eligible_by_capacity(partner):
    """Return (is_eligible, reason) for active state and capacity checks."""
    if not isinstance(partner, Mapping):
        return False, "invalid_record"
    if partner.get("active") is not True:
        return False, "inactive"

    capacity = partner.get("capacity")
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
        return False, "invalid_capacity"

    active_orders = partner.get("active_order_ids", [])
    if active_orders is None:
        active_orders = []
    if isinstance(active_orders, (list, tuple, set, frozenset)):
        active_count = len(active_orders)
    else:
        return False, "invalid_active_orders"

    if active_count >= capacity:
        return False, "at_capacity"
    return True, None


def assign_order(order, partners, travel, now=0):
    """Assign an order to the eligible partner with the lowest ETA.

    Ties are broken by partner ID in ascending lexicographic order.  The
    returned ``reason`` explains an unassigned order deterministically.
    """
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    error = _order_error(order)
    if error is not None:
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": "invalid order: " + error,
        }

    if partners is None:
        partners = []

    reasons = {
        "invalid_record": 0,
        "inactive": 0,
        "invalid_capacity": 0,
        "invalid_active_orders": 0,
        "at_capacity": 0,
        "missing_or_invalid_time": 0,
    }
    options = []

    try:
        candidates = list(partners)
    except TypeError:
        candidates = []

    for partner in candidates:
        eligible, reason = _eligible_by_capacity(partner)
        if not eligible:
            reasons[reason] += 1
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate["eligible"]:
            options.append(estimate)
        else:
            reasons["missing_or_invalid_time"] += 1

    if not options:
        details = ", ".join(
            f"{name}={count}" for name, count in reasons.items() if count
        )
        reason = _UNASSIGNED_REASON
        if details:
            reason += f" ({details})"
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": reason,
        }

    chosen = min(
        options,
        key=lambda item: (item["eta_minutes"], item["partner_id"]),
    )
    return {
        "order_id": order_id,
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    """Apply one cancellation event to a partner, at most once.

    A repeated ``event_id`` is ignored, so workload and capacity are not
    released twice.  The input partner is never mutated.
    """
    if not isinstance(partner, Mapping):
        return deepcopy(partner)

    out = deepcopy(dict(partner))
    processed = out.setdefault("processed_cancellation_ids", [])
    if not isinstance(processed, list):
        processed = _as_order_list(processed)
        out["processed_cancellation_ids"] = processed

    if event_id in processed:
        return out

    active_orders = out.setdefault("active_order_ids", [])
    if not isinstance(active_orders, list):
        active_orders = _as_order_list(active_orders)
        out["active_order_ids"] = active_orders

    if order_id in active_orders:
        active_orders.remove(order_id)

        minutes_by_order = out.get("minutes_by_order", {})
        minutes = 0
        if isinstance(minutes_by_order, Mapping):
            minutes = minutes_by_order.get(order_id, 0)
        if not _is_non_negative_number(minutes):
            minutes = 0

        workload = out.get("workload_minutes", 0)
        if not _is_non_negative_number(workload):
            workload = 0
        out["workload_minutes"] = max(0, workload - minutes)

    processed.append(event_id)
    return out
