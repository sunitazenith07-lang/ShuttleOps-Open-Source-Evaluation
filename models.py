"""Synthetic order aur delivery-partner records ke helpers."""


def new_partner(partner_id, zone, capacity=2):
    # Naya partner active hota hai; shuru mein uske paas workload ya orders nahi.
    return {
        "partner_id": partner_id,
        "zone": zone,
        "active": True,
        "capacity": capacity,
        "active_order_ids": [],
        "workload_minutes": 0,
        "minutes_by_order": {},
        "processed_cancellation_ids": [],
    }


def new_order(order_id, restaurant_id, destination_zone, prep_minutes=10):
    # Order ke IDs, destination aur restaurant preparation time store karo.
    return {
        "order_id": order_id,
        "restaurant_id": restaurant_id,
        "destination_zone": destination_zone,
        "prep_minutes": prep_minutes,
    }
