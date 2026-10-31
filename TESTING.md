# TESTING.md — Test Execution and Verification Report

**Project:** SmartDispatch — Delivery Partner Assignment and ETA Engine  
**Author:** Candidate Submission  
**Repository:** `SmartDispatch-Open-Source-Evaluation`  

---

## 1. Test Command and Environment

### Environment Details
- **Operating System:** macOS (Darwin arm64)
- **Local Python Interpreter:** `Python 3.9.6` (Apple CommandLineTools)
- **Test Framework:** `pytest 8.4.2`
- **Virtual Environment:** Isolated local virtual environment at `.venv/`
- **Target / CI Environment:** Python 3.11 (via GitHub Actions `.github/workflows/tests.yml`)

### Setup and Dependency Installation
To prepare the environment from the repository root:
```bash
# 1. Create a local virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install development and testing dependencies
pip install -r requirements-dev.txt
```

### Verification Commands Run
```bash
# Execute the complete automated test suite
.venv/bin/python -m pytest -q

# Execute the offline demo script
.venv/bin/python -m main
```

### Actual Test Suite Summary Output
```
........................................................................ [ 20%]
........................................................................ [ 41%]
........................................................................ [ 62%]
........................................................................ [ 82%]
...........................................................              [100%]
347 passed in 0.10s
```
- **Total Tests Collected:** 347
- **Passed:** 347 (100%)
- **Failed:** 0
- **Errors:** 0
- **Skipped:** 0
- **Exit Code:** `0`

### Actual Demo Execution Output
```bash
$ .venv/bin/python -m main
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```
- **Exit Code:** `0`

---

## 2. Edge-Case Evidence

The following table documents eight key edge cases tested across the engine, showing the exact input setup, expected behavior, actual observed result, and corresponding test evidence:

