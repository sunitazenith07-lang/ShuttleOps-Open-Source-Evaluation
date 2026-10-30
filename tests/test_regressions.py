"""Regression tests for all fixes applied to service.py.

Each test targets a specific defect that was found and fixed, ensuring
the bug cannot silently return.
"""
import math
import pytest
from models import new_order, new_partner
from service import estimate_eta, assign_order, process_cancellation


# ---------------------------------------------------------------------------
# 1. Travel-time validation regressions
# ---------------------------------------------------------------------------

class TestTravelTimeValidation:
    """Ensure non-numeric, negative, NaN, inf, bool, and string travel times
    are rejected — they must never be treated as zero or silently computed."""

    @pytest.mark.parametrize("bad_leg1,leg2", [
        (-5, 3), ("10", 3), (True, 3), (False, 3),
        (float("nan"), 3), (float("inf"), 3), (1.0, 3),
    ])
    def test_bad_leg1_rejected(self, bad_leg1, leg2):
        order = new_order("O-REG", "R-1", "D-1", 5)
        partner = new_partner("P-1", "Z-1")
        travel = {("Z-1", "R-1"): bad_leg1, ("R-1", "D-1"): leg2}
        result = estimate_eta(order, partner, travel)
        # 1.0 is a valid float, so only truly bad values should be ineligible
        if isinstance(bad_leg1, float) and bad_leg1 == 1.0:
            assert result["eligible"] is True
        else:
            assert result["eligible"] is False
            assert result["eta_minutes"] is None

    @pytest.mark.parametrize("leg1,bad_leg2", [
        (3, -5), (3, "10"), (3, True), (3, False),
        (3, float("nan")), (3, float("inf")),
    ])
    def test_bad_leg2_rejected(self, leg1, bad_leg2):
        order = new_order("O-REG", "R-1", "D-1", 5)
        partner = new_partner("P-1", "Z-1")
        travel = {("Z-1", "R-1"): leg1, ("R-1", "D-1"): bad_leg2}
        result = estimate_eta(order, partner, travel)
        assert result["eligible"] is False
        assert result["eta_minutes"] is None


# ---------------------------------------------------------------------------
# 2. Prep-time validation regressions
# ---------------------------------------------------------------------------

class TestPrepTimeValidation:
    """Ensure invalid prep_minutes values cause ineligibility."""

    @pytest.mark.parametrize("bad_prep", [-1, -100, None, "10", True, float("nan"), float("inf")])
    def test_invalid_prep_rejected_in_estimate(self, bad_prep):
        order = new_order("O-REG", "R-1", "D-1", bad_prep)
        partner = new_partner("P-1", "Z-1")
        result = estimate_eta(order, partner, {("Z-1", "R-1"): 2, ("R-1", "D-1"): 3})
        assert result["eligible"] is False

    def test_zero_prep_is_valid(self):
        order = new_order("O-REG", "R-1", "D-1", 0)
        partner = new_partner("P-1", "Z-1")
        result = estimate_eta(order, partner, {("Z-1", "R-1"): 2, ("R-1", "D-1"): 3})
        assert result["eligible"] is True
        assert result["eta_minutes"] == 0 + 2 + 0 + 0 + 3  # now + leg1 + workload + prep + leg2


# ---------------------------------------------------------------------------
# 3. now-parameter validation regressions
# ---------------------------------------------------------------------------

class TestNowValidation:
    """Negative, string, bool, or None `now` must make the estimate ineligible."""

    @pytest.mark.parametrize("bad_now", [-1, -100, "5", True, False, None])
    def test_invalid_now_rejected(self, bad_now):
        order = new_order("O-REG", "R-1", "D-1", 5)
        partner = new_partner("P-1", "Z-1")
        result = estimate_eta(order, partner, {("Z-1", "R-1"): 1, ("R-1", "D-1"): 1}, bad_now)
        assert result["eligible"] is False

    def test_zero_now_is_valid(self):
        result = estimate_eta(
            new_order("O", "R", "D", 5),
            new_partner("P", "Z"),
            {("Z", "R"): 1, ("R", "D"): 1},
            0,
        )
        assert result["eligible"] is True


