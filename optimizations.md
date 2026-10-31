# optimizations.md - Required submission

## 1. Baseline and objective

- **What needed improvement:** The starter `service.py` lacked input validation entirely. The primary objective was correctness, making existing tests pass by adding the missing validation, filtering, and idempotency logic.
- **What evidence suggested an improvement could help:** tests were failing, all due to missing guards in three functions. The code comments explicitly stated the defects ("Starter is intentionally incomplete: active/capacity/time validation is missing" and "Starter defect: event_id is recorded but not checked before applying the event").

## 2. Options considered

### Option A: Inline all validation in each function (rejected)
- Benefit: No new helper functions, simpler call structure
- Risk: Code duplication - the same `isinstance(value, bool)` / `math.isnan()` / `math.isinf()` checks would be repeated for leg1, leg2, prep, and now (at least 4 places)
- Rejected because: Violates DRY principle, harder to maintain, easy to miss one case

### Option B: Extract reusable validation helpers (chosen)
- Benefit: Single source of truth for "is this a valid numeric time value?". Each helper is small, testable, and named clearly
- Risk: Slight indirection — reader must look up `_is_valid_numeric()` to understand what it checks
- Chosen because: Eliminates duplication, makes adding new validated fields easy, and the underscore-prefix convention signals these are internal helpers

### Option C: Validate at construction time in `new_order()`/`new_partner()` (rejected)
- Benefit: Invalid data never enters the system
- Risk: Tests modify dicts after construction (e.g., `partner["active"] = False`), so construction-time validation would not catch test scenarios
- Rejected because: Would require a fundamental redesign of the data model (e.g., using classes with property setters), which is out of scope

### Option D: Use try/except around arithmetic instead of explicit checks (rejected)
- Benefit: Catches TypeErrors from string/None values
- Risk: Negative numbers and `float("inf")` compute without errors, producing silently wrong results. `-5 + 3` returns `-2`, which is a valid Python operation but a nonsensical travel time
- Rejected because: It hides bugs rather than preventing them

## 3. Changes implemented

- **Change:** Created four private helper functions (`_is_valid_numeric`, `_is_valid_travel_time`, `_is_valid_order`, `_is_eligible_partner`) and integrated them into the three main service functions
- **Reason:** Centralised validation logic, eliminated code duplication, made each validation rule independently testable
- **Tests that protect correctness:** 71 regression tests in `tests/test_regressions.py` across 10 test classes, plus all 229 original tests
- **Measurement method and result:** `python -m pytest -q` runs all 300 tests. No measurable performance regression from the added validation — the checks are O(1) per partner per call

## 4. Trade-offs

| Trade-off | Decision |
|-----------|----------|
| **Strictness vs. flexibility** | Chose strict: `active` must be exactly `True`, capacity must be `int` not `float`. This matches test expectations but could reject valid-looking data like `active=1` |
| **Validation location** | Chose dispatch-time validation over construction-time. More defensive but means invalid data can exist in memory until dispatch is called |
| **Bool rejection** | Explicitly rejecting `bool` adds a line to every check, but prevents the subtle `True == 1` bug. Correctness outweighs brevity |
| **Helper function overhead** | Four extra function calls per partner per dispatch. Negligible for the dataset size (60 partners), but for millions of partners a flattened approach might matter. Readability was prioritised over micro-optimisation |
| **Deep copy in cancellation** | `deepcopy(partner)` is preserved from the starter. It's safe (no mutation of input) but allocates a new dict each call. For high-throughput cancellation streams, in-place mutation with explicit state tracking could be faster |

## 5. Further improvements

With more time, I would:

1. **Validate `workload_minutes`** on the partner — reject negative or non-numeric values, similar to how travel times are validated. Would need corresponding tests.
2. **Add batch assignment** — process multiple orders in priority order, updating partner state after each assignment so capacity is tracked across the batch.
3. **Use dataclasses models** instead of plain dicts — this would enforce types at construction time and eliminate the need for runtime `isinstance` checks. Trade-off: more boilerplate, but catches errors earlier.
4. **Index the travel map** — for very large travel datasets, a lookup by `(zone, restaurant)` in a flat dict is already O(1), but validating all travel entries upfront (once) rather than per-call could reduce repeated checks.
5. **Measure validation overhead** — profile the dispatch path with the full `records.json` dataset (387 travel times, 60 partners) to confirm the validation helpers add negligible overhead. I would use `pytest-benchmark` or Python's `timeit`.
