# Project Notes

## Requirements completed

The following requirements have been addressed in the proposed `service.py` implementation during the development discussion. Runtime verification has not yet been reported, so these should be treated as implementation targets until confirmed against the repository tests.

1. **Input validation:** Validate order ID, restaurant ID, destination zone, and non-negative finite preparation/travel/workload/current-time values.
2. **Partner eligibility:** Consider active partners only, require available order capacity, and reject candidates missing either required travel-time entry.
3. **ETA calculation:** Calculate pickup as current time + partner-to-restaurant travel + remaining workload. Calculate ETA as pickup + preparation time + restaurant-to-customer travel.
4. **Deterministic selection:** Choose the lowest ETA; break ties by ascending lexicographic partner ID.
5. **Missing data and unassignment:** Never substitute missing travel data with zero. Return an unassigned result with an explanatory reason if no valid candidate remains.
6. **Cancellation idempotency:** Check processed cancellation event IDs before applying a cancellation so duplicate events do not release workload twice.
7. **Robustness:** Handle empty partner lists, malformed records, duplicate/unknown identifiers, and invalid or negative time values safely.

## Files changed

- `service.py` — the discussed implementation changes target `estimate_eta()`, `assign_order()`, and `process_cancellation()`.
- `models.py` — inspected to understand the order and partner dictionary shapes; no change has been established.
- `fixtures.py` — inspected to understand the sample order, partners, and travel-time mapping; no change has been established.
- `main.py` — inspected to understand how the sample inputs are passed to `assign_order()`; no change has been established.
- Documentation files — supporting project notes and submission documentation were drafted separately.

## Decisions and assumptions

- Preserve the existing service function names and broadly preserve the assignment result dictionary structure.
- Represent travel times using the existing tuple-key convention: `(origin, destination)`.
- Treat `active_order_ids` as the countable source for partner capacity usage.
- Treat `workload_minutes` as remaining partner workload and `minutes_by_order[order_id]` as the workload released when that order is cancelled.
- Treat `processed_cancellation_ids` as the record of cancellation events already applied.
- Reject missing travel entries rather than interpreting them as zero.
- Resolve equal ETA values by comparing partner IDs as strings in ascending lexicographic order.
- The `now` argument and all time quantities are assumed to use minutes, consistent with the starter code's field names.
- The implementation and these assumptions must be checked against the repository's actual tests and any additional project documentation.

## Tests and results

- No actual `pytest` output has been provided in the conversation.
- No test pass count, failure count, benchmark, or successful CI run is claimed.
- The supplied fixture values were inspected and the expected arithmetic can be calculated:
  - Partner `P-2`: pickup = `0 + 8 + 5 = 13`; ETA = `13 + 10 + 12 = 35`.
  - Partner `P-1`: pickup = `0 + 12 + 2 = 14`; ETA = `14 + 10 + 12 = 36`.
  - Based on the stated rules and supplied travel entries, `P-2` has the lower ETA.
- Run `python -m pytest -q` from the repository root and record the exact output here.
- Also run `python main.py` and record the actual printed result. Do not report the calculated fixture result as an observed execution result.

## Limitations and next steps

- Confirm which proposed `service.py` version is currently in the working tree; the conversation included multiple incremental versions.
- Run the complete test suite and add focused regression tests for missing travel legs, inactive/full partners, ETA ties, invalid times, empty/malformed inputs, and duplicate cancellation events.
- Review cancellation behavior when workload metadata is malformed. Event recording and workload release should not leave partner state partially updated.
- Verify whether the evaluator expects particular reason strings or exact result keys.
- Inspect `git diff` and `git status`, commit the verified changes, push the feature branch, and check the pull-request CI result.

