
from copy import deepcopy
import math


def _valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def estimate_eta(order, partner, travel, now=0):
    invalid = {
        "partner_id": partner.get("partner_id") if isinstance(partner, dict) else None,
        "pickup_minutes": None,
        "eta_minutes": None,
        "eligible": False,
    }

    if not all(isinstance(x, dict) for x in (order, partner, travel)):
        return invalid

    if not _valid_number(now):
        return invalid

    required_order_fields = ("order_id", "restaurant_id", "destination_zone")
    if any(not isinstance(order.get(k), str) or not order[k].strip()
           for k in required_order_fields):
        return invalid

    if not isinstance(partner.get("zone"), str) or not partner["zone"].strip():
        return invalid

    prep = order.get("prep_minutes")
    workload = partner.get("workload_minutes", 0)

    if not _valid_number(prep) or not _valid_number(workload):
        return invalid

    leg1 = travel.get((partner["zone"], order["restaurant_id"]))
    leg2 = travel.get((order["restaurant_id"], order["destination_zone"]))

    if not _valid_number(leg1) or not _valid_number(leg2):
        return invalid

    pickup = now + leg1 + workload
    eta = pickup + prep + leg2

    return {
        "partner_id": partner.get("partner_id"),
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
    }


def assign_order(order, partners, travel, now=0):
    order_id = order.get("order_id") if isinstance(order, dict) else None

    def unassigned(reason):
        return {
            "order_id": order_id,
            "partner_id": None,
            "eta_minutes": None,
            "reason": reason,
        }

    if not isinstance(order, dict):
        return unassigned("invalid order")

    if not isinstance(partners, (list, tuple)) or not isinstance(travel, dict):
        return unassigned("invalid partner or travel data")

    if not _valid_number(now):
        return unassigned("invalid current time")

    candidates = []

    for partner in partners:
        if not isinstance(partner, dict):
            continue

        if partner.get("active") is not True:
            continue

        capacity = partner.get("capacity")
        active_orders = partner.get("active_order_ids")

        if (
            not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity < 1
            or not isinstance(active_orders, list)
            or len(active_orders) >= capacity
        ):
            continue

        estimate = estimate_eta(order, partner, travel, now)

        if estimate["eligible"]:
            candidates.append(estimate)

    if not candidates:
        return unassigned("no eligible partner or missing/invalid time data")

    chosen = min(
        candidates,
        key=lambda item: (
            item["eta_minutes"],
            str(item["partner_id"]),
        ),
    )

    return {
        "order_id": order_id,
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }



def process_cancellation(partner, order_id, event_id):
    if not isinstance(partner, dict):
        return partner

    out = deepcopy(partner)

    if not isinstance(out.get("active_order_ids"), list):
        out["active_order_ids"] = []

    if not isinstance(out.get("processed_cancellation_ids"), list):
        out["processed_cancellation_ids"] = []

    if not isinstance(out.get("minutes_by_order"), dict):
        out["minutes_by_order"] = {}



    if event_id is not None and event_id in out["processed_cancellation_ids"]:
        return out

    if order_id in out["active_order_ids"]:
        out["active_order_ids"].remove(order_id)

        minutes = out["minutes_by_order"].get(order_id, 0)
        workload = out.get("workload_minutes", 0)

        if _valid_number(minutes) and _valid_number(workload):
            out["workload_minutes"] = max(0, workload - minutes)

        out["minutes_by_order"].pop(order_id, None)

    if event_id is not None:
      out["processed_cancellation_ids"].append(event_id)

    return out
