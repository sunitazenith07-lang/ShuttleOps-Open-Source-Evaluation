Challenges — SmartDispatch

1. Challenge: Incomplete Dispatch Logic

The starter implementation did not fully enforce partner eligibility and capacity requirements.

Resolution: Added checks to ensure that only active partners with available capacity are considered.

2. Challenge: Invalid and Missing Travel Data

Missing routes and invalid travel-time values could lead to unreliable ETA calculations.

Resolution: Added validation for travel times and ensured missing or invalid route data makes a partner ineligible.

3. Challenge: Deterministic Assignment

Selecting the correct partner when multiple partners have the same ETA required consistent tie-breaking.

Resolution: Selected the lowest ETA and used ascending partner ID as the tie-breaker.

4. Challenge: Duplicate Cancellation Events

Processing the same cancellation more than once could incorrectly reduce partner workload.

Resolution: Added processed cancellation event tracking to make cancellation processing idempotent.

5. Verification

I initially ran the automated tests and observed 65 failures and 164 passing tests.

After implementing the changes, I ran:

python -m pytest -q

The final reported result was 232 passed tests.

6. Remaining Limitations

* The system uses synthetic travel-time data.
* Live traffic and GPS integration are not included.
* Further integration testing with the expanded dataset should be reviewed.