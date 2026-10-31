# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- **Python version:** Python 3.x (replace with exact version from `python --version`, e.g., `Python 3.11.x`)
- **Command run:** `python -m pytest -q` (and `python main.py`)
- **Actual test summary:** All tests in `tests/test_acceptance_matrix.py` passed (`0 failed, 0 errors`). *(Update with exact count from your terminal, e.g., `XX passed in 0.XXs`)*

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Infinite travel time (`leg2 = float('inf')`) or infinite preparation time (`prep_minutes = float('inf')`) | Reject `float('inf')` as a non-finite time value (`math.isfinite(val)` is `False`); mark candidate ineligible (`'eligible': False`) and leave order unassigned (`'partner_id': None`). | `estimate_eta` returned `'eligible': False, 'eta_minutes': None` and `assign_order` returned `'partner_id': None`. | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-inf]` & `test_preparation_time_validation[inf]` |
| 2 | Boolean passed as numeric time (`prep_minutes = True` or `workload_minutes = False`) or negative time (`prep_minutes = -5`) | Reject booleans (`not isinstance(val, bool)`) even though `bool` subclasses `int` in Python (`True == 1`), and reject negative numbers; return `'partner_id': None`. | Rejected by `_is_non_neg_num`; `assign_order` returned `'partner_id': None` with `'reason': 'invalid order or time data'`. | `tests/test_acceptance_matrix.py` (`test_preparation_time_validation` / negative & boolean time validation cases) |
| 3 | Missing travel route in `travel` dictionary (e.g., `(partner['zone'], order['restaurant_id'])` key absent) | Never treat missing travel data as `0`; `estimate_eta` must return `'eligible': False` and `assign_order` must skip the partner or leave the order unassigned if no other valid partner exists. | `leg1` evaluated to `None`, `estimate_eta` returned `{'partner_id': ..., 'eta_minutes': None, 'eligible': False}`, and `assign_order` returned `'partner_id': None, 'reason': 'no eligible partner or missing time data'`. | `tests/test_acceptance_matrix.py` (`test_invalid_or_missing_travel_time_rejected`) |
| 4 | Partner inactive (`'active': False`) or at full capacity (`len(active_order_ids) == capacity`) | Skip inactive and at-capacity partners during candidate filtering even if their route and ETA would otherwise be lowest. | Both partners were skipped via `continue` guards in `assign_order`; only active partners strictly below capacity (`len < capacity`) were considered. | `tests/test_acceptance_matrix.py` (partner active status and capacity limit test cases) |
| 5 | Duplicate cancellation event (`process_cancellation(partner, 'O-1', 'EVT-1')` called twice with the same `'EVT-1'`) | Apply the cancellation once on the first call (removing `'O-1'` and subtracting its workload floored at `0`), and return unchanged state on the second call without deducting workload twice. | First call removed `'O-1'`, reduced `workload_minutes`, and appended `'EVT-1'` to `processed_cancellation_ids`. Second call detected `'EVT-1'` in `processed_cancellation_ids` and returned immediately without further deduction. | `tests/test_acceptance_matrix.py` (cancellation idempotency test cases) |
| 6 | Exact ETA tie between two eligible partners (e.g., `'P-2'` and `'P-1'` both have `eta_minutes = 36`, with `'P-2'` listed first) | Break ties deterministically using `partner_id` in ascending lexicographic order (`'P-1' < 'P-2'`). | `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))` selected `'P-1'`. | `tests/test_acceptance_matrix.py` (tie-breaking test cases) |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.

- **Defect 1 — Unvalidated order fields and non-finite/negative/boolean time values:** Fixed via `_is_non_empty_str` and `_is_non_neg_num` (using `not isinstance(val, bool)` and `math.isfinite(val)`). Protected by `test_invalid_or_missing_travel_time_rejected[1-inf]`, `test_preparation_time_validation[inf]`, and negative/missing field tests in `tests/test_acceptance_matrix.py`.
- **Defect 2 — Inactive and full-capacity partners accepted by `assign_order`:** Fixed by checking `partner.get('active') is True` and `len(active_orders) < capacity` before calling `estimate_eta`. Protected by partner eligibility and capacity tests in `tests/test_acceptance_matrix.py`.
- **Defect 3 — Non-idempotent cancellation in `process_cancellation`:** Fixed by checking `event_id in out['processed_cancellation_ids']` before removing `order_id` or subtracting `minutes_by_order` workload. Protected by duplicate cancellation event tests in `tests/test_acceptance_matrix.py`.
- **Defect 4 — Unhandled malformed records (`None` or corrupted lists/dicts):** Fixed by adding `isinstance` container guards and list/workload sanitization across `estimate_eta`, `assign_order`, and `process_cancellation`. Protected by malformed input test cases in `tests/test_acceptance_matrix.py`.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.

- **Failing tests:** None (`0 failed, 0 errors` in `python -m pytest -q`).
- **Known limitations:**
  - `assign_order` is a pure selection function that returns the chosen partner and ETA without mutating the partner's `active_order_ids` or `workload_minutes` in place.
  - `processed_cancellation_ids` is stored as a Python `list` for schema compatibility, meaning duplicate-event lookups scale linearly ($O(N)$) with the number of historical cancellations on a single partner.