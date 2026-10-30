from copy import deepcopy
from math import isfinite


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_time(value):
    return _is_number(value) and value >= 0 and value == value and value != float("inf") and isfinite(value)


def _valid_id(value):
    return isinstance(value, str) and value != ""


def _valid_order(order):
    if not isinstance(order, dict):
        return False
    if not _valid_id(order.get("order_id")):
        return False
    if not _valid_id(order.get("restaurant_id")):
        return False
    if not _valid_id(order.get("destination_zone")):
        return False
    if "prep_minutes" not in order:
        return False
    if not _valid_time(order.get("prep_minutes")):
        return False
    return True


def _partner_active_count(partner):
    ids = partner.get("active_order_ids", [])
    if not isinstance(ids, list):
        return 0
    return len(ids)


def estimate_eta(order, partner, travel, now=0):
    partner_id = None
    if isinstance(partner, dict):
        partner_id = partner.get("partner_id")

    if not isinstance(order, dict) or not isinstance(partner, dict):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    if not _valid_order(order):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    if not _valid_time(now):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    if partner.get("active") is not True:
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    capacity = partner.get("capacity", 0)
    if not (isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    if _partner_active_count(partner) >= capacity:
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    workload = partner.get("workload_minutes", 0)
    if workload is None:
        workload = 0
    if not _valid_time(workload):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    if not isinstance(travel, dict):
        travel = {}

    leg1 = travel.get((partner.get("zone"), order.get("restaurant_id")))
    leg2 = travel.get((order.get("restaurant_id"), order.get("destination_zone")))
    if not _valid_time(leg1) or not _valid_time(leg2):
        return {"partner_id": partner_id, "eta_minutes": None, "eligible": False}

    pickup = now + leg1 + workload
    eta = pickup + order.get("prep_minutes") + leg2
    return {
        "partner_id": partner_id,
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def assign_order(order, partners, travel, now=0):
    order_id = order.get("order_id") if isinstance(order, dict) else None

    if not _valid_order(order):
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": "invalid order",
        }

    if not isinstance(partners, (list, tuple)):
        partners = []

    if not isinstance(travel, dict):
        travel = {}

    options = []
    for partner in partners:
        if not isinstance(partner, dict):
            continue
        estimate = estimate_eta(order, partner, travel, now)
        if estimate.get("eligible"):
            options.append(estimate)

    if not options:
        return {
            "order_id": order.get("order_id") if isinstance(order, dict) else order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": "no eligible partner or missing time data",
        }

    chosen = min(options, key=lambda item: (item["eta_minutes"], str(item["partner_id"])))
    return {
        "order_id": order.get("order_id") if isinstance(order, dict) else order_id,
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

    if event_id in out["processed_cancellation_ids"]:
        return out

    if order_id in out["active_order_ids"]:
        try:
            out["active_order_ids"].remove(order_id)
        except ValueError:
            pass
        minutes = 0
        try:
            minutes = out["minutes_by_order"].get(order_id, 0)
        except Exception:
            minutes = 0
        if not _valid_time(minutes):
            try:
                minutes = float(minutes)
            except (TypeError, ValueError):
                minutes = 0
            if not _is_number(minutes) or minutes < 0:
                minutes = 0
        current = out.get("workload_minutes", 0)
        if not _is_number(current) or current is None:
            current = 0
        out["workload_minutes"] = max(0, current - minutes)

    out["processed_cancellation_ids"].append(event_id)
    return out
