# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most subtle defect encountered involved Python's type hierarchy when validating preparation times and travel durations. Specifically, passing boolean values like `True` or `False` to arithmetic operations did not raise a `TypeError` because in Python, `bool` is a subclass of `int` (`isinstance(True, int) is True`). Consequently, passing `prep_minutes=True` silently calculated `now + leg1 + 1` instead of rejecting the input. A second challenge occurred during test execution across directory boundaries, where running `pytest` from the parent workspace caused module collection failures.

## 2. Evidence
- Baseline test failure: `test_preparation_time_validation[True]` failed because `result["eligible"]` was `True` instead of `False`.
- Collection failure: Running pytest from the parent folder produced `ModuleNotFoundError: No module named 'models'` across all 3 test suites during collection.
- Duplicate cancellation failure: `test_duplicate_cancellation_is_idempotent_across_workloads` resulted in duplicate event records `['C', 'C']`.

## 3. What I tried
- Initially attempted using simple numeric checks like `isinstance(val, (int, float)) and val >= 0`. This failed because `True` passed the integer check.
- Attempted `try-except` blocks around arithmetic operations. While this caught strings, it still treated booleans as valid `1` and `0` values.
- Investigated the directory structure and discovered that `pyproject.toml` set `pythonpath = ["."]`, which only took effect when running directly inside the subfolder.

## 4. Resolution
- Created a dedicated helper `_is_valid_non_negative_number(val)` that explicitly checks `not isinstance(val, bool)` and guards against `math.isnan(val)` and `math.isinf(val)`.
- Implemented an early return in `process_cancellation` checking `if event_id in out['processed_cancellation_ids']: return out` before altering partner state.
- Added `tests/conftest.py` to dynamically insert the project root into `sys.path`, allowing tests to run reliably from any directory.

## 5. Proof and regression prevention
- Verified by `test_preparation_time_validation[True]` and `test_invalid_or_missing_travel_time_rejected[True-1]`.
- Added `test_regression_invalid_and_malformed_order_inputs` and `test_regression_cancellation_idempotency_multi_call` in `tests/test_regression.py` to prevent regression.

## 6. Unresolved challenge or next step
- Currently, travel times are stored in an in-memory dictionary. For a large-scale production deployment with thousands of zones, an external spatial index or cache (e.g. Redis with H3 spatial indexing) would be necessary to avoid in-memory memory bloat.
