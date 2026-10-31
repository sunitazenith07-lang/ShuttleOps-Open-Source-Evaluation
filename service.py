"""Deterministic delivery-partner selection and cancellation handling."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
from typing import Any


def _is_time(value: Any) -> bool:
    """Return whether *value* is a finite, non-negative numeric duration."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value >= 0
    )


def _is_identifier(value: Any) -> bool:
    """Identifiers are non-empty strings so routing keys remain unambiguous."""
    return isinstance(value, str) and bool(value.strip())


def _is_valid_order(order: Any) -> bool:
    return isinstance(order, Mapping) and (
        _is_identifier(order.get("order_id"))
        and _is_identifier(order.get("restaurant_id"))
        and _is_identifier(order.get("destination_zone"))
        and _is_time(order.get("prep_minutes"))
    )


def _ineligible(partner: Any) -> dict[str, Any]:
    partner_id = partner.get("partner_id") if isinstance(partner, Mapping) else None
    return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}


def estimate_eta(order: Any, partner: Any, travel: Any, now: Any = 0) -> dict[str, Any]:
    """Calculate a candidate ETA without treating missing or invalid data as zero."""
    if not (
        _is_valid_order(order)
        and isinstance(partner, Mapping)
        and isinstance(travel, Mapping)
        and _is_identifier(partner.get("partner_id"))
        and _is_identifier(partner.get("zone"))
        and _is_time(partner.get("workload_minutes", 0))
        and _is_time(now)
    ):
        return _ineligible(partner)

    leg_to_restaurant = travel.get((partner["zone"], order["restaurant_id"]))
    leg_to_customer = travel.get((order["restaurant_id"], order["destination_zone"]))
    if not _is_time(leg_to_restaurant) or not _is_time(leg_to_customer):
        return _ineligible(partner)

    pickup = now + leg_to_restaurant + partner.get("workload_minutes", 0)
    return {
        "partner_id": partner["partner_id"],
        "pickup_minutes": pickup,
        "eta_minutes": pickup + order["prep_minutes"] + leg_to_customer,
        "eligible": True,
    }


def _is_available(partner: Any) -> bool:
    """Check state that is specific to assignment rather than ETA calculation."""
    if not isinstance(partner, Mapping) or partner.get("active") is not True:
        return False

    capacity = partner.get("capacity")
    active_orders = partner.get("active_order_ids")
    return (
        isinstance(capacity, int)
        and not isinstance(capacity, bool)
        and capacity >= 1
        and isinstance(active_orders, list)
        and len(active_orders) < capacity
    )


def _unassigned(order: Any, reason: str) -> dict[str, Any]:
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    return {
        "order_id": order_id,
        "partner_id": None,
        "eta_minutes": None,
        "reason": reason,
    }


def assign_order(order: Any, partners: Any, travel: Any, now: Any = 0) -> dict[str, Any]:
    """Select the available candidate with the lowest ETA and stable ID tie-break."""
    if not _is_valid_order(order) or not _is_time(now):
        return _unassigned(order, "invalid order or current time")
    if not isinstance(partners, list):
        return _unassigned(order, "no eligible partner or missing time data")

    options = [
        estimate
        for partner in partners
        if _is_available(partner)
        for estimate in [estimate_eta(order, partner, travel, now)]
        if estimate["eligible"]
    ]
    if not options:
        return _unassigned(order, "no eligible partner or missing time data")

    chosen = min(options, key=lambda item: (item["eta_minutes"], item["partner_id"]))
    return {
        "order_id": order["order_id"],
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner: Any, order_id: Any, event_id: Any) -> dict[str, Any]:
    """Apply one cancellation event once, without mutating the input record."""
    out = deepcopy(partner) if isinstance(partner, Mapping) else {}
    active_orders = out.get("active_order_ids")
    processed_events = out.get("processed_cancellation_ids")
    out["active_order_ids"] = active_orders if isinstance(active_orders, list) else []
    out["processed_cancellation_ids"] = (
        processed_events if isinstance(processed_events, list) else []
    )

    if event_id in out["processed_cancellation_ids"]:
        return out

    out["processed_cancellation_ids"].append(event_id)
    if order_id not in out["active_order_ids"]:
        return out

    out["active_order_ids"].remove(order_id)
    minutes_by_order = out.get("minutes_by_order")
    released_minutes = (
        minutes_by_order.get(order_id, 0)
        if isinstance(minutes_by_order, Mapping)
        else 0
    )
    workload = out.get("workload_minutes", 0)
    out["workload_minutes"] = max(
        0,
        (workload if _is_time(workload) else 0)
        - (released_minutes if _is_time(released_minutes) else 0),
    )
    return out
