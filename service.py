from copy import deepcopy
import math


def _is_valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == value
        and value != float("inf")
        and value != float("-inf")
        and math.isfinite(value)
    )


def _is_valid_time(value):
    return _is_valid_number(value) and value >= 0


def _valid_order(order):
    if not isinstance(order, dict):
        return False
    for key in ("order_id", "restaurant_id", "destination_zone"):
        value = order.get(key)
        if value is None or value is False or value == "" or value == 0:
            return False
        if isinstance(value, str) and not value.strip():
            return False
    prep = order.get("prep_minutes", None)
    if not _is_valid_time(prep):
        return False
    return True


def _valid_partner_for_assignment(partner):
    if not isinstance(partner, dict):
        return False
    if partner.get("active") is not True:
        return False
    capacity = partner.get("capacity", None)
    if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
        return False
    active_order_ids = partner.get("active_order_ids", [])
    if active_order_ids is None:
        active_order_ids = []
    if not isinstance(active_order_ids, list):
        return False
    return len(active_order_ids) < capacity


def estimate_eta(order, partner, travel, now=0):
    if not isinstance(order, dict) or not isinstance(partner, dict):
        return {"partner_id": None, "eta_minutes": None, "eligible": False, "pickup_minutes": None}
    if not _valid_order(order):
        return {"partner_id": partner.get("partner_id"), "eta_minutes": None, "eligible": False, "pickup_minutes": None}
    if not _is_valid_time(now):
        return {"partner_id": partner.get("partner_id"), "eta_minutes": None, "eligible": False, "pickup_minutes": None}

    zone = partner.get("zone")
    restaurant_id = order.get("restaurant_id")
    destination_zone = order.get("destination_zone")
    prep_minutes = order.get("prep_minutes")

    workload = partner.get("workload_minutes", 0)
    if not _is_valid_time(workload):
        return {"partner_id": partner.get("partner_id"), "eta_minutes": None, "eligible": False, "pickup_minutes": None}

    if not (hasattr(travel, "get") and callable(getattr(travel, "get"))):
        return {"partner_id": partner.get("partner_id"), "eta_minutes": None, "eligible": False, "pickup_minutes": None}

    leg1 = travel.get((zone, restaurant_id))
    leg2 = travel.get((restaurant_id, destination_zone))
    if not _is_valid_time(leg1) or not _is_valid_time(leg2):
        return {"partner_id": partner.get("partner_id"), "eta_minutes": None, "eligible": False, "pickup_minutes": None}

    pickup = now + leg1 + workload
    eta = pickup + prep_minutes + leg2
    return {
        "partner_id": partner.get("partner_id"),
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def assign_order(order, partners, travel, now=0):
    if not _valid_order(order):
        return {
            "order_id": order.get("order_id") if isinstance(order, dict) else None,
            "partner_id": None,
            "pickup_minutes": None,
            "eta_minutes": None,
            "reason": "invalid order",
        }

    if not isinstance(partners, (list, tuple)):
        partners = [] if partners is None else [partners]

    options = []
    for partner in partners:
        if not _valid_partner_for_assignment(partner):
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get("eligible"):
            options.append(estimate)

    if not options:
        return {
            "order_id": order.get("order_id"),
            "partner_id": None,
            "pickup_minutes": None,
            "eta_minutes": None,
            "reason": "no eligible partner or missing time data",
        }

    chosen = min(options, key=lambda item: (item["eta_minutes"], str(item["partner_id"])))
    return {
        "order_id": order.get("order_id"),
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return partner
    out = deepcopy(partner)
    out.setdefault("active_order_ids", [])
    out.setdefault("processed_cancellation_ids", [])
    out.setdefault("minutes_by_order", {})
    if not isinstance(out["active_order_ids"], list):
        out["active_order_ids"] = list(out["active_order_ids"]) if out["active_order_ids"] is not None else []
    if not isinstance(out["processed_cancellation_ids"], list):
        out["processed_cancellation_ids"] = list(out["processed_cancellation_ids"]) if out["processed_cancellation_ids"] is not None else []
    if not isinstance(out["minutes_by_order"], dict):
        out["minutes_by_order"] = {}

    processed = out["processed_cancellation_ids"]
    if event_id in processed:
        return out

    active_ids = out["active_order_ids"]
    minutes_by_order = out["minutes_by_order"]
    workload = out.get("workload_minutes", 0)
    if not _is_valid_time(workload):
        workload = 0

    if order_id in active_ids:
        out["active_order_ids"] = [oid for oid in active_ids if oid != order_id]
        minutes = minutes_by_order.get(order_id, 0)
        if not _is_valid_time(minutes):
            minutes = 0
        out["workload_minutes"] = max(0, workload - minutes)
        if order_id in minutes_by_order:
            del minutes_by_order[order_id]
        out["minutes_by_order"] = minutes_by_order

    processed.append(event_id)
    out["processed_cancellation_ids"] = processed
    return out
