# AI-Use Declaration

- **Cline (VS Code Extension)**
  - **Purpose:** Used to inspect the initial 65 `pytest` failures, trace how `service.py` interacted with `models.py`, and draft the input validation helpers and cancellation logic.
  - **Independently verified or changed:** Ran `python -m pytest -q` and `python -m main` in the terminal to verify all 229 tests passed. Checked `git diff` to make sure only `service.py` was touched and no test files were modified. Manually tested edge cases like boolean inputs (`isinstance(x, bool)`), `NaN`/`inf` floats, and duplicate cancellation IDs.
  - **Displayed credits/tokens:** Not available.
  - **Suggestion accepted, changed, or rejected:** Rejected wrapping the ETA math in a `try...except TypeError` block because Python still allows arithmetic with booleans (`True + 1`) and negative numbers. Accepted writing explicit helper checks (`_is_valid_number`, `_is_valid_time`) and deep-copying the partner dict in `process_cancellation` so duplicate event IDs return early without mutating state.

- **Google Gemini**
  - **Purpose:** Used to clean up and format the rough notes in `approach.md` and this declaration.
  - **Independently verified or changed:** Checked all test counts (`65 failed, 164 passed` initially -> `229 passed` final), function names, and file paths against my actual terminal output and `git status`.
  - **Displayed credits/tokens:** Not available.
  - **Suggestion accepted, changed, or rejected:** Accepted removing a contradictory note in Section 5 of the initial draft that mentioned adding regression tests, since I only modified `service.py` and left the `tests/` folder untouched.