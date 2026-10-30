# Contribution Guide & Student Workflow

This document explains how to contribute to the SmartDispatch project and outlines the workflow I followed as a student contributor.

---

## 1. Contribution Workflow

When working on bug fixes or new features in this codebase:

1. **Read the Brief First**: Always read `STUDENT_PROBLEM_STATEMENT.md` and `STUDENT_START_HERE.md` to understand what business logic is expected.
2. **Set Up the Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. **Run the Baseline Tests**:
   Before modifying any code, run `python -m pytest -q` to see what is currently working and what is failing. Never delete or skip tests to make them pass.
4. **Make Minimal, Clean Changes**:
   Keep edits focused on the core logic in `service.py`. Do not hardcode fixture values or alter the data models unnecessarily.
5. **Add Regression Tests**:
   For every bug fixed, add test cases in `tests/test_regressions.py` to make sure the defect can never return.
6. **Verify the Entire Suite**:
   Run `python -m pytest -q` and `python -m main` to ensure 100% pass rate with zero regressions.
7. **Document Everything**:
   Complete all required Markdown documents (`approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, and `DISPATCH_NOTES.md`).

---

## 2. Student Contribution Checklist (How I Followed This)

Here is how I verified my work before submission:

- [x] Cloned the repository and installed dependencies with `requirements-dev.txt`.
- [x] Ran untouched tests: recorded baseline of 65 failures / 164 passes.
- [x] Fixed all 7 core defects in `service.py`:
  - Route travel time validation (rejecting negative, string, bool, NaN, inf values).
  - Preparation time and `now` parameter validation.
  - Required order field checks (`order_id`, `restaurant_id`, `destination_zone`).
  - Active partner status check (`partner['active'] is True`).
  - Capacity boundary checks (`len(active_order_ids) < capacity`).
  - Deterministic tie-breaking (by `partner_id` in alphabetical order).
  - Cancellation idempotency (ignoring duplicate `event_id` occurrences).
- [x] Added 71 new regression tests in `tests/test_regressions.py`.
- [x] Final test run: **300 passed / 0 failed in 0.19s**.
- [x] Completed all documentation templates with genuine evidence and student reflections.
- [x] Checked git diff to ensure no secrets or unnecessary files are included.

---

## 3. Code Standards & Integrity

- **Preserve Documentation & Comments**: Keep existing comments intact unless directly related to bug fixes.
- **Pure Functions**: Avoid mutating shared objects directly in helper functions.
- **Deterministic Output**: Always guarantee stable output order for identical ETAs.
- **No AI-Generated Cheating**: Use tools only for learning Python syntax and verifying concepts. All logic, test runs, and problem-solving must be independently understood and explained during viva.
