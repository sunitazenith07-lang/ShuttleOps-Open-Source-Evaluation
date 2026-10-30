# challenges.md — COMPULSORY submission

## 1. Challenge or confusing behaviour

The most confusing aspect was correctly rejecting boolean values from time fields.
In Python, `bool` is a subclass of `int`: `isinstance(True, int)` returns `True`,
and `True == 1` and `False == 0`. This means that if you write a number check as
`isinstance(value, (int, float))`, the boolean values `True` and `False` silently
pass as valid times of 1 and 0 respectively.

The test `test_invalid_or_missing_travel_time_rejected[True-1]` failed on the
unmodified starter and revealed this behaviour.

A secondary challenge was detecting `float('nan')`. Standard equality and comparison
checks do not work for NaN because NaN is defined to be not equal to any value,
including itself.

## 2. Evidence

**Boolean slip-through (actual test failures):**

```
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-False]
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[True]
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[True]
```

The test set `travel[('Z','R')] = True` and expected `eligible=False`. The original
code returned `eligible=True` because `True` passed the `is None` check and was
used in arithmetic as the integer `1`.

**NaN arithmetic behaviour (verified manually in the Python shell):**

```python
>>> float('nan') > 0
False
>>> float('nan') < 0
False
>>> float('nan') >= 0
False
>>> float('nan') != float('nan')
True
```

NaN silently fails all standard comparison checks without raising an error,
making it impossible to detect with a simple `>= 0` guard alone.

## 3. What I tried

**For the boolean problem:**

First I tried `if not isinstance(value, (int, float))` — but `True` still passed
because `isinstance(True, int)` is `True`. I then realised that checking for `bool`
*first*, before the int/float check, was necessary. Moving the bool guard to the
very first line of `is_valid_time` fixed it:

```python
if isinstance(value, bool):
    return False
```

**For the NaN problem:**

I tried `if value < 0` — NaN silently returns `False` for this comparison, so NaN
appeared to be non-negative and slipped through. I then used `if value != value`,
which is `True` only for NaN because NaN is the only Python value not equal to
itself. I confirmed this behaviour in the Python shell before committing it.

## 4. Resolution

**Root cause for booleans:** Python's inheritance hierarchy makes `bool` a subtype
of `int`. The fix is to check `isinstance(value, bool)` first and return `False`
immediately, before the broader `isinstance(value, (int, float))` check that would
otherwise accept it.

**Root cause for NaN:** Standard comparison operators return `False` for any
comparison involving NaN rather than raising an error. The idiomatic Python
detection is `value != value`, which evaluates to `True` only for NaN.

Both issues are addressed inside the `is_valid_time` helper function in `service.py`,
lines 21 and 30 respectively.

## 5. Proof and regression prevention

**Boolean rejection is tested by:**

```
tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]   PASSED
tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-False]  PASSED
tests/test_acceptance_matrix.py::test_preparation_time_validation[True]                 PASSED
tests/test_acceptance_matrix.py::test_current_time_validation[True]                     PASSED
tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[True-0]                  PASSED
```

All five pass after the fix. If the bool guard were removed from `is_valid_time`,
these tests would immediately fail again.

**NaN rejection is tested by:**

```
tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[nan-1]   PASSED
tests/test_acceptance_matrix.py::test_preparation_time_validation[nan]                  PASSED
```

A related case: `float('inf')` must also be rejected. The `is_valid_time` function
explicitly checks for positive and negative infinity on the line after the NaN check.

## 6. Unresolved challenge or next step

No major blocker remained unresolved. All 235 tests pass after the fixes.

The hardest edge case deliberately tested was the combination scenario in
`test_correct_partner_selected_from_mixed_pool` (in `tests/test_regression.py`):
a partner pool containing an inactive partner, a full-capacity partner, a partner
with a missing travel route, and one fully eligible partner — all passed to
`assign_order` in the same call. This confirmed that all four disqualification
rules work correctly in combination, and that the only eligible partner is always
selected regardless of input list order.

If this project were extended to load from `data/records.json`, the travel-time
rows would need to be converted from their JSON list format into the tuple-key
dictionary expected by `service.py`. That conversion is not covered by the current
automated tests and would be the natural next area to investigate.