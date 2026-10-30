# challenges.md - COMPULSORY submission


## 1. Challenge or confusing behaviour
The most challenging part was handling Python's subtle type behavior during input validation—specifically, how boolean values (`True`/`False`) behave as subclasses of integers (`int`) and how missing parameters like `capacity = None` or invalid strings caused unexpected runtime errors instead of safely failing.

## 2. Evidence
When running the initial test suite (`python -m pytest -q`), tests such as `test_preparation_time_validation[True]` and `test_current_time_validation[True]` failed because `isinstance(True, int)` evaluates to `True` in Python. Additionally, capacity boundaries like `None` threw a `TypeError: '>=' not supported between instances of 'int' and 'NoneType'` when comparing active orders against partner capacity.

## 3. What I tried
- **Experiment 1:** Initially, I used a basic type check: `isinstance(value, (int, float))`. This failed the boolean test cases because `True` and `False` passed the check and were incorrectly treated as numeric time values (`1` and `0` minutes).
- **Experiment 2:** I tried adding try-except blocks around arithmetic operations (`+`), but that only caught exceptions rather than validating boundaries or correctly rejecting invalid types according to the strict test matrix expectations.

## 4. Resolution
The root cause was two-fold: lack of explicit boolean rejection and unsafe comparisons with unvalidated `None` values. 
- **What I changed:** I implemented a dedicated helper function `is_valid_time(value)` that explicitly checks `if isinstance(value, bool): return False` before validating integer/float ranges, NaNs, infinities, and negative numbers. I also added strict type validation for partner capacity (`isinstance(capacity, int) and capacity >= 1`).
- **Why it addressed the root cause:** This prevented invalid types from entering arithmetic expressions or comparison operators at their source, rather than just masking the symptoms.

## 5. Proof and regression prevention
- **Demonstrating test(s):** The test matrix in `tests/test_acceptance_matrix.py` (specifically `test_preparation_time_validation`, `test_current_time_validation`, and `test_capacity_boundary_matrix`) directly demonstrates that these edge cases are now fully handled.
- **Test summary proof:** Running `python -m pytest -q` now successfully passes all tests (`229 passed in 0.46s`).
- **Related edge case:** Extreme float values or very large integers could theoretically cause overflow, though mitigated here by finite checks and standard Python arbitrary-precision integers.

## 6. Unresolved challenge or next step
There are no major unresolved blockers remaining as the entire acceptance test suite passes successfully. As a next step if scaling up, I would consider performance optimization (such as caching travel matrix lookups) if the partner and route dataset grows significantly larger.