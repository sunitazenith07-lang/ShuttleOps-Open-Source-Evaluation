from models import new_order, new_partner


def sample_inputs():
    """Offline demo ke liye chhota, synthetic dispatch scenario."""
    order = new_order("O-7", "R-2", "Z-9", 10)

    # P-2 ka ek purana order hai; abhi 5 minute ka workload bacha hai.
    p1 = new_partner("P-2", "Z-1")
    p1.update(workload_minutes=5, active_order_ids=["OLD-1"])

    # P-1 par 2 minute ka workload hai; dono partners compare honge.
    p2 = new_partner("P-1", "Z-3")
    p2.update(workload_minutes=2)

    # Har key (start zone, end zone) hai; values travel time minutes mein hain.
    travel = {
        ("Z-1", "R-2"): 8,
        ("R-2", "Z-9"): 12,
        ("Z-3", "R-2"): 12,
    }
    return order, [p1, p2], travel
