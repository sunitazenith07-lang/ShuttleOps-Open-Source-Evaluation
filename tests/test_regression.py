"""Regression tests for SmartDispatch service.

These tests protect specific behaviour gaps identified during code review.
They cover scenarios not included in the existing acceptance matrix,
contract tests, or edge-case suite.

Each test is named to describe exactly what regression it prevents.
None of the existing test files are modified by adding these tests here.
"""
from models import new_order, new_partner
from service import assign_order, estimate_eta, process_cancellation


# ---------------------------------------------------------------------------
# Test 1: Sequential cancellations of two different orders on one partner
# ---------------------------------------------------------------------------

def test_sequential_cancellations_of_different_orders():
    """Cancel two orders one after another and verify state is correct at each step.

    Scenario:
      - Partner starts with two active orders: O1 (10 min) and O2 (15 min).
      - Total workload = 25 min.
      - After cancelling O1 (event C1): workload drops to 15; O2 still present.
      - After cancelling O2 (event C2): workload drops to 0; both orders gone.

    This protects against a bug where cancelling one order corrupts the
    workload or accidentally removes the wrong order from the active list.
    """
    partner = new_partner('P', 'Z')
    partner.update(
        active_order_ids=['O1', 'O2'],
        workload_minutes=25,
        minutes_by_order={'O1': 10, 'O2': 15}
    )

    # --- First cancellation: remove O1 ---
    after_first = process_cancellation(partner, 'O1', 'C1')

    # O2 must still be present; O1 must be gone
    assert after_first['active_order_ids'] == ['O2']
    # Workload reduced by O1's contribution only (25 - 10 = 15)
    assert after_first['workload_minutes'] == 15
    # C1 is recorded exactly once
    assert after_first['processed_cancellation_ids'] == ['C1']

    # --- Second cancellation: remove O2 using the result of the first ---
    after_second = process_cancellation(after_first, 'O2', 'C2')

    # Both orders are now gone
    assert after_second['active_order_ids'] == []
    # Workload is now zero (15 - 15 = 0)
    assert after_second['workload_minutes'] == 0
    # Both event IDs recorded
    assert 'C1' in after_second['processed_cancellation_ids']
    assert 'C2' in after_second['processed_cancellation_ids']
    # Each recorded exactly once
    assert after_second['processed_cancellation_ids'].count('C1') == 1
    assert after_second['processed_cancellation_ids'].count('C2') == 1


# ---------------------------------------------------------------------------
# Test 2: assign_order correctly uses a non-zero 'now' value
# ---------------------------------------------------------------------------

def test_assign_order_uses_nonzero_now_correctly():
    """Verify that a non-zero 'now' is factored into the ETA returned by assign_order.

    The formula is:
        pickup = now + leg1 + workload
        ETA    = pickup + prep + leg2

    All existing assign_order tests use now=0 (the default). This test
    uses now=10 to confirm the parameter genuinely flows through the
    entire call chain and appears correctly in the result.

    Scenario:
        now=10, leg1=3, workload=0, prep=5, leg2=4
        Expected pickup = 10 + 3 + 0 = 13
        Expected ETA   = 13 + 5 + 4  = 22
    """
    order = new_order('O', 'R', 'D', prep_minutes=5)
    partner = new_partner('P', 'Z')   # workload=0 by default

    travel = {('Z', 'R'): 3, ('R', 'D'): 4}

    result = assign_order(order, [partner], travel, now=10)

    assert result['partner_id'] == 'P'
    assert result['pickup_minutes'] == 13   # 10 + 3 + 0
    assert result['eta_minutes'] == 22      # 13 + 5 + 4
    assert result['reason'] == 'assigned'


# ---------------------------------------------------------------------------
# Test 3: Correct partner selected from a mixed pool of eligible/ineligible
# ---------------------------------------------------------------------------

def test_correct_partner_selected_from_mixed_pool():
    """Only the fully eligible partner is selected when the pool contains
    inactive, full-capacity, and missing-route partners alongside them.

    Pool:
        P-INACTIVE : active=False, valid routes     -> must be skipped (inactive)
        P-FULL     : active=True, capacity=1, full  -> must be skipped (at capacity)
        P-NOROUTE  : active=True, capacity=2, zone has no travel entry -> skipped
        P-GOOD     : active=True, capacity=2, valid routes             -> SELECTED

    This test protects against bugs where any one disqualification rule
    fails silently and allows the wrong partner to be selected, or where
    the only eligible partner is accidentally excluded.
    """
    order = new_order('O', 'R', 'D', prep_minutes=5)

    # Inactive partner — has valid routes but is not working
    p_inactive = new_partner('P-INACTIVE', 'ZI')
    p_inactive['active'] = False

    # Full partner — active but already carrying maximum load (capacity=1, 1 order)
    p_full = new_partner('P-FULL', 'ZF', capacity=1)
    p_full['active_order_ids'] = ['EXISTING']

    # No-route partner — active and under capacity but travel route is missing
    p_noroute = new_partner('P-NOROUTE', 'ZX')   # zone ZX has no entry in travel

    # Good partner — active, under capacity, valid routes
    p_good = new_partner('P-GOOD', 'ZG')

    travel = {
        ('ZI', 'R'): 5,   # inactive partner's route exists but partner is skipped
        ('ZF', 'R'): 5,   # full partner's route exists but partner is skipped
        # ('ZX', 'R') intentionally absent — P-NOROUTE cannot be assigned
        ('ZG', 'R'): 5,   # good partner's leg 1
        ('R', 'D'): 10,   # shared restaurant-to-customer route
    }

    result = assign_order(order, [p_inactive, p_full, p_noroute, p_good], travel)

    # Only P-GOOD is eligible — it must win
    assert result['partner_id'] == 'P-GOOD'
    assert result['eta_minutes'] is not None


