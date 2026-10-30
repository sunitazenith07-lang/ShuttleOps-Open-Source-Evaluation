# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most challenging behavior was handling strict parameter validation across edge-case data types without breaking expected assignment outcomes or raising unhandled runtime exceptions. Specifically:
1. Python treats `bool` as a subclass of `int` (`isinstance(True, int)` evaluates to `True`), which allowed boolean values passed in fields like `capacity` or `prep_minutes` to bypass naive numeric checks.
2. In `process_cancellation`, recording `event_id` only when an order was currently present in `active_order_ids` created an idempotency flaw where duplicate cancellation events for already-removed orders would not be tracked properly in `processed_cancellation_ids`.

## 2. Evidence
- **Type Checking Defect:** A test case passing `capacity = True` or string representations like `'5'` would either accept invalid partners or produce unexpected boolean arithmetic (`True + 5 = 6`).
- **Cancellation Defect:** Inspecting `process_cancellation(partner, order_id, event_id)` showed that if `order_id` was not in `active_order_ids`, the function returned early or skipped appending `event_id` to `processed_cancellation_ids`, allowing duplicate cancellation events to pass unrecorded on subsequent calls.

## 3. What I tried
1. **Attempt 1 (Basic `< 0` and `is None` checks):** Updated `estimate_eta` to check if values were `< 0` or `None`. This failed because `True < 0` evaluated to `False` and passed as valid numeric data.
2. **Attempt 2 (`try-except float()` coercion):** Attempted converting all time parameters using `float(val)`. This converted string inputs like `'10'` into valid numbers, violating strict schema validation requirements that reject string inputs outright.
3. **Attempt 3 (Explicit Type Guarding Helper):** Implemented `is_valid_number(val)` to explicitly filter `bool`, `str`, `None`, `NaN`, `inf`, and negative values. This correctly enforced strict typing while allowing valid `int` and `float` numbers.

## 4. Resolution
- **Root Cause (Validation):** Reliance on Python's loose truthiness and implicit type coercion allowed malformed data types to enter ETA calculations.
- **Root Cause (Cancellation):** Order-state mutation was tightly coupled with event-ID tracking, meaning non-active order cancellations ignored event recording.
- **Fix Applied:**
  - Standardized input validation using `is_valid_number()` across `estimate_eta` and `assign_order`.
  - Updated `process_cancellation` to unconditionally record `event_id` in `processed_cancellation_ids` on first encounter before evaluating `active_order_ids`.
- **Why it fixed the cause:** Enforcing event recording prior to state modifications guarantees idempotency regardless of current partner state, and strict type guarding prevents corrupted calculation states.

## 5. Proof and regression prevention
- **Demonstrating Tests:** All 229 unit tests in the pytest suite (`python -m pytest -q`) passed successfully.
- **Related Cases to Watch:** Changes to partner schema formats (e.g., introducing nested workload structures or multi-zone partner locations) must ensure strict schema validation is extended to those new attributes.

## 6. Unresolved challenge or next step
- **Remaining Limitations:** If travel matrix entries are missing for an origin-destination pair, the system correctly treats the partner as ineligible, but does not currently suggest alternative routes or multi-leg transfers.
- **Next Step:** Introduce fallback route resolution or dynamic distance estimation (e.g., straight-line Euclidean distance fallback with a penalty factor) if missing travel data becomes common in real-world scenarios.