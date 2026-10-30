from collections.abc import Iterable, Mapping
from copy import deepcopy
from math import isfinite


def _is_valid_identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _is_valid_minutes(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
        and (isinstance(value, int) or isfinite(value))
    )


def _valid_order(order):
    return (
        isinstance(order, Mapping)
        and _is_valid_identifier(order.get("order_id"))
        and _is_valid_identifier(order.get("restaurant_id"))
        and _is_valid_identifier(order.get("destination_zone"))
        and _is_valid_minutes(order.get("prep_minutes"))
    )


def _ineligible_eta(partner_id):
    return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}


def estimate_eta(order, partner, travel, now=0):
    partner_id = partner.get("partner_id") if isinstance(partner, Mapping) else None
    if (
        not _valid_order(order)
        or not isinstance(partner, Mapping)
        or not _is_valid_identifier(partner_id)
        or not _is_valid_identifier(partner.get("zone"))
        or not _is_valid_minutes(now)
        or not _is_valid_minutes(partner.get("workload_minutes"))
        or not isinstance(travel, Mapping)
    ):
        return _ineligible_eta(partner_id)

    leg1 = travel.get((partner["zone"], order["restaurant_id"]))
    leg2 = travel.get((order["restaurant_id"], order["destination_zone"]))
    if not _is_valid_minutes(leg1) or not _is_valid_minutes(leg2):
        return _ineligible_eta(partner_id)

    try:
        pickup = now + leg1 + partner["workload_minutes"]
        eta = pickup + order["prep_minutes"] + leg2
    except OverflowError:
        return _ineligible_eta(partner_id)

    if not _is_valid_minutes(pickup) or not _is_valid_minutes(eta):
        return _ineligible_eta(partner_id)

    return {
        "partner_id": partner_id,
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def _unassigned_result(order, reason):
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    return {
        "order_id": order_id,
        "partner_id": None,
        "eta_minutes": None,
        "reason": reason,
    }


def assign_order(order, partners, travel, now=0):
    if not _valid_order(order):
        return _unassigned_result(order, "invalid order data")
    if (
        not isinstance(partners, Iterable)
        or isinstance(partners, (str, bytes, Mapping))
    ):
        return _unassigned_result(order, "invalid partner collection")

    options = []
    exclusion_reasons = set()
    partner_count = 0

    for partner in partners:
        partner_count += 1
        if not isinstance(partner, Mapping):
            exclusion_reasons.add("invalid partner data")
            continue
        if partner.get("active") is not True:
            exclusion_reasons.add("inactive partner")
            continue

        capacity = partner.get("capacity")
        active_order_ids = partner.get("active_order_ids")
        partner_id = partner.get("partner_id")
        if (
            not _is_valid_identifier(partner_id)
            or not _is_valid_identifier(partner.get("zone"))
            or not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity < 1
            or not isinstance(active_order_ids, list)
            or any(not _is_valid_identifier(order_id) for order_id in active_order_ids)
            or not _is_valid_minutes(partner.get("workload_minutes"))
        ):
            exclusion_reasons.add("invalid partner data")
            continue
        if len(active_order_ids) >= capacity:
            exclusion_reasons.add("partner at capacity")
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate["eligible"]:
            options.append(estimate)
        else:
            exclusion_reasons.add("missing or invalid travel-time data")

    if not options:
        if partner_count == 0:
            exclusion_reasons.add("no partner records provided")
        reason = "no eligible partner: " + "; ".join(sorted(exclusion_reasons))
        return _unassigned_result(order, reason)

    chosen = min(
        options,
        key=lambda item: (
            item["eta_minutes"],
            item["partner_id"],
            item["pickup_minutes"],
        ),
    )
    return {
        "order_id": order["order_id"],
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, Mapping):
        raise TypeError("partner must be a mapping")
    if not _is_valid_identifier(event_id):
        raise ValueError("event_id must be a non-empty string")

    out = deepcopy(dict(partner))
    active_order_ids = out.setdefault("active_order_ids", [])
    processed_event_ids = out.setdefault("processed_cancellation_ids", [])
    if not isinstance(active_order_ids, list):
        raise ValueError("partner active_order_ids must be a list")
    if not isinstance(processed_event_ids, list):
        raise ValueError("partner processed_cancellation_ids must be a list")
    if event_id in processed_event_ids:
        return out

    if order_id in active_order_ids:
        minutes_by_order = out.get("minutes_by_order", {})
        if not isinstance(minutes_by_order, Mapping):
            raise ValueError("partner minutes_by_order must be a mapping")
        workload = out.get("workload_minutes", 0)
        cancelled_minutes = minutes_by_order.get(order_id, 0)
        if not _is_valid_minutes(workload) or not _is_valid_minutes(cancelled_minutes):
            raise ValueError("partner workload values must be non-negative numbers")

        out["active_order_ids"] = [
            active_id for active_id in active_order_ids if active_id != order_id
        ]
        out["workload_minutes"] = max(0, workload - cancelled_minutes)

    processed_event_ids.append(event_id)
    return out
