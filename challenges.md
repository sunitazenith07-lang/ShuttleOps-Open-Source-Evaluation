# Challenges and evidence

## 1. Challenge or confusing behaviour
The most important edge case was distinguishing an actually missing route from a route whose value is invalid. The starter checked only for `None`, so negative, string, Boolean and non-finite travel values could reach the ETA calculation. Partner eligibility and cancellation-event deduplication were also absent.

## 2. Evidence
The initial visible suite reported **65 failed, 164 passed**. Failures included `test_invalid_or_missing_travel_time_rejected`, `test_inactive_partners_never_selected`, `test_capacity_boundary_matrix` and `test_duplicate_cancellation_is_idempotent_across_workloads`.

## 3. What I tried
- Read the task's required behavior and the failing assertions before changing the service.
- Ran `python -m pytest -q`; this environment had no `python` command, so I used `python3`.
- Ran the baseline suite with `python3 -m pytest -q --tb=no` to capture a concise failure summary, and ran the offline demo.
- After the changes, reran the full suite and the demo; I also ran a full-capacity/missing-route example.

## 4. Resolution
Added shared checks for non-empty string identifiers and non-negative finite numeric times. Dispatch now filters inactive and full partners before estimating an ETA. Cancellation processing now checks the processed-event list before releasing workload and preserves the caller's original partner object by working on a deep copy.

## 5. Proof and regression prevention
The final suite passed: **235 passed**. Existing matrix/contract tests cover invalid time values, capacity, tie-breaking and repeated cancellations. `tests/test_regressions.py` adds malformed-record, overflow and input-immutability cases.

## 6. Unresolved challenge or next step
Cancellation deduplication is stored in each partner record, so it depends on that state being persisted by the caller between events. This repository has no persistence layer to test. The cancellation handler raises an explicit error if its state-list shape is malformed; a production integration should define how such corrupt persisted state is surfaced and repaired.