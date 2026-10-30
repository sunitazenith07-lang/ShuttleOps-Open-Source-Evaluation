# Challenges

## 1. Challenge or confusing behaviour
The hardest part was not one single bug; it was the combination of missing validation and incorrect assignment logic. The code looked close to a working dispatch function, but it was accepting invalid inputs and then selecting candidates on the basis of incomplete data.

The most important confusing cases were:
- missing travel-time entries
- inactive or full partners still being considered
- duplicate cancellation events being processed again
- negative or malformed numeric values passing through the ETA logic

## 2. Evidence
The project tests explicitly covered these behaviors. For example:
- invalid travel values were expected to return `eligible == False` and `eta_minutes is None`
- inactive partners were expected to never receive an assignment
- duplicate cancellations were expected to leave `processed_cancellation_ids` unchanged after the first event
- full-capacity partners were expected to be excluded

The evidence was captured by the acceptance and edge-case test files under `tests/`.

## 3. What I tried
I inspected the service flow end-to-end before changing code:
- from order creation to candidate filtering
- ETA calculation using travel lookup
- assignment selection using minimum ETA and tie-break rules
- cancellation state updates and workload reduction

I then ran the suite in the project environment and confirmed the failures were concentrated in the same areas: invalid route handling, partner eligibility, and duplicate cancellation processing.

## 4. Resolution
The root cause was that the service layer was missing the business rules required by the challenge. It was using raw data without validating time values and route availability, and it was not checking whether a partner was active or full before assignment.

The fix was to enforce the rules at the service boundary:
- reject missing or invalid travel legs
- reject invalid numeric values and empty IDs
- filter out inactive or full partners before assignment
- choose the lowest ETA with stable tie-breaking
- ignore duplicate cancellation events after the first processing

This addressed the cause instead of masking symptoms, because the validation rules operate before dispatch or workload changes.

## 5. Proof and regression prevention
The strongest proof is the final suite result:
- `python -m pytest -q`
- result: `229 passed in 0.05s`

The tests that specifically protect the fix are the acceptance matrix and edge-case tests covering:
- invalid route rejection
- negative preparation time rejection
- current-time validation
- inactive and full partner rejection
- tie-breaking by partner ID
- duplicate cancellation idempotency
- workload floor at zero

## 6. Unresolved challenge or next step
There are no remaining visible failures in the provided repository. The remaining work is only operational: preparing the submission files and opening the pull request against the original repository once the branch is pushed to a fork.