# Optimizations and trade-offs

## 1. Baseline and objective

The starter failed 65 of 229 tests. Correct eligibility, safe inputs and one-time
cancellation were the objectives. No performance benchmark was performed; test
elapsed times are not evidence of a speedup.

## 2. Options considered

| Option | Expected benefit | Correctness/maintenance implications | Decision |
|---|---|---|---|
| Shared validation | Consistent time/ID rules | Small helpers preserve zero/fractions and prevent unsafe arithmetic | Implemented |
| Existing min over candidates | Simple deterministic linear selection | Stores eligible estimates but is easy to inspect | Retained |
| Sort all candidates | Ordered candidate list | Same winner, unnecessary O(p log p) work | Rejected |
| Running best candidate | O(1) candidate storage | More bookkeeping; no measured need for 60 partners | Deferred |
| Cache ETAs/routes | Less repeated batch work | Workload, time, prep/routes change; stale caches risk wrong assignments | Deferred |
| Persistent cancellation-ID set | Faster history lookup | Changes the JSON-friendly list contract and storage assumptions | Deferred |

## 3. Improvements actually implemented

Validation precedes arithmetic and route-key construction. Cancellation rejects
replayed IDs before releasing work, and removes a cancelled order's stale minutes
entry. These improve correctness/clarity; no speed claim is made.
Original matrices and new safety/dataset regressions protect the changes.
The initial submission suite passed 469 tests. No runtime dependency was added.

## 4. Improvements investigated but rejected or deferred

The options above were reviewed against the code/contract, not implemented as
benchmark prototypes. The dataset has 60 partners and 387 unique route keys;
there is no evidence that caching or a storage redesign would help this task.

With p partners and at most a active IDs each, unique-ID validation costs O(p*a),
minimum selection O(p), and candidate storage O(p), with temporary O(a) sets.
Cancellation copies the partner and scans its lists, so work/memory are linear
in partner state size. Copying protects caller-owned input. Repeated order checks
keep direct estimates safe; a trusted internal path to avoid them was unnecessary.

## 5. Potential future improvements

If measured batch use justifies it, benchmark a running minimum and validated
order context. Require identical winners, ETAs, rejection behaviour and unchanged
inputs. Durable/global event tracking needs explicit retention, ownership and
atomic-update rules first. These are future ideas, not implemented features.

## 6. Optional report trade-off

Implemented a separate `explain_assignment` wrapper. Ordinary assignments perform
exactly the same work as before; reports intentionally call assignment and then
estimate candidates again. This small extra pass reuses the validated rules and
protects the existing return contract. Report rows require O(p) additional space,
and the second validation pass has the same O(p*a) bound as normal estimation.

An opt-in flag on `assign_order` or refactoring both paths into one new engine
could avoid repeated work, but would change the existing function or its control
flow. That compatibility risk was unnecessary for the supplied 60 partners.
No timing benchmark or speedup is claimed. The final 500 passing cases include
unchanged assignment fields for all 180 dataset orders. Only the candidate-report
stretch feature was added; batching and preparation-change recalculation remain
outside this submission.
