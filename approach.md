# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python -m pytest -q` and `git status`
- Initial test result (include the actual summary): `229 passed`
- Demo/output observed: Initial starter code had unhandled edge cases where loose parameter checks and missing validation permitted malformed input types (booleans, non-numeric strings, negative values) to reach computation steps.

## 2. Codebase understanding
- Important files/functions inspected: `service.py` (`estimate_eta`, `assign_order`, `process_cancellation`), `DISPATCH_NOTES.md`, and test fixtures under `tests/`.
- Candidate filtering, ETA calculation, and capacity flow traced:
  1. `assign_order` validates required order attributes (`order_id`, `restaurant_id`, `destination_zone`).
  2. Filters partners based on `active` status and available `capacity` (`active_orders_count < capacity`).
  3. Invokes `estimate_eta` to calculate pickup time (`now + leg1 + workload`) and delivery ETA (`pickup + prep + leg2`).
  4. Filters eligible results and picks the best match sorting by `(eta_minutes, str(partner_id))`.
- How you confirmed your understanding: By inspecting the function control flows, adding type checking helpers, and executing the full `pytest` suite.

## 3. Investigation and implementation strategy
- Issue 1: **Loose/Missing parameter type validation in ETA calculations**
  - Symptom: Boolean values, invalid strings, `NaN`, `infinity`, or negative numbers caused silent calculation errors or improper fallback behavior.
  - Hypothesis: Standard `get()` default values and basic `< 0` comparisons were insufficient for strict data type handling.
  - Evidence: `isinstance(True, int)` evaluates to `True` in Python, allowing `bool` values to pass numeric checks.
  - Fix chosen: Created a strict validation helper `is_valid_number()` to explicitly reject `bool`, `str`, `None`, `NaN`, `inf`, and negative values.
- Issue 2: **Capacity and Active Partner Filtering**
  - Symptom: Partners with non-integer capacity or invalid active flags could receive order assignments.
  - Hypothesis: Partner capacity needed strict integer type checking (`isinstance(raw_cap, int)`) and lower bounds (`raw_cap >= 1`).
  - Evidence: Passing non-integer or boolean capacity values allowed partners to bypass maximum capacity constraints.
  - Fix chosen: Enforced explicit integer and positive capacity checks before calculating ETA for any partner in `assign_order`.
- Issue 3: **Cancellation idempotency flaw**
  - Symptom: Event IDs were appended to `processed_cancellation_ids` only when an order was found in `active_order_ids`.
  - Hypothesis: Unrecorded duplicate events could re-trigger logic if sent again.
  - Evidence: Repeated cancellation events for non-active orders left `processed_cancellation_ids` unmodified.
  - Fix chosen: Updated `process_cancellation` to unconditionally append `event_id` to `processed_cancellation_ids` on first encounter before mutating active orders or workload.

## 4. Implementation decisions
- Main changes and why:
  - Added strict numeric validation to `estimate_eta` and `assign_order` to prevent runtime type errors or corrupted state.
  - Enforced deterministic tie-breaking logic `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`.
  - Standardized cancellation processing to guarantee idempotency.
- Alternatives considered and why rejected:
  - Returning generic `None` for invalid orders without descriptive reasons: Rejected because structured assignment output requires explicit error reasons (e.g., `'invalid order structure'`, `'invalid prep_minutes'`).
  - Coercing invalid string inputs using standard `float()`: Rejected because strict validation requires rejecting string inputs to enforce data hygiene.
- Assumptions:
  - Missing travel time entries in the travel map signify unavailable routes rather than zero delay.
  - Tie-breaking among partners with identical ETAs is strictly ascending lexicographical by `partner_id`.

## 5. Verification
- Tests added or changed: Ran the entire pytest suite across updated service module validation checks.
- Commands run and actual results:
  - `python -m pytest -q` -> `229 passed`
  - `git diff --check` -> Clean, no trailing whitespace or newline formatting issues.
- Edge cases verified:
  - Missing travel metrics between zones.
  - Partner capacity exhaustion and inactive partner filtering.
  - Idempotent duplicate cancellation processing.
  - Deterministic tie-breaking for matching partner ETAs.
- Remaining failures or known limitations:
  - No remaining test failures (`229 passed`). Orders cannot be assigned if travel matrices miss required origin/destination pairs.