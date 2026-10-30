# Project Notes

## Requirements completed
All seven required behaviours in `STUDENT_PROBLEM_STATEMENT.md` are implemented and covered by tests:

1. **Input validation.** `order_id`, `restaurant_id` and `destination_zone` must be non-empty strings. `prep_minutes`, travel times, workload and `now` must be finite, non-negative numbers. Bools, NaN, infinity and ints too large for a float are rejected.
2. **Eligibility.** Only partners with `active is True` and fewer active orders than an integer `capacity` (≥ 1) are considered. A partner missing either travel leg gets no ETA.
3. **ETA formula.**
   - `pickup = now + partner_to_restaurant + workload`
   - `eta = pickup + prep + restaurant_to_customer`
4. **Selection.** The lowest ETA wins; exact ties go to the partner ID that comes first in ascending lexicographic order.
5. **Missing data.** Missing travel data is never treated as zero. If no partner is valid, the order stays unassigned, and `reason` lists each rejection cause with a count.
6. **Cancellation idempotency.** A cancellation event is applied only once per `event_id`, so a duplicate cannot release workload or capacity twice.
7. **Determinism and safety.** Results are the same regardless of input order. Empty lists, unknown IDs, malformed records and negative or extreme values are handled without crashing.

Other deliverables:
- The JSON travel rows are converted into the `(from, to)` tuple-key map (`tests/test_dataset.py`).
- Regression tests were added for every fix.
- `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md` and `DISPATCH_NOTES.md` are complete.

**Stretch feature (one chosen):** `explain_assignment` returns the normal assignment result plus a per-partner verdict, showing either the ETA or the rejection reason.

## Files changed
| File | Change |
|---|---|
| `service.py` | Implemented validation helpers (`_is_valid_time`, `_is_valid_id`, `_order_problem`, `_partner_problem`), the ETA checks in `estimate_eta`, candidate evaluation (`_evaluations`, `evaluate_candidates`), selection in `assign_order`, `explain_assignment`, and idempotent `process_cancellation`. |
| `tests/test_regression.py` | New: 54 regression and edge-case tests. |
| `tests/test_dataset.py` | New: 5 tests replaying `data/records.json` (180 orders, 177 cancellations). |
| `README.md` | Project introduction added above the original evaluation instructions, which are preserved. |
| `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `DISPATCH_NOTES.md` | Required documentation completed. |
| `VIVA_PREPARATION.md` | New: implementation walkthrough, viva questions and live-change exercises. |
| `AI_USAGE_TEMPLATE.md`, `PROJECT_NOTES_TEMPLATE.md` | Completed. |

Not changed: the original tests, `models.py`, `fixtures.py`, `main.py`, the dataset, configuration, CI workflows and the problem statement.

## Decisions and assumptions
- **Validation returns results, it does not raise.** Invalid input produces `eligible: False` or `partner_id: None` with a reason, because the tests expect results rather than exceptions.
- **Strict records.** `active` must be literally `True`, and `capacity` must be an `int` ≥ 1 (bool, 0, negative and float are rejected). Missing `active_order_ids` / `workload_minutes` default to `[]` / `0`; present but malformed values reject the partner.
- **No silent repair.** Invalid data is never converted into valid-looking values:
  - A malformed `workload_minutes` is preserved during cancellation.
  - A malformed `active_order_ids` or `processed_cancellation_ids` makes the cancellation a no-op. Overwriting it could erase real orders or the event history.
- **ETA range check.** The computed ETA must itself be finite. If valid inputs overflow to `inf`, the partner is rejected with `'ETA out of range'`.
- **One result schema.** Every `assign_order` result has the same five keys: `order_id`, `partner_id`, `pickup_minutes`, `eta_minutes`, `reason`. Unassigned results use `None` for the partner, pickup and ETA values.
- **Copy, don't mutate.** `process_cancellation` works on a deep copy, so the caller's record is never modified.
- **Events without an ID.** Cancellations that have no `event_id` are deduplicated per partner, so only the first one applies.
- **Time model.** All times are minutes on one clock. `eta_minutes` is an absolute time; the delivery duration is `eta_minutes - now`.

## Tests and results
- **Baseline (untouched starter):** `python -m pytest -q` gave 65 failed, 164 passed (229 tests).
- **Final:** 288 passed, 0 failed, 0 skipped, 0 warnings (Python 3.14.3, pytest 9.1.1).
  - The 229 original tests are unmodified.
  - 59 tests were added: 54 regression and 5 dataset.
- **Demo:** `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- **Dataset replay:** 180 orders → 170 assigned, 10 unassigned, with 0 mismatches against an independent checker.
- **Cancellation replay:** 177 events, 0 accounting mismatches, no negative workloads. Replaying the stream a second time leaves the state unchanged.
- **Determinism:** shuffling the partners and travel rows gives identical results.
- **Hostile inputs:** probes produced 0 crashes.
- Full evidence and 17 documented edge cases: [TESTING.md](TESTING.md).

## Limitations and next steps
- **Static snapshot.** There is no re-optimisation after an assignment, and travel times come from a fixed table.
- **Aggregate workload.** `workload_minutes` is one number, not a schedule.
- **Events without an ID.** A second, genuinely different cancellation without an `event_id` on the same partner would be ignored. If the specification required those events, the next step would be to deduplicate them by `order_id` and re-run the dataset replay.
- **Dataset quirk.** 10 partners in `records.json` start above their capacity. The engine never assigns to them, but it does not correct the source data.
- **Two passes in `explain_assignment`.** It evaluates the partners twice, which was an accepted trade-off for readability.
- **Scaling.** For much larger data, index partners by zone and use sets for order and event lookups, then benchmark before and after with `timeit`.
- **CI.** The GitHub Actions result will be checked once the pull request is opened.