# ---------------------------------------------------------------------------
# 4. Order-field validation regressions
# ---------------------------------------------------------------------------

class TestOrderFieldValidation:
    """Orders with empty, None, or non-string IDs, and invalid prep, must not
    be assigned to any partner."""

    @pytest.mark.parametrize("field,value", [
        ("order_id", ""), ("order_id", None), ("order_id", 0),
        ("restaurant_id", ""), ("restaurant_id", None), ("restaurant_id", 0),
        ("destination_zone", ""), ("destination_zone", None), ("destination_zone", 0),
        ("prep_minutes", -1), ("prep_minutes", None), ("prep_minutes", "2"),
        ("prep_minutes", True), ("prep_minutes", float("nan")),
    ])
    def test_invalid_field_rejects_assignment(self, field, value):
        order = new_order("O", "R", "D")
        order[field] = value
        result = assign_order(order, [new_partner("P", "Z")], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None


# ---------------------------------------------------------------------------
# 5. Active-partner filtering regressions
# ---------------------------------------------------------------------------

class TestActivePartnerFiltering:
    """Inactive partners (active is False, 0, None, or non-True) must never
    be selected."""

    @pytest.mark.parametrize("active_val", [False, 0, None, "yes", "no", 1])
    def test_non_true_active_not_assigned(self, active_val):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z")
        partner["active"] = active_val
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None

    def test_active_true_is_assigned(self):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z")
        partner["active"] = True
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] == "P"


# ---------------------------------------------------------------------------
# 6. Capacity-check regressions
# ---------------------------------------------------------------------------

