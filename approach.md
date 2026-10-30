# Approach — SmartDispatch Assignment and ETA

## 1. Baseline

- Before editing, I ran `python -m pytest -q` against the starter implementation.
- Baseline result: **65 failed, 164 passed**. Failures covered invalid travel and
  preparation times, inactive and full partners, invalid current time, invalid
  order fields, and duplicate cancellation handling.
- I did not run the demo before editing. After the implementation changes,
  `python -m main` completed and printed:
  `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding

- I inspected `service.py`, `models.py`, `fixtures.py`, `main.py`, the three
  visible test modules, `STUDENT_PROBLEM_STATEMENT.md`, `README.md`, and the
  project test configuration.
- `models.py` defines orders and partners as dictionaries. A partner includes
  an active flag, capacity, active order IDs, remaining workload, per-order
  workload, and processed cancellation IDs.
- `estimate_eta` is the calculation boundary. It reads two required entries
  from the travel-time mapping: partner zone to restaurant, then restaurant to
  destination zone. The required formulas are:
  - Pickup = current time + first travel leg + partner workload.
  - ETA = pickup + preparation time + second travel leg.
- `assign_order` filters candidate partners, estimates ETAs for candidates with
  valid route data, and chooses the lowest ETA. The contract requires an
  ascending partner-ID tie-break when ETAs match.
- `process_cancellation` returns an updated partner record. Cancellation must
  remove the order and its workload once, while remembering event IDs to make
  repeated delivery of the same event safe.
- I confirmed the behavior and intended edge cases by comparing the stated
  contract with assertions in `tests/test_contract.py`,
  `tests/test_acceptance_matrix.py`, and `tests/test_edge_cases.py`, and by
  running the tests before and after the change.

## 3. Investigation and implementation strategy

### Issue 1: Invalid numeric and order data could produce an ETA

- **Symptom:** The starter calculation accepted negative travel and preparation
  times and could attempt arithmetic with malformed values. It treated missing
  routes specially, but did not validate present route values, `now`, or the
  required order identifiers.
- **Evidence:** Baseline cases in the acceptance matrix failed for negative,
  string, boolean, NaN, and infinite travel/preparation values, invalid current
  times, and invalid order fields.
- **Fix:** Added small validation helpers for non-negative numeric values,
  identifiers, and required order fields. Booleans are explicitly excluded
  from numeric values, and floating-point values must be finite. `estimate_eta`
  now returns an ineligible result with `eta_minutes=None` when an input or a
  required route value is invalid. It also checks the calculated pickup and ETA
  so arithmetic overflow cannot produce an eligible result with a non-finite
  time.

### Issue 2: Assignment did not enforce partner eligibility and capacity

- **Symptom:** The starter considered every partner with route data, without
  checking whether the partner was active or still had order capacity.
- **Evidence:** The contract tests for inactive and full partners failed in the
  baseline. The acceptance matrix exercises capacity boundaries, including
  zero, invalid capacity types, and a partner exactly at capacity.
- **Fix:** `assign_order` now skips malformed partner records, partners whose
  `active` value is not exactly `True`, invalid partner identifiers/zones,
  invalid capacities, and partners whose active-order count meets or exceeds
  capacity. Remaining candidates still use `estimate_eta`; selection remains
  lowest ETA with partner ID as a deterministic tie-breaker.

### Issue 3: Repeated cancellation events were not idempotent

- **Symptom:** The starter appended cancellation event IDs but never checked
  whether an event had already been processed.
- **Evidence:** The baseline duplicate-cancellation tests showed that repeated
  processing could apply a cancellation more than once. The test matrix also
  checks workload clamping and cancellation of an order that is not active.
- **Fix:** `process_cancellation` now checks the processed-event list before
  applying an event. For a new event, it removes a matching active order and
  subtracts that order's recorded workload, clamping the result at zero. It
  records each valid event ID once. Unknown or absent order IDs do not release
  another order's workload.

## 4. Implementation decisions

- **Input validation is shared.** `_is_nonnegative_number`,
  `_is_valid_identifier`, and `_is_valid_order` keep the rules consistent
  between direct ETA estimates and full assignment. This prevents a caller
  from bypassing validation by calling `estimate_eta` directly.
- **Missing travel data is not zero.** A missing key, `None`, negative number,
  boolean, non-number, NaN, or infinity makes that estimate ineligible. A
  zero-minute route remains valid.
- **Assignment keeps its existing result shape.** A successful assignment
  includes the order ID, partner ID, pickup, ETA, and `"assigned"` reason.
  Invalid orders return no partner and `"invalid order data"`; when no
  candidate remains, the existing no-candidate reason is retained.
- **Candidate order does not control ties.** The selection key is `(ETA,
  partner_id)`, so equivalent candidates produce a deterministic result
  regardless of their input order.
- **Cancellation updates a copy.** The function deep-copies a mapping before
  updating it, preserving the caller's original partner record. A duplicate
  event returns that copied state without applying the cancellation again.
- **I kept the scope limited to core behavior.** I did not add batch
  assignment, alter tests, or change the data model. The visible tests already
  express the contract and gave focused feedback on these defects.

## 5. Verification

- **Tests added or changed:** None. I left the supplied tests unchanged and used
  them as the acceptance and regression suite.
- **Baseline command/result:** `python -m pytest -q` — **65 failed, 164 passed**
  before editing.
- **Final command/result:** `python -m pytest -q` — **229 passed**.
- **Demo:** `python -m main` — completed successfully and assigned order `O-7`
  to partner `P-2`, with pickup `13` and ETA `35` minutes.
- **Static checks:** Pylance file syntax validation found no syntax errors;
  Pylance diagnostics for `service.py` returned no diagnostics. `git diff
  --check` completed without reporting whitespace errors.
- **Edge cases covered by the existing suite:** absent/invalid route times;
  negative, boolean, NaN, or infinite times; invalid preparation times and
  current time; inactive partners; partners at or above capacity; stable
  lowest-ETA and partner-ID tie-breaking; duplicate cancellation; unknown
  cancellation order; and workload subtraction that must not go below zero.
- **Remaining failures or known limitations:** None of the supplied tests
  failed in the final run. The public functions remain dictionary-based and do
  not define a broader schema or logging policy for malformed external data;
  those concerns were outside the tested assignment behavior.
