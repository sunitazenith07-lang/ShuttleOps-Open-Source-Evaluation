# Testing

## How I tested the project

I installed the development requirements using:

`python -m pip install -r requirements-dev.txt`

I ran the tests using:

`python -m pytest -q`

I also ran the program using:

`python -m main`

The sample run printed:

`{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

For this sample, partner P-2 has a pickup time of 13 minutes and an ETA
of 35 minutes. Partner P-1 has an ETA of 36 minutes, so P-2 is selected.

## Test results during development

At the beginning, the test run showed 65 failures and 164 passes. This
helped me identify which parts of the starter code were incomplete.

After making the earlier set of fixes, the test run showed:

`229 passed`

I later worked on a shorter version of the code. I still need to run the
full test command again on that final version before treating 229 passed
as its result.

## Edge cases I considered

1.  **Missing travel time:** If either travel-time entry is missing, the
    partner should not receive a made-up ETA.
2.  **Negative time:** Negative preparation, travel, workload, or
    current-time values should not be accepted as valid time values.
3.  **Inactive partner:** A partner who is not active should not be
    assigned an order.
4.  **Full partner:** A partner who has reached their order capacity
    should be skipped.
5.  **Same ETA:** If two partners have the same ETA, the partner ID
    decides who is selected.
6.  **No available partner:** If no partner is eligible, the order
    should remain unassigned.
7.  **Repeated cancellation:** Processing the same cancellation event
    again should not reduce workload a second time.
8.  **Cancellation for an unknown order:** A cancellation should not
    remove an order that is not in the partner's active order list.

## Final check

Before submitting, I should run `python -m pytest -q` again after the
final code changes and record the actual result here. I should also
check `python -m main` to make sure the sample still works.
