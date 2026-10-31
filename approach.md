# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: python -m pip install -r requirements-dev.txt followed by python -m pytest -q.
- Initial test result (include the actual summary): 65 tests failed, 164 passed.
- Demo/output observed:I observed total of 5 demo ouputs and these are as follows:
 1. test_duplicate_cancellation_is_idempotent: The test failed because the list of processed_cancellation_ids had duplicates (e.g., ['C', 'C']).
 2. test_inactive_partner_not_assigned: The test failed because the code assigned orders to partners that have active=False.
 3. test_full_partner_not_assigned: The test failed because the code assigned orders to partners that were at full capacity.
 4. test_eta_calculation_matrix: The test failed because estimate_eta returned eligible=False for valid input parameters.
 5. test_current_time_validation / test_preparation_time_validation: The tests failed because the code accepted invalid types and negative numbers.

## 2. Codebase understanding
- Important files/functions inspected: service.py (logic implementation), test_acceptance_matrix.py (rules validation) and, test_contract.py (constraints).
- Candidate filtering, ETA calculation, and capacity flow traced: The assign_order function looped through partners, however, it didn't have validation to check whether the partner is active and had any capacity limit before assigning.

The estimate_eta function calculated the estimated pickup time as now + leg1 + workload, and then calculated eta as pickup + prep + leg2. But this function did not have validation on inputs to check if all inputs are valid and within range.

The process_cancellation function was cancelling orders while processing cancellations, but it didn't track previously processed cancellations' IDs, hence there was a chance of duplicating the cancellation process.
- How you confirmed your understanding:

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Idempotency of Cancellation
    Symptom: The system was generating duplicate cancellation IDs in the output.
    Hypothesis: The system did not perform a check for any cancellation IDs.
    Fix: Created the processed_cancellation_ids array. Check if the ID to be processed has been processed before. If it has, return the current state. If it has not, process it and append it to the list.
- Issue 2: Missing Input Validation
    Symptom: TypeError crash or bad value acceptance such as now=-1 or prep_minutes=True.
    Hypothesis: The system did not enforce input checking.
    Fix: Implemented strict checks in estimate_eta and assign_order to eliminate: 
    1. Wrong types (strings, None, booleans).
    2. Negative values.
    3. NaN and Infinity.
    4. Mark it as eligible=false immediately if any check fails.
- Issue 3: Wrong Eligible Flag
    Symptom: Demanded conditions returned eligible=false.
    Hypothesis: The return statement always returned eligible=False.
    Fix: Changed the successful return to eligible=True path.
- Issue 4: Eligibility of Partners
  Symptom: There are reports about inactive and overloaded partners having received orders.
   Hypothesis: assign_order did not filter partners based on active status or capacity.
   Fix: Added explicit checks to skip partners where active is not True or len(active_order_ids) >= capacity.

## 4. Implementation decisions
- Main changes and why: For all inputs, validation was implemented, which has enabled and ensured safety and optionally deterministic behavior in terms of running the software. For cancellation purposes, idempotency checks were added. 
- Alternatives considered and why rejected: No exceptions were used because the testing unit has been made in a way that invalid inputs render eligible=False returns and not errors.
- Assumptions: It is also worth mentioning that all time values must have finite and non-negative values. Boolean types will be rejected even when treated as integers in the Python programming language.

## 5. Verification
- Tests added or changed: None. I used the used the existing test suite.
- Commands run and actual results: python -m pytest -q and actual result - 0 failures, 229 passed
- Edge cases verified: Duplicate cancellations, inactive partners, capacity limits, invalid input types, negative values, NaN/Infinity, empty fields.
- Remaining failures or known limitations: None.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.