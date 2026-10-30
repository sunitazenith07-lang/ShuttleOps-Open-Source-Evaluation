# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour

The tricky part was that the ETA formula could look correct for normal numbers, while invalid values still got through. For example, a negative preparation time or a negative current time could still produce an eligible result. Partner selection also needed to check active status and capacity, not only whether an ETA could be calculated.

## 2. Evidence

- The negative travel-time case expected `eligible` to be `False`, but the ETA validation did not reject a negative route value.
- The negative preparation-time and current-time tests also expected the partner to be ineligible.
- The inactive-partner test returned partner `P` even though `active` was `False`.
- With capacity `1` and one active order, the service still selected that partner.
- A duplicate cancellation produced `['C', 'C']` instead of `['C']`.
- A workload value of `-5` produced a negative pickup time, and a workload value of `"5"` raised `TypeError`.
- Running the full dataset through the service showed that 55 cancelled orders could still be assigned, and 7 cancellation records had no event ID.

## 3. What I tried

- I ran the individual failing pytest cases to see the actual input and assertion.
- I followed each case into the related function in `service.py`.
- I added validation before ETA arithmetic and filtering before adding partners to the assignment options.
- I reran the focused test groups and then the full test suite.

I used an AI assistant to help understand the test output and implement/check fixes.

## 4. Resolution

- `is_valid_minutes` now checks that travel times, preparation time, current time and partner workload are finite, non-negative numbers, and are not booleans.
- `is_valid_identifier` checks the order ID, restaurant ID and destination zone.
- `assign_order` skips inactive partners and partners with invalid or full capacity.
- `process_cancellation` ignores an event ID it has already processed.
- `assign_order` leaves orders marked `CANCELLED` unassigned, and `process_cancellation` leaves partner data unchanged when the event ID is missing or invalid.

These changes address the input checks and filtering that were missing, instead of changing the tests or the ETA formula.

## 5. Proof and regression prevention

- The final full test run was **237 passed**.
- I added six workload cases to `test_invalid_partner_workload_is_rejected`.
- The existing parameterized acceptance tests cover invalid routes and times, inactive partners, capacity boundaries, invalid order fields and duplicate cancellations.
- Dataset integration tests cover all 180 orders and 177 cancellation events.
- The demo also ran successfully and assigned the sample order to `P-2` with ETA `35`.

## 6. Unresolved challenge or next step

The visible suite and supplied dataset pass, but hidden tests are not available here. If new input shapes appear, I would add a small test for them and rerun the full suite.