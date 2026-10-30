# Challenges and debugging

Actual observations from Codex's AI-assisted implementation.

## Time types and eligibility
The baseline had 65 failures, including negative/string/bool/NaN/infinite time cases,
inactive partners and full capacity. Python booleans behave as numbers, so generic arithmetic
or isinstance(value, int) was insufficient. Added exact numeric type checks and finite float
validation, plus separate strict capacity and active checks. Existing validation matrices and
new malformed-field regressions now pass.

## Cancellation identity versus order identity
A replay guard must run before releasing any order: a repeated event ID with a changed order
payload must not release a different active order. Also, a new event ID for an already cancelled
order must not subtract its old minutes again. The new regression starts with two active orders
and verifies both cases, the retained workload, ledger cleanup and input immutability.

## Missing accounting data
The demo has workload without a complete per-order minutes ledger. Requiring a complete ledger
for ETA would incorrectly reject the existing fixture. ETA uses aggregate workload; cancellation
uses an available per-order deduction, retaining workload if that deduction is absent.
Negative/malformed ledger values reject cancellation. This conservative policy is documented.

## Numeric boundaries
Finite input floats can still sum to infinity, and mixing huge ints with floats can overflow.
The regression tests genuine integer arithmetic separately from invalid float conversion;
the service checks calculation results and catches overflow before updating state.

## Remaining work and limitations
All 274 local tests pass. Publication uses the browser signed in as @adjj07, as requested. GitHub CI is not yet observed. A concurrent real service would need
atomic capacity reservations and a durable event registry; these are outside this offline API.
