# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- **What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)?**
  - **Repeated Work & Early Exit:** In the starter `assign_order`, order validation did not exist before the `for partner in partners:` loop, and ineligible partners (inactive or at capacity) were passed directly into `estimate_eta` to perform dictionary lookups on `travel`.
  - **Maintainability & Duplicated Validation Logic:** Checking for non-empty strings and finite, non-boolean, non-negative numbers (`not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0`) across `estimate_eta`, `assign_order`, and `process_cancellation` caused verbose, error-prone inline conditions.
  - **Unnecessary Work on Duplicate Cancellations:** In `process_cancellation`, the starter code scanned `active_order_ids` and recalculated `workload_minutes` even when `event_id` had already been processed.
- **What evidence suggested an improvement could help?**
  - Code inspection of `service.py` showed that an invalid order (e.g., negative or `inf` `prep_minutes` or missing `restaurant_id`) would still iterate through all $N$ partners in `partners` before returning an unassigned result. Similarly, inline type checks repeated 4 booleans per time variable across multiple functions.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.

- **Option 1: Pre-loop order validation and cheap partner guard clauses before calling `estimate_eta` (Accepted)**
  - **Expected Benefit:** Validates `order` and `now` once in $O(1)$ time before iterating over `partners`. Inside the loop, checks `active is True` and `len(active_order_ids) < capacity` before calling `estimate_eta`, avoiding unnecessary function calls and tuple-keyed `travel` lookups for disqualified partners.
  - **Risk:** Minimal; requires ensuring `estimate_eta` still retains its own independent validation when called directly by unit tests.
- **Option 2: Extracting `_is_non_empty_str` and `_is_non_neg_num` helper functions (Accepted)**
  - **Expected Benefit:** Centralizes string and numeric validation (including `not isinstance(val, bool)` and `math.isfinite(val)`) in one place, improving readability and eliminating the risk of forgetting a `bool` or `inf` check on a single field.
  - **Risk:** Slight function-call overhead in Python, which is negligible for small in-memory dispatch inputs compared to the gain in correctness and maintainability.
- **Option 3: Converting `processed_cancellation_ids` and `active_order_ids` from `list` to `set` (Rejected)**
  - **Expected Benefit:** Would reduce membership checks (`event_id in out['processed_cancellation_ids']` and `order_id in out['active_order_ids']`) from $O(N)$ list scans to $O(1)$ hash lookups.
  - **Reason Rejected:** `models.py` and the acceptance test suite (`tests/test_acceptance_matrix.py`) explicitly expect `active_order_ids` and `processed_cancellation_ids` to be serialized as Python `list` objects. Changing their type to `set` would break schema compatibility with caller expectations and tests.

## 3. Changes implemented
- **Change and reason:**
  1. **Pre-loop validation in `assign_order`:** Checked `order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`, `now`, `travel`, and `partners` once at the top of `assign_order` to fail fast in $O(1)$ time when the order or global input is invalid.
  2. **Early `continue` guards in `assign_order`:** Filtered out inactive partners, full partners (`len(active_orders) >= capacity`), and partners with invalid `workload_minutes` before invoking `estimate_eta`.
  3. **Early idempotency return in `process_cancellation`:** Checked `if not _is_non_empty_str(event_id) or event_id in out['processed_cancellation_ids']: return out` before searching `active_order_ids` or computing workload subtraction.
  4. **Centralized validation helpers (`_is_non_empty_str`, `_is_non_neg_num`):** Consolidated type, boolean, finiteness (`math.isfinite`), and sign checks into reusable helpers.
- **Tests that protect correctness:**
  - Verified against the full pytest suite in `tests/test_acceptance_matrix.py` (including `test_invalid_or_missing_travel_time_rejected[1-inf]`, `test_preparation_time_validation[inf]`, tie-breaking, eligibility, and cancellation idempotency tests).
- **Measurement method and result (only if measured):**
  - Not benchmarked for wall-clock speedup; changes were made primarily for correctness, fail-fast behavior (avoiding $O(N)$ partner iterations on invalid orders), and maintainability. All tests in `python -m pytest -q` pass (`0 failed, 0 errors`).

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.

- **Defensive Validation in Both `assign_order` and `estimate_eta` (Correctness vs. Redundant Checks):**
  - Both `assign_order` and `estimate_eta` validate `prep_minutes`, `now`, and `workload_minutes`. While this introduces minor redundant checks when `assign_order` calls `estimate_eta`, it guarantees that calling `estimate_eta` directly in isolation is just as safe against `None`, `bool`, negative numbers, and `float('inf')` as calling `assign_order`.
- **Deep Copy in `process_cancellation` (Safety/Immutability vs. Memory/CPU):**
  - `copy.deepcopy(partner)` allocates a new dictionary and nested lists on every call, which costs $O(K)$ memory and time proportional to the partner record size. However, this trade-off is essential to prevent mutating the caller's input dictionary in place when an event is ignored or applied.

## 5. Further improvements
What would you do next with more time, and how would you validate it?

- **Maintain a Companion Set or Bounded Index for Idempotency:** If a partner processes thousands of cancellation events over a long shift, `event_id in out['processed_cancellation_ids']` degrades linearly ($O(M)$ where $M$ is the number of processed events). With more time, I would benchmark `process_cancellation` using `timeit` with $10{,}000$ historical event IDs and store an internal `_processed_cancellation_set` (or use an `OrderedDict` as a bounded LRU cache) alongside the list to achieve $O(1)$ duplicate detection while keeping the public list intact.
- **Single-Pass Minimum Selection Without Intermediate List Allocation:** Currently `assign_order` appends all eligible estimates to `options = []` and then runs `min(options, ...)`. Tracking `best_choice = None` directly inside the loop would reduce auxiliary memory from $O(N)$ to $O(1)$, which I would validate against the existing tie-breaking test suite.