# TESTING.md — Verification and Test Evidence

This document records the actual test environment, execution commands, historical test progression, and verified edge cases for the SmartDispatch delivery partner assignment engine.

---

## Test Command and Environment

- **Python version:** Python 3.15.1 (also verified with standard Python 3.10+)
- **Test Framework:** pytest 9.2.0, pluggy 1.7.0
- **Platform:** Windows (win32)
- **Commands run:**
  ```bash
  # Run baseline/quick suite
  python -m pytest -q

  # Run full suite with detailed verbose output
  python -m pytest -v

  # Run offline demo
  python -m main
  ```
- **Actual Final Test Summary:**
  ```text
  ============================= 229 passed in 0.35s =============================
  Total test cases: 229
  Passed: 229
  Failed: 0
  Errors: 0
  Skipped: 0
  ```

---

## Historical Progression of Test Results

To maintain complete transparency, the table below documents the test progression across all development phases:

| Phase / Milestone | Tests Passed | Tests Failed | Key Changes / Fixes |
| :--- | :---: | :---: | :--- |
| **Untouched Starter Baseline** | 164 | 65 | Unmodified starter code with intentional defects. |
| **After Bug 1 Fix** (ETA & input validation) | 195 | 34 | Added `_is_valid_non_negative_number` and `_is_valid_non_empty_str`; validated `now`, `prep`, travel legs, IDs. (28 failures resolved). |
| **After Bug 2 Fix** (Partner eligibility & capacity) | 213 | 16 | Added `_is_valid_capacity`, strict `active is True` check, and `len(active_orders) < capacity` enforcement. (18 failures resolved). |
| **After Bug 3 Fix** (Cancellation idempotency) | **229** | **0** | Added deduplication check `event_id in processed_cancellation_ids` and non-negative workload clamping. (16 failures resolved). |

---

## Edge-Case Evidence

The table below documents verified edge cases tested against the implementation:

| # | Case / Input | Expected Behaviour | Actual Result | Test Name or Evidence |
|---|---|---|---|---|
| 1 | Negative travel time (`leg1 = -1, leg2 = 1`) | Candidate marked ineligible; ETA is `None` | `{'eligible': False, 'eta_minutes': None}` | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[-1-1]` |
| 2 | Boolean travel time (`leg1 = True, leg2 = 1`) | Boolean rejected explicitly (not treated as 1); marked ineligible | `{'eligible': False, 'eta_minutes': None}` | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]` |
| 3 | Floating-point `NaN` travel time (`leg1 = NaN, leg2 = 1`) | Rejected as non-finite; marked ineligible | `{'eligible': False, 'eta_minutes': None}` | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[nan-1]` |
| 4 | Missing travel route (`travel = {}`) | Never treated as zero; marked ineligible | `{'eligible': False, 'eta_minutes': None}` | `tests/test_contract.py::test_missing_travel_is_not_zero` |
| 5 | Negative prep time (`prep_minutes = -5`) | Order rejected; no partner assigned | `{'partner_id': None, 'reason': 'no eligible partner...'}` | `tests/test_contract.py::test_negative_prep_time_is_rejected` |
| 6 | Inactive partner (`active = False`) | Inactive partner excluded from dispatch | `{'partner_id': None, 'reason': 'no eligible partner...'}` | `tests/test_contract.py::test_inactive_partner_not_assigned` |
| 7 | Full capacity partner (`capacity = 2, active_orders = 2`) | Excluded from dispatch when active orders equal capacity | `{'partner_id': None, 'reason': 'no eligible partner...'}` | `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[2-2]` |
| 8 | Duplicate cancellation event (`event_id = 'C1'` called twice) | Second call is a no-op; event recorded once; workload not double deducted | `workload_minutes = 0`, `processed_cancellation_ids = ['C1']` | `tests/test_contract.py::test_duplicate_cancellation_is_idempotent` |
| 9 | Lexicographic tie-break (`ETA = 7` for partner 'A' and 'Z') | Partner with smaller alphabetical ID ('A') is chosen | `result['partner_id'] == 'A'` | `tests/test_contract.py::test_tie_break_by_partner_id` |

---

## Regression Tests and Defect Verification

All 229 pre-existing tests in the repository act as regression tests:
- **`tests/test_contract.py` (9 tests):** Validates the high-level business contract: formula calculation, missing travel safety, inactive partners, full capacity exclusion, lowest ETA selection, tie-breaking, negative prep rejection, and cancellation idempotency.
- **`tests/test_acceptance_matrix.py` (189 tests):** Validates parameterized boundary combinations of travel times, workloads, prep times, capacities, active flags, order IDs, and cancellation workloads (0 to 999 minutes).
- **`tests/test_edge_cases.py` (31 tests):** Validates deterministic ETA calculations across extreme workload boundaries (up to 10,000 minutes) and missing route combinations.

---

## Remaining Failures or Limitations

- **Failing Tests:** Zero. All 229 automated unit and acceptance tests pass.
- **Known Limitations:**
  - In-memory data store: Partner and order state reside in memory. Persistence to an external database is outside the synthetic challenge scope.
  - Linear search for cancellations: `processed_cancellation_ids` uses a Python list. While optimal for synthetic workloads, a hash set would be preferred for high-volume cancellation histories.
