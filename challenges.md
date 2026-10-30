# challenges.md. COMPULSORY submission

## 1.. Confusing behaviour

The hardest part was figuring out why boolean values needed special handling in numeric validation. In Python `and `False` are actually subclasses of `int`. So when you check `isinstance(True, int)` it returns `True`. That means `True` gets through a validation check like `isinstance(value, (int float))`.. The tests expected that `True` should not be accepted as a valid number. For example `test_invalid_or_missing_travel_time_rejected[True-1]` expected `=False` when travel time was `True`.. Test_capacity_boundary_matrix[true-0]` expected capacity `True` to be rejected. This meant every numeric validation had to check if the value was a boolean and reject it if it was.

Another tricky thing is that ` == 1` and `True == 1.0` both evaluate to `True`. So you can't use equality checks to differentiate them. Only `isinstance` or `is` checks work properly.

## 2. Evidence

```

# Before fix. Test failure:

test_invalid_or_missing_travel_time_rejected[True-1]

assert result["eligible"] is False

E  assert True is False

# Root cause in service.py:

leg1 = travel.get(("Z","R"))  # returns True (a bool)

if leg1 is None or leg2 is None:  # True is not None. This passes

...

pickup = now + leg1 + workload  # True is treated as 1 arithmetic succeeds silently

```

During my own testing I wrote a check like `if bad_leg1 == 1.0` to see if a float was valid. But that didn’t work because `True == 1.0` is `True`. I had to change it to `isinstance(bad_leg1, float) and bad_leg1 == 1.0`.

## 3. What I tried

1. First I tried validating with isinstance(value, (int, float)) and value >= 0`. This allowed `True` and `False` to pass which broke the tests.

2. Then I added `not isinstance(value, bool)` as the first check. That fixed the issues with travel time and capacity tests.

3. I also had to handle `float("nan")`. Float("inf")`. `Nan >= 0` returns `False` which's correct but `inf >= 0` returns `True`. So I added `math.isnan()`. Math.isinf()` checks to reject those cases.

4. I went through each failing test case one by one to make sure the validation matched what the test expected for valid and invalid inputs.

## 4. Resolution

The root cause was that the original `estimate_eta()` function had no type checking. It only checked for `None`. The fix was to create a _is_valid_numeric()` function that checks:

- The value must be an `int` or `float`

- It must not be a `bool` (checked first because bool is a subclass of int)

- It must not be `NaN` or `inf` (using `math.isnan()` and `math.isinf()`)

- It must be greater than or equal to zero

This single function is now used for travel times, prep minutes and the `now` parameter. It fixes the problem instead of just hiding it under try/catch blocks.

## 5. Proof and regression prevention

- `TestTravelTimeValidation::test_bad_leg1_rejected[True-3]`. Confirms `True` as travel time is rejected

- `TestTravelTimeValidation::test_bad_leg2_rejected[3-True]`. Same for leg2

- `test_invalid_or_missing_travel_time_rejected[True-1]` and `[1-]`. Original tests now pass

- `test_capacity_boundary_matrix[True-0]`. Confirms `True` as capacity is rejected

- `test_preparation_time_validation[True]`. Confirms `True` as prep time is rejected

One edge case that might still break things: if a future change allows `numpy` numeric types like `numpy.int64` the `isinstance(value, (int float))` check would reject them. That’s acceptable since the project only uses Python types.

## 6. Unresolved challenge or next step

There are no unresolved issues. All 300 tests pass. One small limitation is that `workload_minutes`, on the partner dict is not validated. It could be negative or non-numeric. No existing test requires validation. Adding it might break compatibility with the data flow. If I had time I would add validation in `_is_eligible_partner()` and write tests for it.