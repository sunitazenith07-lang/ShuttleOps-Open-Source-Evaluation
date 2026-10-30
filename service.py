from collections.abc import Mapping
from copy import deepcopy
from math import isfinite


def _is_nonnegative_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value >= 0 and (isinstance(value, int) or isfinite(value))


def _is_valid_identifier(value):
    return isinstance(value, str) and bool(value.strip())


def _is_valid_order(order):
    return (
        isinstance(order, Mapping)
        and _is_valid_identifier(order.get("order_id"))
        and _is_valid_identifier(order.get("restaurant_id"))
        and _is_valid_identifier(order.get("destination_zone"))
        and _is_nonnegative_number(order.get("prep_minutes"))
    )


def _unavailable_estimate(partner):
    partner_id = partner.get("partner_id") if isinstance(partner, Mapping) else None
    return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}


def estimate_eta(order, partner, travel, now=0):
    if (
        not _is_valid_order(order)
        or not isinstance(partner, Mapping)
        or not _is_valid_identifier(partner.get("zone"))
        or not _is_nonnegative_number(partner.get("workload_minutes", 0))
        or not _is_nonnegative_number(now)
        or not isinstance(travel, Mapping)
    ):
        return _unavailable_estimate(partner)

    leg1 = travel.get((partner.get("zone"), order.get("restaurant_id")))
    leg2 = travel.get((order.get("restaurant_id"), order.get("destination_zone")))
    if not _is_nonnegative_number(leg1) or not _is_nonnegative_number(leg2):
        return _unavailable_estimate(partner)

    pickup = now + leg1 + partner.get("workload_minutes", 0)
    eta = pickup + order.get("prep_minutes") + leg2
    if not _is_nonnegative_number(pickup) or not _is_nonnegative_number(eta):
        return _unavailable_estimate(partner)

    return {
        "partner_id": partner.get("partner_id"),
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def assign_order(order, partners, travel, now=0):
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    if not _is_valid_order(order):
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": "invalid order data",
        }

    options = []
    if not isinstance(partners, (list, tuple)):
        partners = []

    for partner in partners:
        if not isinstance(partner, Mapping):
            continue
        capacity = partner.get("capacity")
        active_order_ids = partner.get("active_order_ids")
        if (
            partner.get("active") is not True
            or not _is_valid_identifier(partner.get("partner_id"))
            or not _is_valid_identifier(partner.get("zone"))
            or isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
            or not isinstance(active_order_ids, (list, tuple))
            or len(active_order_ids) >= capacity
        ):
            continue

        estimate = estimate_eta(order, partner, travel, now)
        if estimate["eligible"]:
            options.append(estimate)

    if not options:
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": "no eligible partner or missing time data",
        }

    chosen = min(options, key=lambda item: (item["eta_minutes"], item["partner_id"]))
    return {
        "order_id": order_id,
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    if isinstance(partner, Mapping):
        out = deepcopy(dict(partner))
    else:
        return deepcopy(partner)

    if not isinstance(out.get("active_order_ids"), list):
        out["active_order_ids"] = []
    if not isinstance(out.get("processed_cancellation_ids"), list):
        out["processed_cancellation_ids"] = []

    if not _is_valid_identifier(event_id):
        return out
    if event_id in out["processed_cancellation_ids"]:
        return out

    if _is_valid_identifier(order_id) and order_id in out["active_order_ids"]:
        out["active_order_ids"] = [
            active_id for active_id in out["active_order_ids"] if active_id != order_id
        ]
        minutes_by_order = out.get("minutes_by_order")
        minutes = (
            minutes_by_order.get(order_id)
            if isinstance(minutes_by_order, Mapping)
            else None
        )
        workload = out.get("workload_minutes", 0)
        if _is_nonnegative_number(workload) and _is_nonnegative_number(minutes):
            out["workload_minutes"] = max(0, workload - minutes)

    out["processed_cancellation_ids"].append(event_id)
    return out
