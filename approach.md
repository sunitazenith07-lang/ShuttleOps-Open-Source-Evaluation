# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
    "First we clone the repository of the given problem statement then run the following commands."
    - `python -m pip install -r requirements-dev.txt`
    - `python -m pytest -q`
    - `python -m main`
- Initial test result (include the actual summary):
    - `Ran the initial baseline test suite on the starter` `service.py`.
    - `Total Test case runs : 229 in which 164 Test case passed and 65 Test case failed`
    - ` Then i observed the failure and categorised it `
        `1. Missing validations like Restaurant IDs and partner IDs `
        `2. Capacity checks and non-negetaive number checks `
        `3.  process of cancellation `
- Demo/output observed:
    - ` Executed the code and run it and it shows `
        `= total test case runs: 229`
        `= 164 test case passed`
        ``= 65 test case failed`
## 2. Codebase understanding
- Important files/functions inspected:
    - `service.py (estimate_eta, assign_order, process_cancellation)`
    - `models.py (new_partner, new_order)`
    - `fixtures.py (sample_inputs)`
- Candidate filtering, ETA calculation, and capacity flow traced:
   - `Candidate filtering : traced through `assign_order` siterates through partners, filters out inactive partners or those at/above their order capacity, delegates ETA calculation to `estimate_eta`, and picks the lowest ETA candidate with tie-breaking on partner_id in ascending lexicographic order.`
    - `Traced how `estimate_eta` performs tuple-key lookups on the `travel` dictionary for leg 1 and leg 2, adding current time (`now`), partner workload( time remaining in previous orders), and preparation time(prepration time and travel time to reach the customer).`
    - `Traced how `process_cancellation` removes active orders, decrements workload safely using `max(0, ...)`, and records event IDs`
- How you confirmed your understanding:
    - `By inspecting  data structures, running unit tests, and verifying behavior against the required acceptance contract and running the code many times and understanding code many times`
## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Time and Special Float Validation (`nan` / `inf` / Booleans / Negatives)
  - Symptom: Tests with `float('nan')`, `float('inf')`, boolean values (`True`), or negative numbers raised type errors or incorrect eligibility.       
  - Hypothesis: Standard `< 0` comparisons fail or behave unexpectedly on `nan`/`inf`, and Python treats `bool` as a subclass of `int`.
  - Evidence: Test failures like `test_invalid_or_missing_travel_time_rejected[nan-1]` and `test_preparation_time_validation[nan]`.
  - Fix Chosen: Implemented robust type and value checking using `isinstance(t, (int, float))`, `not isinstance(t, bool)`, `math.isfinite(t)`, and `t >= 0`.
- Issue 2: Capacity Boundary Type Enforcement
  - Symptom: Passing non-integer capacities like `1.5`, `True`, or `None` caused comparison errors or improper order allocation.
  - Hypothesis: Capacity must be a strict integer count of active orders.
  - Evidence: Failures in `test_capacity_boundary_matrix` with inputs like `1.5` or `True`.
  - Fix Chosen: Enforced strict integer type checking (`isinstance(capacity, int)` and `not isinstance(capacity, bool)`) for capacity evaluation.
- Issue 3 (if applicable): Malformed Inputs & Whitespace IDs
  - Symptom: `None` inputs caused `AttributeError` on `.get()`, and whitespace-only strings (`"   "`) bypassed basic truthiness checks.
  - Hypothesis: Input records and IDs require strict type safety and sanitization.
  - Fix Chosen: Added fail-safe dictionary checks (`isinstance(..., dict)`) and string sanitization using `.strip()` across order/partner IDs and zones.
- Issue 4 : Duplicate Cancellation Idempotency
  - Symptom: Duplicate cancellation events processed the same `event_id` multiple times, releasing workload incorrectly.
  - Hypothesis: `processed_cancellation_ids` must be checked before applying cancellation state changes.
  - Fix Chosen: Implemented an early return check (`if event_id in out['processed_cancellation_ids']: return out`) at the beginning of `process_cancellation`.

## 4. Implementation decisions
- Main changes and why:
    - Added fail-fast type guards and `math.isfinite` checks to prevent crashes on edge-case numbers.
    - Sanitized ID fields with `.strip()` to reject whitespace strings.
    - Enforced strict integer capacity validation.
    - set rule for the cancellations if one cancel happens so after network glitch it doesn`t appear again  if it appear it effects the workload
- Alternatives considered and why rejected:
    - Using custom exception classes for invalid input; rejected in favor of returning safe fallback dictionaries (`eligible: False` or unassigned reason) to keep the contract clean and deterministic because for eligible and false  fallback  application reject it and does not crash.
- Assumptions:
    - Missing travel data means the partner is ineligible.
## 5. Verification
- Tests added or changed: Relied on the comprehensive build in in the test and verified and fixes  it without modifying or weakening existing tests.
- Commands run and actual results:
    - `python -m pytest -q`-> 229 passed in 0.29s
- Edge cases verified:
    `nan`/`inf` travel and prep times, non-integer capacities (`1.5`, `True`), whitespace-only IDs, `None` record inputs, and duplicate order cancellations.
- Remaining failures or known limitations:
    No remaining failure . All test cases pass successfully in the terminal.
Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.