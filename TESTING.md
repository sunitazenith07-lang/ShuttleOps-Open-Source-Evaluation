# TESTING.md — Required submission

## Test command and environment
- **Python version:** 3.13.5
- **Command run:** `python main.py` and manual Python edge-case checks.
- **Actual test summary:** 7 out of 8 manual checks passed. One issue was identified with unknown cancellation events.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Empty partner list | Order remains unassigned without errors. | Passed | Empty partner list |
| 2 | Inactive partner | Inactive partner is excluded from assignment. | Passed | Inactive partner excluded |
| 3 | Partner at full capacity | Partner is excluded from assignment. | Passed | Full capacity excluded |
| 4 | Missing travel-time data | Candidate is rejected; missing data is not treated as zero. | Passed | Missing travel data rejected |
| 5 | Negative preparation time | Invalid time is rejected. | Passed | Negative prep time rejected |
| 6 | Equal ETA for two partners | Partner with the lower ID is selected. | Passed | ETA tie broken by ascending partner ID |
| 7 | Duplicate cancellation event | Workload is deducted only once. | Passed | Duplicate cancellation deducted once |
| 8 | Unknown order cancellation | Unknown cancellation should not be processed. | Failed | Unknown cancellation event is recorded |

## Regression tests added

Manual checks were performed for empty partner lists, inactive and full-capacity partners, missing travel data, negative times, ETA tie-breaking, and duplicate cancellation events.

No permanent automated regression test cases have been added yet.

## Remaining failures or limitations

- Unknown order cancellation events are currently added to `processed_cancellation_ids`, even when the order does not exist in the partner's active orders.
- Automated regression tests still need to be added.
- Additional malformed-record and invalid-ID combinations require testing.