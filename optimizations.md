# optimizations.md

## 1. Baseline and objective

When I started working on SmartDispatch, my main focus was not on making the application run faster but on making the existing logic more reliable and easier to maintain.

The initial test results showed 164 passing tests and 65 failing tests. This indicated that several parts of the application needed improvement, particularly input validation, partner eligibility and cancellation handling.

I identified a few areas where the code could be improved:

- Validation logic was limited and needed to be more consistent.
- Similar validation conditions could become repetitive if written separately in different places.
- Invalid input handling needed to be more predictable.
- The assignment logic needed to consider partner eligibility before calculating ETAs.
- Cancellation processing needed to avoid applying the same event more than once.

My main objective was therefore to improve correctness and maintainability without introducing unnecessary complexity.

## 2. Options considered

While working on the validation logic, I considered a few different approaches.

### Option 1: Writing validation conditions directly inside each function

One approach was to write separate conditions for checking travel time, preparation time and other time-related values.

This would work, but it could lead to repeated code. It would also make future changes more difficult because the same validation rules might need to be updated in multiple places.

### Option 2: Creating a reusable validation helper

I chose to create a helper function called `is_valid_time()`.

This allowed me to keep the time-validation rules in one place and reuse them wherever necessary.

I preferred this approach because it makes the code easier to read and reduces unnecessary repetition.

### Option 3: Sorting all candidates before selecting a partner

Another possible approach for partner selection would be to sort all eligible candidates by ETA and then select the first one.

However, sorting an entire list is unnecessary when the application only needs the candidate with the lowest ETA.

Using Python's `min()` function with an appropriate selection key is a simpler alternative. The existing implementation already follows this approach, so I kept it rather than introducing additional sorting logic.

I also decided against adding caching or complicated optimization techniques because the supplied project did not provide evidence that ETA calculation speed was a problem.

## 3. Changes implemented

### 1. Reusable time validation

The first improvement I implemented was creating the `is_valid_time()` helper function.

```python
def is_valid_time(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )
```

Previously, the travel-time validation only checked whether a value was `None`.

The new helper checks the numeric type, excludes Boolean values, rejects non-finite numbers and ensures that time values are non-negative.

This makes the validation logic easier to reuse and understand.

### 2. Consistent travel-time validation

I used the new helper function to validate both required travel-time entries before calculating the ETA.

This ensures that the same validation rules are applied to both travel legs.

It also makes future changes easier because the validation rules can be updated in one place.

### 3. Keeping the existing ETA calculation

I decided to retain the original ETA calculation for valid inputs instead of rewriting the working mathematical logic.

The existing formula already followed the requirements of the problem statement, so changing it unnecessarily could introduce new problems.

### 4. Maintaining deterministic partner selection

The existing implementation uses `min()` with ETA and partner ID as the selection criteria.

I retained this approach because it is straightforward and ensures that candidates with equal ETAs are handled consistently.

**Testing and measurement:**

After implementing the travel-time validation helper, I reran the relevant travel-related tests and confirmed that the issue was resolved.

I did not conduct formal execution-time or memory benchmarks. Therefore, I am not claiming any measured performance improvement.

## 4. Trade-offs

During the implementation, I focused on keeping the code simple rather than introducing more complicated solutions.

Some of the trade-offs I considered were:

**Code reusability vs. additional function calls**

Creating a helper function introduces an additional function call, but it avoids repeating the same validation conditions throughout the code.

I preferred the reusable approach because maintainability and consistent validation were more important than an unmeasured micro-optimization.

**Simplicity vs. complexity**

I avoided introducing unnecessary caching, sorting or additional data structures because the current project did not demonstrate a need for them.

**Correctness vs. convenience**

I chose to reject missing or invalid travel-time information rather than silently treating it as zero.

This can result in fewer eligible delivery partners, but it prevents the system from producing misleading delivery estimates.

Overall, I prioritised correctness, readability and maintainability over optimizations that were not supported by actual performance measurements.

## 5. Further improvements

With more time, there are several areas I would like to improve further.

1. **Extend reusable validation:** Reuse the time-validation helper for preparation time, current time and partner workload after confirming the relevant input contracts.

2. **Improve identifier validation:** Introduce a separate helper to validate order IDs, restaurant IDs and destination zones consistently.

3. **Improve cancellation handling:** Ensure duplicate cancellation events are detected before modifying partner workload or active orders.

4. **Review candidate selection:** Investigate whether the assignment process can be made more efficient for substantially larger partner datasets while preserving deterministic results.

5. **Add more regression tests:** Cover invalid inputs, capacity boundaries, missing travel information and repeated cancellation events.

6. **Performance measurement:** If the dataset becomes significantly larger, use Python profiling tools to measure execution time and identify actual bottlenecks before making further optimizations.

My overall learning from this part of the project is that optimization does not always mean making code faster. Sometimes, making code easier to understand, reuse and maintain is a more valuable improvement, especially when correctness is the main requirement.