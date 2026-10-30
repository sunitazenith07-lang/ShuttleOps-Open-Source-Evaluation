Approach — SmartDispatch

1. Understanding the Codebase

I reviewed the project instructions, problem statement, starter implementation, data models, and automated tests.

The main implementation is in service.py. The data structures for partners and orders are defined in models.py.

2. Initial Testing

I ran the test suite using:

python -m pytest -q

The initial run reported 65 failures and 164 passing tests. I used the failing tests to identify incomplete validation and dispatch behaviour.

3. Implementation Approach

I focused on the following areas:

1. Input validation: Check required order fields and reject invalid or negative time values.
2. ETA calculation: Calculate pickup time using current time, travel time to the restaurant, and partner workload.
3. Partner eligibility: Consider only active partners who have available capacity.
4. Assignment: Choose the partner with the lowest ETA.
5. Tie-breaking: Use ascending partner ID when ETAs are equal.
6. Cancellation: Track processed cancellation event IDs to prevent duplicate workload release.

4. Verification

After implementation, I ran:

python -m pytest -q

The final reported result was 232 passed tests.

The tests cover ETA calculations, missing routes, invalid inputs, capacity checks, tie-breaking, and cancellation idempotency.

5. Design Decisions

* Missing travel data is treated as unavailable rather than zero.
* Invalid time values are rejected.
* A partner at capacity is not considered for assignment.
* Cancellation processing is idempotent.
* The implementation uses deterministic selection so identical inputs produce consistent results.

6. Limitations

The implementation uses synthetic travel-time data and does not include live GPS, traffic prediction, or real-time map services.