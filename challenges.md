# challenges.md - COMPULSORY submission

The hardest behaviour to reason about was partner eligibility during order assignment. A partner can have a valid route and a low ETA but still should not be selected if the partner is inactive or already at capacity. The starter implementation checks whether an ETA can be calculated, but it does not apply those availability checks.



## 1. Challenge or confusing behaviour
A  important edge case was duplicate cancellation delivery, processing the same cancellation event more than once must not release workload repeatedly or record the same event multiple times.

## 2. Evidence  
1) In service.py, assign_order adds a candidate whenever estimate_eta returns eligible=True. The starter code does not check the partner's active flag or compare the number of active orders with capacity.
2) The acceptance tests test_inactive_partners_never_selected and test_capacity_boundary_matrix cover inactive partners and full-capacity partners. The initial test run reported failures in the supplied suite.
3) In process_cancellation, the starter code appends event_id to processed_cancellation_ids without first checking whether it was already processed.
4) test_duplicate_cancellation_is_idempotent_across_workloads applies cancellation event C twice and expects the processed-event list to remain ['C'].
5) The baseline demo printed an assignment for partner P-2 with pickup time 13 minutes and ETA 35 minutes. This confirms the simple demo path runs, but does not establish that inactive or full partners are filtered correctly.

## 3. What I tried
1) Inspected assign_order, estimate_eta and process_cancellation in service.py to trace candidate selection, ETA calculation and cancellation handling respectively.
2) Inspected new_partner and new_order in models.py to understand the partner and order fields used by the service.
3) Read fixtures.py and main.py to understand the sample input and the demo execution path.
4) Read the parameterized cases in test_acceptance_matrix.py, especially the active-status, capacity, tie-breaking, invalid-time and duplicate-cancellation tests.
5) Ran pytest -q. The initial result was 65 failed, 164 passed.
6) Ran python main.py. It completed and printed the sample assignment with order_id 0-7, partner P-2, pickup time 13 and ETA 35.

## 4. Resolution
The root causes identified are missing validation and eligibility checks in the assignment flow and the absence of an idempotency check in cancellation processing. These changes address the causes directly: invalid values will be rejected, unavailable partners will not enter candidate selection and repeated events will not be applied again.

## 5. Proof and regression prevention
1) Robust Type Enforcement (valid_minutes and valid_id)
2) Failure Isolation via Default Fallbacks (estimate_eta)
3) Data Integrity & Deduplication Safeguards (assign_order)
4) Preventing Side-Effects using Deep Copying (process_cancellation)
5) Protection Against Network Duplication (process_cancellation)

## 6. Unresolved challenge or next step
The main unresolved task is to implement the validation, partner-availability and cancellation-idempotency checks then run the complete test suite and demo again. I would first address the failing acceptance cases, inspect any remaining failure messages, add tests for malformed partner state if required and record the actual post-fix test summary. Until that work is done, the remaining baseline failures remain unresolved.