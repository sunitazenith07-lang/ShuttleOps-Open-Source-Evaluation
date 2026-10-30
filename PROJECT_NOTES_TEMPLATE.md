# Project notes

## Requirements completed

The dispatch code checks order details and time values, skips inactive or full partners, and requires both travel-time legs before it calculates an ETA. When more than one partner is eligible, it chooses the lowest ETA and uses the partner ID to break a tie. Cancellation events with an ID are only applied once.

## Files changed

The implementation and regression tests are in `service.py` and `tests/test_regression.py`. The partner and order helper functions are in `models.py`. The project also has supporting notes in `approach.md`, `TESTING.md`, and `DISPATCH_NOTES.md`. Update this list if your final submission changes a different set of files.

## Decisions and assumptions

- A time must be a finite, non-negative number. Booleans and text are not treated as times.
- A partner is available only when `active` is exactly `True` and the number of active orders is below capacity.
- Missing travel-time information means there is not enough information to estimate an ETA, so the partner is skipped.
- Ties are broken by partner ID in alphabetical order. For example, `P10` comes before `P2`.
- A cancellation needs an event ID so repeated delivery of the same event can be recognized.

## Tests and results

`TESTING.md` records a baseline of 65 failures and 164 passes before the fixes, and a final run of 443 passing tests. It also lists edge cases and regression tests. These are the results already recorded in that file; rerun the command and update this section if your current code has changed since then.

## Limitations and next steps

The assignment function returns the selected partner but does not update that partner's active orders or workload. A caller would need to update the partner before assigning another order. The current rules also do not check an order's status. A useful next step would be to decide how those behaviors should work, add tests for the decision, and then implement them.
