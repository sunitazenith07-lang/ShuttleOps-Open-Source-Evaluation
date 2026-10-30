# AI-Use Declaration

### 1. Tools and Sources Used
- **Tool / Assistant:** Antigravity AI Assistant & Official Python Documentation (docs.python.org).
- **Purpose:** 
  - I used the assistant as a learning aid to understand confusing Python edge cases, especially why `isinstance(True, int)` evaluates to `True` in Python (since `bool` inherits from `int`).
  - I also asked about pytest parametrization syntax (`@pytest.mark.parametrize`) to see how the existing tests were structured.
- **Credits / Tokens:** Standard student environment / Not available.

### 2. Independent Verification & What I Changed
- I did not copy-paste code blindly. Every change in `service.py` was tested locally by running `python -m pytest -q` in PowerShell.
- I manually traced the ETA calculation on paper for sample order `O-7` (now=0, leg1=8, workload=5, prep=10, leg2=12) to verify `pickup = 13` and `eta = 35`.
- I wrote the 71 regression tests in `tests/test_regressions.py` myself to specifically check each edge case that failed initially (negative numbers, string inputs, booleans, capacity boundaries, and duplicate cancellations).

### 3. Suggestions Evaluated (Accepted / Rejected)
- **Rejected Suggestion:** An early suggestion was to replace the plain dictionary structures with Pydantic models or custom classes. I rejected this because the project requirements and existing tests (`test_contract.py`, `test_acceptance_matrix.py`) pass plain Python dictionaries, and rewriting the models would have broken existing starter code.
- **Accepted Suggestion:** Using `isinstance(value, bool)` check *before* `isinstance(value, (int, float))` when validating numbers. In Python, `bool` is a subclass of `int`, so `True` would pass a basic `isinstance(..., int)` check unless explicitly rejected first.

### 4. Integrity Statement
All final code and explanations are my own work. I understand how every helper function works and I am ready to explain the logic and walk through any test during the viva.
