# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- **Commands run before editing**:
  - `python3 -m pytest -q`
  - `python3 -m main`
- **Initial test result (include the actual summary)**:
  - Total tests run: 229
  - Result: **65 failed, 164 passed in 0.60s**
  - Major failures included:
    - Type errors in travel/prep time addition (`TypeError: unsupported operand type(s) for +`)
    - Inactive and saturated partners being assigned (`AssertionError: assert 'P' is None`)
    - Duplicate cancellations not being idempotent (`AssertionError: assert ['C', 'C'] == ['C']`)
- **Demo/output observed**:
  - `python3 -m main` produced:
    `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. Codebase understanding
- **Important files/functions inspected**:
  - `service.py`: Main dispatch logic containing `estimate_eta`, `assign_order`, and `process_cancellation`.
  - `models.py`: Constructor factories `new_partner` and `new_order` defining data schemas.
  - `fixtures.py`: Sample data used for offline demo execution.
  - `tests/test_contract.py`, `tests/test_acceptance_matrix.py`, `tests/test_edge_cases.py`: Acceptance suite verifying formulas, boundary conditions, and idempotency.
- **Candidate filtering, ETA calculation, and capacity flow traced**:
  1. `assign_order` receives an order, candidate partner list, and travel time mapping.
  2. For each candidate partner, it must verify the partner is active and has spare capacity (`len(active_order_ids) < capacity`).
  3. `estimate_eta` looks up route leg 1 (partner zone to restaurant) and leg 2 (restaurant to destination zone). If either is missing, negative, or invalid, the candidate is ineligible.
  4. Pickup time is computed as $t_{\text{now}} + \text{leg1} + \text{workload}$, and ETA is $t_{\text{pickup}} + \text{prep} + \text{leg2}$.
  5. The candidate with minimum ETA is selected, breaking ties deterministically by ascending partner ID.
- **How you confirmed your understanding**:
  - By analyzing the parameterized test inputs in `tests/test_acceptance_matrix.py` and running isolated test slices to identify the exact assertions failing on the starter code.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.

- **Issue 1: Lack of strict numeric and boundary validation in `estimate_eta`**
  - *Symptom*: Unhandled `TypeError` when `None`, strings, or booleans were passed as time parameters, and failure to reject negative values or non-finite floats (`NaN`, `inf`).
  - *Hypothesis*: The starter code directly performed addition (`now + leg1 + partner.get('workload_minutes', 0)`) without checking type or domain boundaries.
  - *Evidence*: `test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[2-1]` raised `TypeError: unsupported operand type(s) for +: 'int' and 'str'`.
  - *Fix*: Introduced `_is_valid_non_negative_number` validating that values are numeric (`int`, `float`), not `bool` (since `isinstance(True, int)` is True in Python), finite (`math.isfinite`), and $\ge 0$.

- **Issue 2: Inactive and over-capacity partners assigned in `assign_order`**
  - *Symptom*: Partners with `active=False` or `len(active_order_ids) >= capacity` were being assigned orders.
  - *Hypothesis*: The starter loop contained a placeholder comment noting that active/capacity validation was intentionally omitted.
  - *Evidence*: `test_contract.py::test_inactive_partner_not_assigned` failed with `AssertionError: assert 'P' is None`.
  - *Fix*: Added explicit guards ensuring `partner.get('active') is True`, validating capacity is an integer $\ge 1$, and requiring `len(active_order_ids) < capacity`.

- **Issue 3: Cancellation duplicate events not idempotent in `process_cancellation`**
  - *Symptom*: Repeated cancellation calls with the same `event_id` deducted workload multiple times and appended duplicate event IDs.
  - *Hypothesis*: The starter code appended `event_id` to `processed_cancellation_ids` unconditionally without checking prior occurrence.
  - *Evidence*: `test_contract.py::test_duplicate_cancellation_is_idempotent` showed `processed_cancellation_ids == ['C1', 'C1']`.
  - *Fix*: Added an idempotency check: `if event_id in out['processed_cancellation_ids']: return out` before altering workload or order lists.

## 4. Implementation decisions
- **Main changes and why**:
  - Centralized numeric validation into a clean helper function `_is_valid_non_negative_number` to maintain DRY code across `now`, `prep_minutes`, `workload_minutes`, and travel legs.
  - Centralized identifier validation into `_is_valid_id` to ensure order and zone keys are non-empty strings.
  - Defensively cloned partner objects in `process_cancellation` via `deepcopy` to prevent unexpected mutations to caller data.
- **Alternatives considered and why rejected**:
  - *Relying on try-except TypeError during arithmetic*: Rejected because booleans in Python (`True == 1`) would be silently treated as 1 minute instead of invalid input, violating the specification.
  - *Modifying partner in-place in cancellation*: Rejected to maintain immutability and predictability across multiple simulation steps.
- **Assumptions**:
  - `active` status must be strictly boolean `True` (truthy values like `"yes"` or `1` are not treated as active).
  - Valid partner capacity is an integer $\ge 1$.

## 5. Verification
- **Tests added or changed**:
  - Created `tests/test_regression.py` with 7 dedicated test functions covering whitespace IDs, boolean workloads, negative workloads, unknown-order cancellation replay, capacity saturation, `None` arguments, and the optional stretch feature (`explain_candidates`).
  - Did not delete, alter, or weaken any starter tests.
- **Commands run and actual results**:
  - `python3 -m pytest -q` $\rightarrow$ **236 passed in 0.15s** (100% passing).
  - `python3 -m main` $\rightarrow$ Correct offline assignment demo output matching expected ETA and partner.
- **Optional stretch work implemented**:
  - Implemented candidate explanations (`explain_candidates`) returning transparent diagnostic reasons for eligible and rejected candidates.
- **Edge cases verified**:
  - String numbers, booleans, `NaN`, and `inf` in travel and prep times.
  - Missing route entries in travel dictionary.
  - Duplicate cancellation replay with same and different event IDs.
  - Inactive partner and capacity saturation boundary conditions.
- **Remaining failures or known limitations**:
  - No failing tests remaining. In-memory execution assumes single-process sequential execution.