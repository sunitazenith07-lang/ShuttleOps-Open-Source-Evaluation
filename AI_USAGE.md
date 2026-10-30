# AI-Use Declaration

## Tool / Model Information
- **Tool / Model:** Antigravity / Gemini 3.8 Flash
- **Purpose:** Assisting in repository exploration, tracing test failures in `tests/test_acceptance_matrix.py`, drafting regression tests in `tests/test_regression.py`, and compiling comprehensive documentation for submission files.
- **Independent Verification:**
  - Independently executed baseline tests using `python3 -m pytest -q` and recorded the exact output (`65 failed, 164 passed in 0.39s`).
  - Traced root causes of Python's boolean subclassing behavior where `isinstance(True, int)` caused invalid times and capacities to be accepted as valid.
  - Formulated dedicated validation helper functions (`_is_valid_non_negative_number` and `_is_valid_string_id`) and verified each edge case against the entire parameter space.
  - Ran local benchmarks on macOS with Python 3.14 to measure dispatch latency (43.34 µs/order across 9,000 iterations).
- **Displayed Credits / Tokens:** Not available
- **Suggestions Evaluated:**
  - *Suggestion accepted:* Centralizing type checking into `_is_valid_non_negative_number` with `math.isfinite` to handle `NaN`, `Inf`, and `bool` in a single unified helper.
  - *Suggestion rejected:* Modifying partner records in-place during dispatch was rejected to preserve pure functional semantics and avoid caller state side-effects.

