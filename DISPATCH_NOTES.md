# Dispatch notes

AI-assisted engineering record; not a claim of independently authored student work.

## Worked ETA
Verified by test_worked_eta_and_inputs_remain_unchanged:
order O, restaurant R, destination D; partner P at Z; current time 3 minutes;
Z-to-R travel 8; workload 5; preparation 10; R-to-D travel 12.
Pickup = 3 + 8 + 5 = **16**. ETA = 16 + 10 + 12 = **38**.
Actual pickup 16 and ETA 38. Inputs remain unchanged.
The offline fixture at now=0 selects P-2 with pickup 13 and ETA 35.

## No eligible partner
Verified by test_full_partner_and_missing_route_leave_order_unassigned:
A has capacity 1 and one active order, so is full. B has spare capacity but zone UNKNOWN
has no travel entry to R. The R-to-D entry exists, but one route is insufficient.
Actual result: partner_id=None, pickup_minutes=None, eta_minutes=None and a nonempty
reason mentioning eligibility, capacity and required travel data.

## Edge cases
1. Equal ETA: P10 precedes P2 lexicographically regardless of input ordering.
   Duplicate partner IDs are excluded as ambiguous. Regression verifies both.
2. Cancel A with C1, then replay C1 for B: B stays active and workload is not reduced twice.
   Cancelling A again with C2 also changes nothing; the order is no longer active.
3. Missing route is unknown rather than zero; genuine zero-valued travel is valid.
   Existing formula and missing-route matrices pass.
4. Cancelling an order whose minutes exceed aggregate workload clamps workload to zero;
   existing boundary tests pass. Negative per-order minutes are rejected.

## Assumptions
Nonempty string identifiers, exact boolean active=True, positive integer capacity.
Times are finite nonnegative int/float values; booleans are rejected. All units are minutes.
Preparation is added after pickup as explicitly required, without overlapping waiting time.
Assignment is a pure recommendation: callers must reserve capacity before another dispatch.
Cancellation event IDs are scoped per partner. Unknown orders and malformed events/state
are no-ops; successful cancellations remove both active ID and minutes ledger entry.
Missing per-order minutes release capacity without inventing a workload deduction.
No stretch item, persistence or global partner/order catalog was added.
