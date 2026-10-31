"""Assignment and ETA logic for the offline SmartDispatch exercise."""

from collections.abc import Mapping
from copy import deepcopy
import math


def _valid_id(value):
    """Return whether value is a non-empty string identifier."""
    return isinstance(value, str) and bool(value.strip())


def _valid_minutes(value):
    """Accept finite, non-negative integer or float minute values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if value < 0:
        return False
    return not isinstance(value, float) or math.isfinite(value)


def _valid_order(order):
    return (
        isinstance(order, Mapping)
        and _valid_id(order.get("order_id"))
        and _valid_id(order.get("restaurant_id"))
        and _valid_id(order.get("destination_zone"))
        and _valid_minutes(order.get("prep_minutes"))
    )


def _partner_problem(partner):
    """Return a short reason a partner cannot be considered, or None."""
    if not isinstance(partner, Mapping):
        return "malformed partner record"
    if not _valid_id(partner.get("partner_id")) or not _valid_id(
        partner.get("zone")
    ):
        return "malformed partner record"
    if partner.get("active") is not True:
        return "inactive partner"

    capacity = partner.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        return "invalid capacity"

    active_order_ids = partner.get("active_order_ids")
    if not isinstance(active_order_ids, (list, tuple)):
        return "invalid active order list"
    if any(not _valid_id(order_id) for order_id in active_order_ids):
        return "invalid active order list"
    if len(active_order_ids) >= capacity:
        return "capacity reached"

    if not _valid_minutes(partner.get("workload_minutes", 0)):
        return "invalid workload"
    return None


def _ineligible_eta(partner_id=None):
    return {
        "partner_id": partner_id,
        "pickup_minutes": None,
        "eta_minutes": None,
        "eligible": False,
    }


def estimate_eta(order, partner, travel, now=0):
    """Estimate pickup and delivery times when all required data is valid.

    The result is ineligible when identifiers, partner availability, time
    values, or either required travel leg is invalid or missing.
    """
    partner_id = partner.get("partner_id") if isinstance(partner, Mapping) else None
    if not _valid_order(order) or _partner_problem(partner) is not None:
        return _ineligible_eta(partner_id)
    if not _valid_minutes(now) or not isinstance(travel, Mapping):
        return _ineligible_eta(partner_id)

    restaurant_id = order["restaurant_id"]
    first_leg = travel.get((partner["zone"], restaurant_id))
    second_leg = travel.get((restaurant_id, order["destination_zone"]))
    if not _valid_minutes(first_leg) or not _valid_minutes(second_leg):
        return _ineligible_eta(partner_id)

    try:
        pickup = now + first_leg + partner.get("workload_minutes", 0)
        eta = pickup + order["prep_minutes"] + second_leg
    except OverflowError:
        return _ineligible_eta(partner_id)
    # Finite inputs can still overflow when added as floats.
    if not _valid_minutes(pickup) or not _valid_minutes(eta):
        return _ineligible_eta(partner_id)

    return {
        "partner_id": partner_id,
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def _unassigned(order_id, reason):
    return {
        "order_id": order_id,
        "partner_id": None,
        "eta_minutes": None,
        "reason": reason,
    }


def assign_order(order, partners, travel, now=0):
    """Assign an order to the eligible partner with the lowest ETA."""
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    if not _valid_order(order):
        return _unassigned(order_id, "invalid order identifiers or preparation time")
    if not isinstance(partners, (list, tuple)):
        return _unassigned(order_id, "partner records must be provided as a list or tuple")
    if not partners:
        return _unassigned(order_id, "no partner records supplied")

    options = []
    rejection_counts = {}
    for partner in partners:
        problem = _partner_problem(partner)
        if problem is not None:
            rejection_counts[problem] = rejection_counts.get(problem, 0) + 1
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate["eligible"]:
            options.append((estimate, partner["zone"]))
        else:
            rejection_counts["missing or invalid ETA data"] = (
                rejection_counts.get("missing or invalid ETA data", 0) + 1
            )

    if not options:
        details = "; ".join(
            f"{reason}: {count}"
            for reason, count in sorted(rejection_counts.items())
        )
        return _unassigned(order_id, f"no eligible partner ({details})")

    chosen = min(
        options,
        key=lambda option: (
            option[0]["eta_minutes"],
            option[0]["partner_id"],
            option[0]["pickup_minutes"],
            option[1],
        ),
    )
    estimate = chosen[0]
    return {
        "order_id": order_id,
        "partner_id": estimate["partner_id"],
        "pickup_minutes": estimate["pickup_minutes"],
        "eta_minutes": estimate["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    """Apply a cancellation once and return an updated partner copy.

    Invalid event identifiers are ignored. Unknown orders are recorded as
    processed events but do not change workload or capacity.
    """
    if isinstance(partner, Mapping):
        out = deepcopy(dict(partner))
    else:
        out = {}

    active_order_ids = out.get("active_order_ids")
    if not isinstance(active_order_ids, list):
        active_order_ids = []
    processed_ids = out.get("processed_cancellation_ids")
    if not isinstance(processed_ids, list):
        processed_ids = []

    # Normalize prior event IDs while preserving their order, so malformed
    # legacy duplicates cannot make the result non-idempotent.
    unique_processed_ids = []
    for processed_id in processed_ids:
        if _valid_id(processed_id) and processed_id not in unique_processed_ids:
            unique_processed_ids.append(processed_id)
    out["active_order_ids"] = active_order_ids
    out["processed_cancellation_ids"] = unique_processed_ids

    if not _valid_id(event_id) or event_id in unique_processed_ids:
        return out

    out["processed_cancellation_ids"].append(event_id)
    if not _valid_id(order_id) or order_id not in active_order_ids:
        return out

    out["active_order_ids"] = [
        active_id for active_id in active_order_ids if active_id != order_id
    ]
    workload = out.get("workload_minutes", 0)
    if not _valid_minutes(workload):
        workload = 0
    minutes_by_order = out.get("minutes_by_order")
    if not isinstance(minutes_by_order, Mapping):
        minutes_by_order = {}
    cancelled_minutes = minutes_by_order.get(order_id, 0)
    if not _valid_minutes(cancelled_minutes):
        cancelled_minutes = 0
    try:
        out["workload_minutes"] = max(0, workload - cancelled_minutes)
    except OverflowError:
        # Keep the known workload rather than releasing an amount we cannot
        # represent safely with the supplied mixed numeric values.
        out["workload_minutes"] = workload
    return out
