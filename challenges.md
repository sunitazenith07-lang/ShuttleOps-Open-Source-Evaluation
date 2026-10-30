# Challenges

## 1. Challenge or confusing behaviour
The hardest distinction was between missing route data and a valid zero-minute route. Cancellation idempotency also required checking identity before workload or active-order mutations.

## 2. Evidence
The baseline had 65 failures, including inactive partners, full capacity, negative preparation, invalid route values, and duplicate cancellation. Acceptance tests use `None` for missing routes and `0` for valid zero-duration routes.

## 3. What I tried
I ran the complete pytest suite, focused on failing contract tests, and ran the demo. The failures showed that filtering needed to be implemented in the service rather than adjusted in fixtures or assertions.

## 4. Resolution
The root cause was missing value-contract checks. I added finite non-negative numeric validation and explicit dictionary lookup. Duplicate cancellation now exits before mutation when its event ID is already processed.

## 5. Proof and regression prevention
ETA matrices, route-missingness cases, capacity boundaries, duplicate-cancellation tests, and four focused contract regressions now pass. Final result: 233 passed. Externally malformed dictionaries remain an area for further fuzz testing.

## 6. Unresolved challenge or next step
No visible-suite failures remain. Future external integrations should add explicit record schemas. The next investigation would fuzz malformed nested dictionaries and verify no exceptions escape public service functions.
