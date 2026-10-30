# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
Two real difficulties: (a) deciding the correct semantics for duplicate cancellation events when the dataset contains both duplicated `event_id`s AND events with no `event_id` at all, and (b) the test matrix deliberately leaves some inputs unconstrained (`active=1`, `"yes"`), forcing a defensible strictness decision rather than a test-driven one.

## 2. Evidence
- `data/records.json` holds 177 cancellation events: 170 carry `event_id` (9 IDs appear twice with identical payloads), 7 have **no** `event_id` key at all, and 41 reference orders not present in the partner's `active_order_ids` (e.g. `NO-SUCH-ORDER-0`). The edge-case catalog lists "duplicate cancellation event and duplicate event ID with differing payload".
- Starter code appended `event_id` to `processed_cancellation_ids` but never checked membership — the 15-workload matrix showed workload released twice per duplicated event.
- `test_inactive_partners_never_selected` parametrizes `active` over `[False, True, 0, 1, None, "no", "yes"]` but only asserts for falsy values and literal `True`; truthy non-`True` values are unconstrained.

## 3. What I tried
- Replayed all 177 dataset events through the fixed `process_cancellation` and asserted whole-stream idempotency (`once == twice` on a second replay): passes under per-partner `event_id` dedup.
- Considered deduping ID-less events by `order_id` fallback instead of `None`. Rejected: it complicates the invariant and whole-stream replay then re-appends IDs, breaking fixed-point idempotency. Keeping `None` as the dedup key is simpler and conservative.
- For the `active` ambiguity, chose `partner.get('active') is True` (strict bool) because the problem statement requires validating record structures rather than coercing invalid values; the dataset only contains real booleans, so this cannot regress real data.
- Verified the duplicate-event-with-different-payload scenario directly: event `C1` cancels `O1`, a replayed `C1` claiming `O2` must NOT release `O2` — covered by `test_duplicate_event_id_with_different_order_still_ignored`.

## 4. Resolution
- Root cause of the cancellation defect: the starter recorded IDs for audit but never used them as a guard. Fix: return the deep-copied record unchanged when `event_id in processed_cancellation_ids`, before touching `active_order_ids`/`workload_minutes`.
- Strictness ambiguity resolved by treating non-conforming values as malformed input (reject), consistent with "do not silently convert invalid data into valid-looking values".

## 5. Proof and regression prevention
- `test_duplicate_cancellation_is_idempotent_across_workloads` (15 cases), `test_duplicate_cancellation_is_idempotent`, `test_duplicate_event_id_with_different_order_still_ignored`, `test_full_cancellation_stream_replay_is_idempotent` (dataset replay) and `test_duplicate_event_ids_in_dataset_do_not_double_release` all pass: 274 total.
- Related case that could still break: if a future spec allows multiple distinct ID-less cancellation events per partner, the `None`-dedup assumption must be revisited.

## 6. Unresolved challenge or next step
- Remaining limitation: cancellations without `event_id` are deduplicated as a group per partner, so a second genuinely-different ID-less event on the same partner is ignored. The dataset's ID-less events are duplicates, so the conservative choice is correct for this data. If the spec changed, I would dedup ID-less events by `(order_id)` fallback and re-run the dataset replay test.
