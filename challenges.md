# Challenges and debugging

These are issues observed during the Codex-assisted implementation. They are not presented as problems independently discovered or solved by the student. See the work record in approach.md.

## Sorting out the initial failures

The baseline had 65 failures, but that did not mean 65 separate bugs. Several parameterized cases tested the same missing rule with different inputs. For example, negative travel time, a string travel time and a boolean travel time all showed that duration validation was missing.

Codex read the original assertions and grouped the failures around validation, eligibility and cancellation. After those changes, all 229 original tests passed without altering their assertions. This gave a useful starting point for extra tests, but was not treated as proof that the service was finished.

## Duplicate cancellation events

The starter recorded event IDs but did not use the history to reject a replay. Even when the order was already gone, processing the same event appended its ID again.

The fix checks `event_id` before changing order or workload state. A stronger regression cancels A with event E, then attempts to cancel B with the same event. B must remain assigned. This is checked by `test_cancellation_replay_cannot_cancel_a_different_order` in `tests/test_regressions.py`.

## Numeric overflow during cancellation

The stress test used a workload of `10**400` and released minutes of `0.5`, and also tested the reverse combination. Both values passed the duration check individually, but subtracting a float from such a large integer raised `OverflowError`.

The failing output pointed to `workload - released`. The earlier code removed the order before doing that calculation on the copied state. The revised code calculates the remaining workload first and catches overflow. If the calculation cannot be represented, it returns the unchanged copy and does not record the event as processed.

Both reproductions are kept in `test_cancellation_numeric_overflow_is_atomic` in `tests/test_stress.py`. Returning unchanged state is safe for accounting, but the caller does not receive a separate error message. A structured cancellation result would make that limitation clearer.

## A tie that depended on input order

Two records with the same partner ID had pickup times of 1 and 2. With preparation time `1e20`, floating-point rounding made both final ETAs equal. Comparing only ETA and partner ID therefore returned whichever record appeared first, including its different pickup time.

The fix uses pickup time as a final comparison after ETA and partner ID. It does not change the required partner-ID rule for distinct IDs. `test_duplicate_partner_ids_have_deterministic_result` checks that reversing the records gives the same complete result.

## A mistake in an added test

One new malformed-input test incorrectly expected the selected ID to be only `P` or `None`. Its inputs included the string `"7"`, which is a valid identifier under the implemented rule. That failure came from the new assertion, not the service. The test was corrected to compare a selected ID with the supplied partner ID. No original test was weakened.

## Ambiguity review: reproduction, fix and verification

**Observed problem:** A requirements review showed that cancelling OLD-1 from the actual fixture removed the order but left 5 workload minutes behind. The fixture has no per-order entry for OLD-1, and cancellation previously treated that missing entry as zero. Missing total workload or active-order lists also received defaults that could allow an incomplete record to be processed.

**Evidence before the fix:** Eight new regression cases were run before the fix: seven failed and the explicit-zero case passed. The fix removes these accounting defaults. Missing or invalid accounting leaves the partner unchanged and does not consume the event ID. A retry test fills in the missing 5 minutes and submits the same event again; the order is then removed, workload becomes zero, and the event is recorded once. Explicitly recorded zero minutes remain valid.

**Duplicate-order decision:** The review also showed that an already-active order could be assigned again. Assignment now checks the supplied partners' active-order lists before selection and returns `order is already active` when it finds a match. Tests cover both an active and an inactive existing partner, because an inactive partner can still hold an order.

**Verification:** These cases are in `tests/test_accounting.py`. After the changes, all eight passed and the full suite passed 352 tests. The later full-suite rerun reported 352 passed in 0.83s. This is a guard against duplicate orders visible in the supplied state, not a reservation system. Two separate calls with stale state can still make the same recommendation.

## What remains

The final local suite passed all 352 tests. This does not prove correctness for arbitrary inputs or an external production system. Missing accounting now prevents cancellation instead of being treated as zero. Malformed cancellation state still returns unchanged without an explicit error result. Assignment remains a recommendation and does not reserve capacity. Those API limits need consideration before extending the service.
