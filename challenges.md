# challenges.md — implementation notes

## 1. Challenge or confusing behaviour
The most important issue was that a candidate could have a mathematically calculable ETA but still be unavailable: `assign_order` did not inspect the partner's active status or order capacity. Malformed time values also reached arithmetic directly.

## 2. Evidence
The untouched suite reported **65 failed, 164 passed**. Failures included inactive and full partners being assigned, negative preparation time being accepted, and cancellation event IDs appearing twice after replay. The acceptance matrix also covered strings, booleans, `NaN`, and infinity as invalid time values.

## 3. What I tried
- Read the problem statement, service, models, fixtures, demo, all visible tests, and data schema notes.
- Ran the baseline suite and demo before editing.
- Compared each failing acceptance case to the branch in `estimate_eta`, `assign_order`, or `process_cancellation`.
- Added regression cases for invalid workload, malformed order/partner collection, reason clarity, repeated event IDs, and duplicate active-order entries.

## 4. Resolution
I kept the public functions and dictionary-based data structures, then added input checks before time arithmetic and partner selection. Cancellation now checks the processed-event list before changing active orders or workload. These changes address the decision points that caused the failures rather than special-casing test inputs.

## 5. Proof and regression prevention
The final `.venv/bin/python -m pytest -q` run reported **239 passed**. The baseline tests continue to exercise the ETA formula, missing travel, capacity, active status, tie-breaking, and duplicate cancellations. The new regression file covers additional malformed-input and event-reuse cases.

## 6. Unresolved challenge or next step
Local validation used Python 3.14.7 while GitHub Actions specifies Python 3.11.The code uses standard-library features, but compatibility with Python 3.11 should still be verified through the repository's CI workflow before submission. No performance measurements were made because the task is focused on correctness and the dataset is small.
