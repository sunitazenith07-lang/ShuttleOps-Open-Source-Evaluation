# TESTING.md

## Test command and environment

Testing was an important part of my work on SmartDispatch. I started by running the existing test suite before making any changes so that I could understand the current state of the application.

**Python version:** Python 3.10+ is required by the project. My exact installed Python version still needs to be recorded using `python --version`.

**Command run:**

```bash
python -m pytest -q
```

I also ran the application using:

```bash
python -m main
```

**Initial test summary:**

When I first ran the test suite on the untouched starter code, the results were:

| Result | Count |
|---|---:|
| Passed | 164 |
| Failed | 65 |
| Total | 229 |

The application demo also ran successfully and assigned order `O-7` to partner `P-2`, with a pickup time of 13 minutes and an estimated delivery time of 35 minutes.

After making changes to the travel-time validation, I reran the relevant travel-related tests and confirmed that the identified validation issue was resolved. I have not yet recorded the exact targeted test count.

## Edge-case evidence

While working on SmartDispatch, I identified and examined several edge cases that could affect ETA calculations, partner assignments and cancellation handling.

**1. Missing travel-time information:** When either required travel-time entry is missing (`None`), the system should not calculate a reliable ETA for that candidate. I addressed this by adding validation before the ETA calculation. The relevant travel-related tests were rerun, and the issue was confirmed as resolved.

**2. Negative travel time:** Travel times should never be negative. I included a non-negative check in the `is_valid_time()` helper so that negative values are rejected before being used in calculations.

**3. Boolean travel-time values:** Python treats Boolean values as a subclass of integers. Because of this, a simple numeric type check could accidentally accept `True` or `False` as travel times. I added an explicit Boolean check to prevent this.

**4. NaN and infinity:** Values such as NaN and infinity should not be accepted as valid travel times. I used Python's `math.isfinite()` function to check that the supplied values are finite.

**5. Zero travel time:** A travel time of zero is valid and should not be rejected. The validation condition allows zero while rejecting negative values. This helped preserve the distinction between actual zero travel time and missing travel information.

**6. Negative preparation time:** Preparation time must be non-negative and valid before it is included in the ETA calculation. This was identified as a validation issue during code inspection and requires final implementation and test verification.

**7. Inactive delivery partners:** An inactive delivery partner should never receive a new order, even if they have available capacity. This behaviour was identified as a missing eligibility check in the starter implementation.

**8. Partner at maximum capacity:** A partner who has already reached their maximum order capacity must not receive another assignment. This is important for preventing workload and capacity inconsistencies.

**9. Equal ETA values:** When two eligible partners have identical estimated delivery times, the system should select the partner with the lower ID in ascending lexicographic order. This ensures that assignment results remain deterministic.

**10. Duplicate cancellation events:** If the same cancellation event is received more than once, the system should process it only once. Otherwise, the partner's workload could be reduced multiple times and capacity could be released incorrectly.

**11. Empty partner list:** When no delivery partners are available, the order should remain unassigned and the system should return an appropriate explanation instead of raising an unnecessary error.

These edge cases helped me understand that the dispatch engine must handle not only normal delivery scenarios but also missing information, invalid values and unexpected events safely.

## Regression tests added

During the initial debugging stage, I primarily used the existing test cases to identify problems and verify my changes.

The first confirmed fix was travel-time validation. I introduced the reusable `is_valid_time()` helper and reran the relevant travel-related tests to check that invalid values were handled correctly.

The following areas are important for regression testing:

1. **Travel-time validation:** Prevent negative, Boolean, missing and non-finite values from being accepted.
2. **Preparation-time validation:** Ensure invalid preparation times cannot enter the ETA calculation.
3. **Partner eligibility:** Prevent inactive and capacity-full partners from receiving assignments.
4. **Deterministic selection:** Ensure equal ETAs always produce the same partner selection.
5. **Cancellation idempotency:** Prevent duplicate cancellation events from changing workload more than once.

No additional regression-test functions have been added or independently verified at this stage. Adding dedicated tests for these cases remains part of my remaining work.

## Remaining failures or limitations

The original test run had 65 failing tests and 164 passing tests.

After addressing travel-time validation, I confirmed that the corresponding issue was resolved. However, I have not yet recorded a complete test run after all subsequent implementation changes, so I cannot provide a verified final passing count.

The main remaining areas that need verification are:

- Preparation-time and current-time validation.
- Validation of malformed order and partner records.
- Partner activity and capacity restrictions.
- Duplicate cancellation handling.
- Workload consistency after cancellation.
- Regression testing for deterministic partner selection.
- Additional edge cases that may not be covered by the visible tests.

My next step is to add dedicated regression tests for these behaviours and run the complete test suite again.

I want to make sure that fixing one issue does not accidentally break another part of the application. My aim is not just to achieve a green test suite, but to make sure the underlying dispatch logic behaves reliably in different situations.