| # | Case / Input Setup | Expected Behaviour | Actual Result | Test Name & Evidence |
|---|---|---|---|---|
| **1** | **String or Boolean Travel Time:**  <br>`leg1="2"` or `leg1=True` passed to `estimate_eta` | Mark candidate ineligible (`eligible=False`, `eta_minutes=None`) without raising `TypeError`. | `eligible: False`, `eta_minutes: None` returned safely. | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[2-1]`, `[True-1]` |
| **2** | **Negative or NaN Prep Time:**  <br>`prep_minutes=-5` or `float('nan')` in order | Reject order immediately or mark candidate ineligible; no negative or NaN ETA generated. | Order rejected with `partner_id: None`, `eta_minutes: None`. | `tests/test_contract.py::test_negative_prep_time_is_rejected`, `tests/test_acceptance_matrix.py::test_preparation_time_validation[nan]` |
| **3** | **Partner at Full Capacity:**  <br>`capacity=2`, `active_order_ids=['A', 'B']` | Candidate partner is filtered out; cannot receive an order assignment. | Partner skipped; fallback response returned if no other partner eligible. | `tests/test_contract.py::test_full_partner_not_assigned`, `tests/test_assignment_regression.py::test_partner_at_capacity_rejected` |
| **4** | **Duplicate Cancellation Event ID:**  <br>`process_cancellation` called twice with identical `event_id="C1"` | First call removes order and deducts workload; second call is a no-op (idempotent, workload not deducted twice, event ID not duplicated). | `workload_minutes=0`, `processed_cancellation_ids=['C1']`. | `tests/test_contract.py::test_duplicate_cancellation_is_idempotent`, `tests/test_phase4_regression.py::test_duplicate_cancellation_same_event_id_is_idempotent` |
| **5** | **Huge Integer Finiteness ($10^{400}$):**  <br>Travel time or prep time $> 10^{308}$ passed to `estimate_eta` | Accepted as valid finite integer without throwing `OverflowError: int too large to convert to float`. | `eligible: True`, pickup and ETA computed accurately without error. | `tests/test_phase4_regression.py::test_large_integer_does_not_raise_overflow_error` |
| **6** | **Mixed Int/Float Overflow:**  <br>`now = 10**400` with float `leg1 = 1.5` passed to `estimate_eta` | Safe calculation without unhandled `OverflowError`; result validated as non-finite and marked ineligible. | `eligible: False`, `eta_minutes: None`. | `tests/test_phase4_regression.py::test_estimate_eta_large_int_plus_float_no_overflow_error` |
| **7** | **Deterministic Lexicographical Tie-Breaking:**  <br>Two partners (`P-1`, `P-2`) both yield identical ETA | Break tie deterministically by alphabetical order of `str(partner_id)` (`P-1` wins over `P-2`). | `P-1` selected regardless of input list ordering. | `tests/test_contract.py::test_tie_break_by_partner_id`, `tests/test_acceptance_matrix.py::test_ties_break_by_partner_id_independent_of_input_order` |
| **8** | **Malformed Partner Fields:**  <br>`active_order_ids=None`, `workload_minutes=None`, or `partner_id=None` | Do not treat malformed collections as 0 orders; do not crash on cancellation; do not assign order to `partner_id=None`. | Malformed partners skipped safely without unhandled exceptions. | `tests/test_phase4_regression.py::test_assign_order_active_order_ids_none_skips_partner`, `test_process_cancellation_workload_none_no_type_error` |

---

## 3. Regression Tests Added

To guarantee that fixed defects cannot return, two dedicated regression test files were authored. No original starter tests were modified or weakened:

### 1. `tests/test_assignment_regression.py` (29 Tests)
- **Active Status Verification:** Tests boolean `True` versus `False`, `None`, `0`, `1`, `"yes"`, `"no"`, and non-boolean truthy values.
- **Capacity Boundaries:** Tests partner assignment when below capacity, at capacity, and exceeding capacity.
- **Capacity Value Types:** Tests rejection of invalid capacity values: `0`, `-1`, `-5`, `True`, `False`, `1.5`, `None`, `"2"`, `""`, `[]`.
- **Order Field Robustness:** Exhaustive parameter matrix testing missing, empty, whitespace-only, and non-string values for `order_id`, `restaurant_id`, and `destination_zone`.

### 2. `tests/test_phase4_regression.py` (89 Tests)
- **Travel Leg Validation (13 cases):** Validates rejection of `None`, negative numbers, strings, booleans, NaN, $+\infty$, and $-\infty$.
- **Preparation Time in `estimate_eta` (17 cases):** Validates standalone rejection of invalid prep times and acceptance of valid float/int values.
- **Current Time `now` Validation (20 cases):** Validates rejection of negative numbers, strings, booleans, `None`, NaN, and Infinities.
- **Cancellation Idempotency (3 tests):** Validates repeated application of identical event ID, distinct event independence, and workload floor stability.
- **Large Integer Overflow Protection (1 test):** Validates $10^{400}$ without `OverflowError`.
- **Partner Workload Validation (11 tests):** Rejects `None`, negative numbers, booleans, strings, NaN, and Infinities; verifies missing workload key defaults to 0; verifies valid integer and float arithmetic.
- **Malformed State & Robustness Fixes (24 tests):**
  - *Malformed `active_order_ids` (6 tests):* `None`, string, empty list, at capacity, below capacity, and list with mixed-type elements.
  - *Malformed Cancellation Fields (4 tests):* `workload_minutes=None`, `active_order_ids=None`, `minutes_by_order=None`, and valid record correctness.
  - *Invalid Partner IDs (4 tests):* `partner_id=None`, empty string, whitespace-only string, and valid assignment.
  - *Arithmetic Overflow (5 tests):* Large int + float overflow, huge float overflow, normal int arithmetic, normal float arithmetic, and pure large integer arithmetic.
  - *Invalid Event IDs (5 tests):* `event_id=None`, empty string, whitespace string, duplicate valid ID, and two distinct valid IDs.

---

## 4. Test Suite Progression Summary

The table below clearly tracks the historical test suite growth across development phases, leading to the final verified test count:

| Development Phase | Test Files Involved | Total Tests | Passed | Failed | Key Milestones & Notes |
|---|---|---|---|---|---|
| **Phase 2 Baseline** | `test_contract.py`, `test_acceptance_matrix.py`, `test_edge_cases.py` | 229 | 164 | 65 | Documented initial 65 failing tests on untouched starter codebase. |
| **Phase 3 Assignment** | Above + `test_assignment_regression.py` | 258 | 220 | 38 | Added 29 assignment tests; resolved active status, capacity, and order string checks. |
| **Phase 4 Verification** | Above + `test_phase4_regression.py` | 312 | 312 | 0 | Added 54 ETA & cancellation tests; resolved travel time validation, float finiteness, and cancellation idempotency. |
| **Workload Defense Step** | `test_phase4_regression.py` (extended) | 323 | 323 | 0 | Added 11 workload validation tests; guarded `estimate_eta()` against `workload_minutes=None`. |
| **Final Hardening Phase** | Complete test suite | **347** | **347** | **0** | Added 24 robustness tests for malformed collections, arithmetic overflow, invalid partner IDs, and invalid event IDs. |

### Test Count Breakdown by File
- `tests/test_contract.py`: 9 passed
- `tests/test_acceptance_matrix.py`: 189 passed
- `tests/test_edge_cases.py`: 31 passed
- `tests/test_assignment_regression.py`: 29 passed
- `tests/test_phase4_regression.py`: 89 passed
- **Total across all files:** **347 passed** (0 failed, 0 errors, 0 skipped)

---

## 5. Remaining Failures or Limitations

- **Failing Tests:** **0** (All 347 tests passing cleanly).
- **Environment Context:** Local development was conducted using Python 3.9.6, while the problem statement recommends Python 3.10+ and CI runs on Python 3.11. All code strictly uses backward- and forward-compatible Python constructs supported from 3.9 through 3.12+.
- **External Dependencies:** Only standard library modules (`copy`, `math`) and the `pytest` test framework are used. No unexpected third-party dependencies are introduced.

---
*End of TESTING.md*