# ---------------------------------------------------------------------------
# Test 4: Already-processed event_id blocks a different order from being cancelled
# ---------------------------------------------------------------------------

def test_already_processed_event_blocks_different_order():
    """The idempotency guard fires on event_id, not on order_id.

    Scenario:
        - Partner has two active orders: O1 and O2, each worth 10 min.
        - First call:  cancel O1 with event 'EVT-1' → works correctly.
        - Second call: attempt to cancel O2 also with event 'EVT-1' (same event ID).
        - Because 'EVT-1' is already in processed_cancellation_ids, the second
          call must be a complete no-op — O2 must remain in active_order_ids.

    This protects against a misimplementation where the guard checks
    order_id instead of event_id. If order_id were the guard, the second
    call would incorrectly cancel O2 because O2 is a different order.
    """
    partner = new_partner('P', 'Z')
    partner.update(
        active_order_ids=['O1', 'O2'],
        workload_minutes=20,
        minutes_by_order={'O1': 10, 'O2': 10}
    )

    # --- First cancellation: O1 with EVT-1 ---
    after_first = process_cancellation(partner, 'O1', 'EVT-1')

    assert 'O1' not in after_first['active_order_ids']   # O1 removed
    assert 'O2' in after_first['active_order_ids']        # O2 still present
    assert after_first['workload_minutes'] == 10          # only O1's share removed

    # --- Second call: try to cancel O2 but reuse event 'EVT-1' ---
    # EVT-1 is already processed → must be a complete no-op
    after_second = process_cancellation(after_first, 'O2', 'EVT-1')

    # O2 must still be in the active list (not cancelled)
    assert 'O2' in after_second['active_order_ids']
    # Workload must be unchanged (O2 not removed)
    assert after_second['workload_minutes'] == 10
    # EVT-1 must appear exactly once — not appended again
    assert after_second['processed_cancellation_ids'].count('EVT-1') == 1


# ---------------------------------------------------------------------------
# Test 5: Partner with missing 'active' key is not assigned
# ---------------------------------------------------------------------------

def test_partner_missing_active_key_is_not_assigned():
    """A partner dict with no 'active' key is treated as inactive.

    assign_order uses: partner.get('active')
    When the key is absent, .get() returns None.
    None is falsy, so 'not None' is True, and the partner is skipped.

    This ensures the code handles incomplete partner records safely,
    for example when loading data from records.json where a field
    might be missing entirely rather than set to False.
    """
    order = new_order('O', 'R', 'D')
    partner = new_partner('P', 'Z')

    # Completely remove the 'active' key — simulates a missing field in data
    del partner['active']

    result = assign_order(order, [partner], {('Z', 'R'): 1, ('R', 'D'): 1})

    # A partner with no 'active' key must not be assigned
    assert result['partner_id'] is None
    assert result['eta_minutes'] is None


# ---------------------------------------------------------------------------
# Test 6: Missing 'workload_minutes' key defaults to zero workload
# ---------------------------------------------------------------------------

def test_missing_workload_minutes_key_defaults_to_zero():
    """When a partner dict is missing 'workload_minutes', the ETA uses 0.

    estimate_eta uses: partner.get('workload_minutes', 0)
    When the key is absent, the default of 0 is used silently.
    The partner remains fully eligible and receives a correct ETA.

    This tests the robustness of the .get() default for incomplete records
    that might arrive from external data sources.

    Scenario (now=0, leg1=5, workload=0(default), prep=10, leg2=7):
        Expected pickup = 0 + 5 + 0 = 5
        Expected ETA   = 5 + 10 + 7  = 22
    """
    order = new_order('O', 'R', 'D', prep_minutes=10)
    partner = new_partner('P', 'Z')

    # Remove the workload_minutes key entirely — simulates a missing field
    del partner['workload_minutes']

    travel = {('Z', 'R'): 5, ('R', 'D'): 7}

    result = estimate_eta(order, partner, travel, now=0)

    # Partner must still be eligible
    assert result['eligible'] is True
    # Pickup = 0 + 5 + 0 (workload defaults to 0)
    assert result['pickup_minutes'] == 5
    # ETA = 5 + 10 + 7
    assert result['eta_minutes'] == 22
