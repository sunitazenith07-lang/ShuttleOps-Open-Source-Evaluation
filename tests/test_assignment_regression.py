"""Regression tests for Phase 3: Assignment Logic Implementation."""
import pytest
from models import new_order, new_partner
from service import assign_order


# --- Task A: Active Partner Eligibility ---

def test_active_partner_assigned():
    """Active partner should be eligible for assignment."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    partner = new_partner("P-ACTIVE", "ZONE-A")
    partner["active"] = True
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] == "P-ACTIVE"
    assert result["reason"] == "assigned"


def test_inactive_partner_boolean_false_rejected():
    """Partner with active=False must not be assigned."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    partner = new_partner("P-INACTIVE", "ZONE-A")
    partner["active"] = False
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None
    assert result["reason"] == "no eligible partner or missing time data"


def test_inactive_partner_non_boolean_truthy_rejected():
    """Partner with non-boolean active values (e.g., 'yes', 1) must not be treated as active."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    for falsy_or_non_bool in [0, 1, None, "yes", "no", [], {}]:
        partner = new_partner("P-NONBOOL", "ZONE-A")
        partner["active"] = falsy_or_non_bool
        result = assign_order(order, [partner], travel)
        assert result["partner_id"] is None, f"Failed for active={falsy_or_non_bool!r}"


# --- Task B: Capacity Enforcement ---

def test_partner_at_capacity_rejected():
    """Partner with active_order_ids matching capacity must not be assigned."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    partner = new_partner("P-FULL", "ZONE-A", capacity=2)
    partner["active_order_ids"] = ["ORD-EXISTING-1", "ORD-EXISTING-2"]
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None
    assert result["reason"] == "no eligible partner or missing time data"


def test_partner_exceeding_capacity_rejected():
    """Partner with active_order_ids exceeding capacity must not be assigned."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    partner = new_partner("P-OVER", "ZONE-A", capacity=1)
    partner["active_order_ids"] = ["ORD-EXISTING-1", "ORD-EXISTING-2"]
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None


def test_partner_below_capacity_accepted():
    """Partner with active_order_ids fewer than capacity should be assigned."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    partner = new_partner("P-PARTIAL", "ZONE-A", capacity=3)
    partner["active_order_ids"] = ["ORD-EXISTING-1", "ORD-EXISTING-2"]
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] == "P-PARTIAL"


# --- Task C: Capacity Value Validation ---

def test_invalid_capacity_types_rejected():
    """Invalid capacity values (0, negative, bool, float, None, str) must be rejected."""
    order = new_order("ORD-1", "REST-1", "DEST-1")
    travel = {("ZONE-A", "REST-1"): 5, ("REST-1", "DEST-1"): 10}
    for invalid_cap in [0, -1, -5, True, False, 1.5, None, "2", "", []]:
        partner = new_partner("P-CAP", "ZONE-A", capacity=2)
        partner["capacity"] = invalid_cap
        partner["active_order_ids"] = []
        result = assign_order(order, [partner], travel)
        assert result["partner_id"] is None, f"Failed for invalid capacity={invalid_cap!r}"


# --- Task D: Order Field Validation ---

@pytest.mark.parametrize("field,invalid_val", [
    ("order_id", ""),
    ("order_id", "   "),
    ("order_id", None),
    ("order_id", 0),
    ("order_id", 123),
    ("restaurant_id", ""),
    ("restaurant_id", "   "),
    ("restaurant_id", None),
    ("restaurant_id", 0),
    ("destination_zone", ""),
    ("destination_zone", "   "),
    ("destination_zone", None),
    ("destination_zone", 0),
    ("prep_minutes", -1),
    ("prep_minutes", -0.1),
    ("prep_minutes", None),
    ("prep_minutes", "10"),
    ("prep_minutes", True),
    ("prep_minutes", False),
    ("prep_minutes", float("nan")),
    ("prep_minutes", float("inf")),
])
def test_order_field_validation_rejects_invalid_values(field, invalid_val):
    """assign_order must reject orders with invalid IDs or prep_minutes."""
    order = new_order("O-VALID", "R-VALID", "D-VALID", 10)
    order[field] = invalid_val
    partner = new_partner("P-1", "Z-1")
    travel = {("Z-1", "R-VALID"): 5, ("R-VALID", "D-VALID"): 10}
    result = assign_order(order, [partner], travel)
    assert result["partner_id"] is None
    assert result["eta_minutes"] is None


def test_order_non_dict_rejected():
    """Non-dict order object must return an unassigned result safely."""
    partner = new_partner("P-1", "Z-1")
    travel = {("Z-1", "R"): 5, ("R", "D"): 10}
    for invalid_order in [None, "order_string", 123, [], ()]:
        result = assign_order(invalid_order, [partner], travel)
        assert result["partner_id"] is None
