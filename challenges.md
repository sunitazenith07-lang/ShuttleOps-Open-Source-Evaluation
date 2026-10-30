# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour

The hardest challenge was understanding why `bool` values needed special treatment in numeric validation. Python's `True` and `False` are instances of `int` (`isinstance(True, int)` returns `True`), so `True` passes an `isinstance(value, (int, float))` check. The test `test_invalid_or_missing_travel_time_rejected[True-1]` expected `eligible=False` for a travel time of `True`, and `test_capacity_boundary_matrix[True-0]` expected rejection of capacity `True`. This meant every numeric validation had to explicitly check `isinstance(value, bool)` first and reject it.

A related subtlety: `True == 1` and `True == 1.0` are both `True` in Python, so equality comparisons cannot distinguish them either. Only `isinstance` or `is` checks work.

## 2. Evidence

```
# Before fix — test failure:
test_invalid_or_missing_travel_time_rejected[True-1]
  assert result["eligible"] is False
  E  assert True is False

# Root cause in original service.py:
leg1 = travel.get(("Z","R"))  # returns True (a bool)
if leg1 is None or leg2 is None:  # True is not None, so this passes
    ...
pickup = now + leg1 + workload  # True is treated as 1, arithmetic succeeds silently
```

Similarly, in my own regression test during development, I wrote `if bad_leg1 == 1.0` to check for a valid float, but this branch also matched `True` because `True == 1.0`. I had to change it to `isinstance(bad_leg1, float) and bad_leg1 == 1.0`.

## 3. What I tried

1. First attempted validation with just `isinstance(value, (int, float)) and value >= 0` — this accepted `True`/`False` and failed the bool-related tests
2. Added `not isinstance(value, bool)` as the first check — this fixed the travel-time and capacity bool tests
3. Also needed to handle `float("nan")` and `float("inf")` — `nan >= 0` is `False` (rejects correctly), but `inf >= 0` is `True` (would accept infinity). Added explicit `math.isnan()` and `math.isinf()` checks
4. Traced each failing parametrized test case one-by-one to confirm the validation matched what the test expected as valid vs. invalid

## 4. Resolution

Root cause: the original `estimate_eta()` had zero type-checking — it only checked `is None`. The fix was creating a reusable `_is_valid_numeric()` function that enforces:
- Must be `int` or `float`
- Must NOT be `bool` (checked first, since `bool` is a subclass of `int`)
- Must not be `NaN` or `inf` (via `math.isnan`/`math.isinf`)
- Must be ≥ 0

This single function is used for travel times, prep_minutes, and the `now` parameter. It addresses the cause (missing validation) rather than hiding symptoms (try/except around arithmetic).

## 5. Proof and regression prevention

- `TestTravelTimeValidation::test_bad_leg1_rejected[True-3]` — confirms `True` as travel time is rejected
- `TestTravelTimeValidation::test_bad_leg2_rejected[3-True]` — same for leg2
- `test_invalid_or_missing_travel_time_rejected[True-1]` and `[1-False]` — original tests now pass
- `test_capacity_boundary_matrix[True-0]` — confirms `True` as capacity is rejected
- `test_preparation_time_validation[True]` — confirms `True` as prep is rejected

Related case that might still break: if a future change allows `numpy` numeric types (e.g., `numpy.int64`), the `isinstance(value, (int, float))` check would reject them. This is acceptable since the project uses only standard Python types.

## 6. Unresolved challenge or next step

No major unresolved issues. All 300 tests pass. One minor limitation: `workload_minutes` on the partner dict is not validated (it could theoretically be negative or non-numeric), but no existing test requires this validation, and adding it could break compatibility with the starter data flow. If time allowed, I would add workload validation in `_is_eligible_partner()` with corresponding tests.