class TestCapacityCheck:
    """Partners at or over their order capacity must be rejected."""

    def test_at_capacity_rejected(self):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z", 1)
        partner["active_order_ids"] = ["EXISTING"]
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None

    def test_over_capacity_rejected(self):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z", 1)
        partner["active_order_ids"] = ["A", "B"]
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None

    def test_below_capacity_accepted(self):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z", 2)
        partner["active_order_ids"] = ["A"]
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] == "P"

    @pytest.mark.parametrize("bad_capacity", [0, -1, True, False, None, 1.5, "3"])
    def test_invalid_capacity_rejected(self, bad_capacity):
        order = new_order("O", "R", "D")
        partner = new_partner("P", "Z")
        partner["capacity"] = bad_capacity
        result = assign_order(order, [partner], {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None


# ---------------------------------------------------------------------------
# 7. Cancellation idempotency regressions
# ---------------------------------------------------------------------------

class TestCancellationIdempotency:
    """Duplicate cancellation events must not reduce workload or capacity a
    second time."""

    def test_duplicate_event_id_no_double_release(self):
        partner = new_partner("P", "Z")
        partner.update(
            active_order_ids=["O1"],
            workload_minutes=15,
            minutes_by_order={"O1": 15},
        )
        once = process_cancellation(partner, "O1", "C-DUP")
        assert once["workload_minutes"] == 0
        assert once["active_order_ids"] == []
        assert once["processed_cancellation_ids"] == ["C-DUP"]

        twice = process_cancellation(once, "O1", "C-DUP")
        # Second application must be a no-op
        assert twice["workload_minutes"] == 0
        assert twice["active_order_ids"] == []
        assert twice["processed_cancellation_ids"] == ["C-DUP"]

    def test_different_event_ids_both_recorded(self):
        partner = new_partner("P", "Z")
        partner.update(
            active_order_ids=["O1", "O2"],
            workload_minutes=20,
            minutes_by_order={"O1": 10, "O2": 10},
        )
        after1 = process_cancellation(partner, "O1", "C1")
        after2 = process_cancellation(after1, "O2", "C2")
        assert after2["active_order_ids"] == []
        assert after2["workload_minutes"] == 0
        assert after2["processed_cancellation_ids"] == ["C1", "C2"]

    def test_cancellation_of_unknown_order_records_event(self):
        partner = new_partner("P", "Z")
        partner.update(active_order_ids=["A"], workload_minutes=5, minutes_by_order={"A": 5})
        result = process_cancellation(partner, "UNKNOWN", "C-X")
        assert result["active_order_ids"] == ["A"]
        assert result["workload_minutes"] == 5
        assert result["processed_cancellation_ids"] == ["C-X"]


# ---------------------------------------------------------------------------
# 8. Tie-breaking regressions
# ---------------------------------------------------------------------------

class TestTieBreaking:
    """When two partners have the same ETA, the one with the lexicographically
    smaller partner_id must be selected."""

    def test_tie_selects_lower_id(self):
        order = new_order("O", "R", "D", 0)
        a = new_partner("Alpha", "Z")
        b = new_partner("Beta", "Z")
        result = assign_order(order, [b, a], {("Z", "R"): 5, ("R", "D"): 5})
        assert result["partner_id"] == "Alpha"

    def test_tie_independent_of_input_order(self):
        order = new_order("O", "R", "D", 0)
        partners = [new_partner(f"P-{i:03}", "Z") for i in range(10, 0, -1)]
        result = assign_order(order, partners, {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] == "P-001"


# ---------------------------------------------------------------------------
# 9. Empty / no-partner regressions
# ---------------------------------------------------------------------------

class TestNoPartners:
    """Empty partner lists, or all-ineligible partners, must return an
    unassigned result with a reason."""

    def test_empty_partner_list(self):
        result = assign_order(new_order("O", "R", "D"), [], {})
        assert result["partner_id"] is None
        assert result["reason"]

    def test_all_inactive(self):
        partners = [new_partner(f"P{i}", "Z") for i in range(3)]
        for p in partners:
            p["active"] = False
        result = assign_order(new_order("O", "R", "D"), partners, {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None

    def test_all_at_capacity(self):
        partners = [new_partner(f"P{i}", "Z", 1) for i in range(3)]
        for p in partners:
            p["active_order_ids"] = ["X"]
        result = assign_order(new_order("O", "R", "D"), partners, {("Z", "R"): 1, ("R", "D"): 1})
        assert result["partner_id"] is None

    def test_all_missing_routes(self):
        partners = [new_partner(f"P{i}", "Z") for i in range(3)]
        result = assign_order(new_order("O", "R", "D"), partners, {})
        assert result["partner_id"] is None
        assert result["eta_minutes"] is None


# ---------------------------------------------------------------------------
# 10. ETA formula sanity check (non-fixture-dependent)
# ---------------------------------------------------------------------------

class TestETAFormulaSanity:
    """Verify the formula: pickup = now + leg1 + workload;
    ETA = pickup + prep + leg2."""

    def test_formula_with_workload(self):
        order = new_order("O", "R", "D", 10)
        partner = new_partner("P", "Z")
        partner["workload_minutes"] = 5
        result = estimate_eta(order, partner, {("Z", "R"): 8, ("R", "D"): 12}, now=0)
        assert result["pickup_minutes"] == 0 + 8 + 5  # 13
        assert result["eta_minutes"] == 13 + 10 + 12  # 35

    def test_formula_with_now_offset(self):
        order = new_order("O", "R", "D", 3)
        partner = new_partner("P", "Z")
        partner["workload_minutes"] = 2
        result = estimate_eta(order, partner, {("Z", "R"): 4, ("R", "D"): 6}, now=10)
        assert result["pickup_minutes"] == 10 + 4 + 2  # 16
        assert result["eta_minutes"] == 16 + 3 + 6  # 25

    def test_formula_all_zeros(self):
        order = new_order("O", "R", "D", 0)
        partner = new_partner("P", "Z")
        result = estimate_eta(order, partner, {("Z", "R"): 0, ("R", "D"): 0}, now=0)
        assert result["pickup_minutes"] == 0
        assert result["eta_minutes"] == 0
        assert result["eligible"] is True
