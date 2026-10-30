# Dispatch notes

## 1. Worked ETA example

Validated demo: order O-7, restaurant R-2, destination Z-9, preparation 10 minutes,
current time 0. Both candidates are active and below capacity two.

| Partner | Travel to restaurant | Workload | Pickup | Travel to customer | ETA |
|---|---:|---:|---:|---:|---:|
| P-2 (one active order) | 8 | 5 | 0 + 8 + 5 = 13 | 12 | 13 + 10 + 12 = 35 |
| P-1 (no active orders) | 12 | 2 | 0 + 12 + 2 = 14 | 12 | 14 + 10 + 12 = 36 |

P-2 wins because 35 < 36. Earlier ID only matters when ETAs tie.
Actual `python -m main` output before and after the fix:

```text
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

`test_demo_calculation_and_inputs_are_unchanged` asserts this output and unchanged
inputs. Times are minutes on the supplied clock. Workload, travel and preparation
are added as required; preparation does not overlap travel in this model.

## 2. No-eligible-partner example

`test_no_eligible_partner_example` uses order O/R/D, preparation 10, Z -> R = 1,
and R -> D = 2. Candidates and actual direct-estimate reasons:

| Partner | State | Rejection reason |
|---|---|---|
| A | Inactive | `inactive partner` |
| B | One active order, capacity one | `partner at capacity` |
| C | Zone UNKNOWN lacks its route to R | `missing travel time` |

Actual assignment, asserted by the passing regression:

```text
{'order_id': 'O', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
```

The general reason preserves the original contract. `estimate_eta` explains a
specific candidate's rejection. Unknown travel is never replaced by zero.

## 3. Meaningful edge cases

| Input | Expected and actual verified result | Test |
|---|---|---|
| All times zero | Eligible; pickup 0, ETA 0 | Original `test_eta_calculation_matrix` |
| Equal routes, P-1/P-10/P-2 in every permutation | P-1 wins lexicographically | `test_lexicographic_tie_is_independent_of_every_input_permutation` |
| Negative, string, boolean, NaN or infinite time | Ineligible; ETA None | Original time matrices and new workload regressions |
| Cancel A (4) with C, then try B (6) with C | B remains and workload stays 6 | `test_same_event_with_different_payload_is_ignored` |
| Valid unknown-order cancellation | No release; remember event once | `test_unknown_order_records_event_once_without_releasing_work` |

## 4. Assumptions and limitations

IDs are non-blank strings. Only boolean True is active. Capacity is a positive
integer, and active-order count must be lower. Finite non-negative integers and
fractions are accepted as minutes; booleans are rejected. Missing workload and
active-order lists default to zero/empty as in the starter.

Assignment returns a decision without reserving capacity; callers must update
state before the next assignment. Priority/status scheduling is outside the seven
core rules. Dataset orders are tested independently against a partner snapshot.
No restaurant registry exists: unknown IDs without required routes are unassignable.

Cancellation returns a deep copy, removes a present order's minutes entry and
floors remaining workload at zero. Invalid events/state leave it unchanged;
missing per-order minutes are not guessed. History is partner-local and must be
retained by the caller. Persistence/concurrent reservations are not implemented.
Human independent review/explanation remains necessary; see `AI_USAGE.md`.

## 5. Optional complete candidate report

Use the report only when its explanations are needed:

```python
from fixtures import sample_inputs
from service import explain_assignment
order, partners, travel = sample_inputs()
report = explain_assignment(order, partners, travel)
```

The validated demo report keeps the assignment P-2/pickup 13/ETA 35 and adds:

| Candidate index | Partner | Eligible | Selected | ETA | Reason |
|---|---|---|---|---|---|
| 0 | P-2 | True | True | 35 | selected by ETA and partner ID |
| 1 | P-1 | True | False | 36 | higher ETA than selected partner |

Rejected rows retain the specific `estimate_eta` reason. Equal ETA losers report
that an earlier partner ID won. Identical ID/ETA duplicate rows select only the
first supplied row; later duplicates say an earlier candidate was selected.
`candidate_index` is zero-based and follows input order, including malformed rows.
An empty or invalid partner collection produces an empty candidate list and the
original assignment-level reason. No partner is selected when all are rejected.

`test_explanation_preserves_every_dataset_assignment` checks report compatibility
on all 180 orders. Default `assign_order` still returns exactly its original fields;
no candidate list is added unless this separate function is called. Neither
function reserves capacity. Reports use a stable caller-supplied snapshot and do
not provide a concurrent or durable dispatch transaction.
