# Challenges.md

## 1. Challenge or confusing behaviour

When I first started working on SmartDispatch, one of the things I found confusing was how the system handled missing and invalid time values while calculating delivery ETAs.

Initially, the `estimate_eta()` function only checked whether the travel-time values were `None`. I realised that this wasn't enough because values like negative numbers, Boolean values, strings, NaN and infinity could also get through the validation.

Another thing I had to understand was the difference between a travel time of zero and missing travel information. A travel time of zero is valid, but missing information should not automatically be considered zero.

While exploring the rest of the code, I also noticed a few other areas that needed attention:

- Preparation time was being used without proper validation.
- Current time and partner workload also needed to be checked.
- Partner selection needed to consider whether a partner was active and had available capacity.
- Duplicate cancellation events could affect workload and capacity incorrectly.
- When two partners had the same ETA, the system needed a consistent way to select one.

## 2. Evidence

When I first ran the test suite on the original starter code, I got the following results:

| Test result | Count |
|---|---:|
| Passed | 164 |
| Failed | 65 |
| Total | 229 |

I looked into the failing tests and found that the problems were spread across different parts of the application.

| Problem area | Failed cases |
|---|---:|
| Travel-time validation | 9 |
| Preparation-time validation | 8 |
| Inactive partner selection | 5 |
| Capacity validation | 11 |
| Duplicate cancellation | 15 |
| Current-time validation | 5 |
| Invalid order fields | 8 |
| Additional contract failures | 4 |

One example I came across was the travel-time validation. The original code only checked whether a value was `None`, so other invalid values could still reach the ETA calculation.

This helped me understand why input validation was an important part of this project.

## 3. What I tried

I decided to approach the problems one at a time instead of changing the entire codebase together.

Here is what I did:

1. Started by reading `service.py` to understand how the ETA calculation and partner assignment worked.
2. Ran the existing test suite to get an idea of what was working and what was failing.
3. Investigated the travel-time validation and understood why checking only for `None` was insufficient.
4. Created a reusable helper function called `is_valid_time()`.
5. Used `isinstance()` to check whether a value was numeric and added a separate condition to reject Boolean values.
6. Used `math.isfinite()` to make sure values like NaN and infinity were rejected.
7. Updated the existing travel-time validation to use the new helper function.
8. Ran the relevant travel-time tests again and confirmed that the issue was resolved.
9. Continued reviewing the remaining functions to understand the problems with preparation time, partner eligibility, capacity and cancellation handling.

Working this way helped me understand each problem individually and made it easier to identify where changes were actually needed.

## 4. Resolution

The first issue I successfully addressed was travel-time validation.

I imported Python's `math` module and created the following helper function:

```python
def is_valid_time(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )
```

This function checks whether a time value is numeric, is not a Boolean, is finite and is non-negative.

I then reused this function to validate both travel-time entries before calculating the ETA.

This fixed the actual problem because invalid values were stopped before they could affect the calculation. Instead of trying to correct an incorrect ETA afterwards, the function now checks the input first.

While reviewing the rest of the code, I also identified a few improvements that needed to be made:

- Preparation time, current time and partner workload need similar validation.
- Inactive partners and partners who have reached their capacity should not be considered for new assignments.
- Cancellation event IDs need to be checked before processing an event so that the same cancellation cannot release workload twice.

These were identified as important areas for further correction and verification.

## 5. Proof and regression prevention

I used the original test results as my starting point: 164 tests passed and 65 failed.

After making the travel-time validation changes, I ran the relevant travel-related tests again and confirmed that the travel-time validation issue was resolved.

I also identified several cases that are important to test whenever changes are made to this logic.

| Test scenario | Expected behaviour |
|---|---|
| Zero travel time | Should be accepted |
| Negative travel time | Should be rejected |
| Missing travel information | Should not produce a reliable ETA |
| Boolean travel value | Should be rejected |
| NaN or infinity | Should be rejected |
| Negative preparation time | Should be rejected |
| Inactive delivery partner | Should not be eligible |
| Partner at maximum capacity | Should not be eligible |
| Two partners with equal ETAs | Partner with the lower ID should be selected |
| Duplicate cancellation | Workload should not be released twice |

One area I still need to pay attention to is the validation of other inputs, especially current time and partner workload. Even if the travel-time validation works correctly, invalid values in these other fields could still affect the final ETA.

Adding regression tests for these situations will help prevent similar issues from appearing again.

## 6. Unresolved challenge or next step

At this stage, my main focus is to complete the remaining fixes and verify the entire implementation against the visible test suite.

My next steps are:

- Complete preparation-time and current-time validation.
- Check order identifiers and partner workload.
- Make sure partner eligibility and capacity rules work correctly.
- Verify that duplicate cancellation events are handled only once.
- Add regression tests for important edge cases.
- Run the complete test suite and record the actual final results.
- Review the code for any other cases that might not be covered by the visible tests.

One of the biggest things I have learned from working on SmartDispatch is that making the normal calculation work is only one part of software development. Handling unexpected inputs, missing information and repeated events is equally important.

This project has helped me understand why validation, testing and writing maintainable code matter so much when building a reliable backend system.