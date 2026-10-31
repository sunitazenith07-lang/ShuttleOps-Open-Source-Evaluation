# Challenges Faced

## 1. Understanding the Existing Codebase
One of the first challenges was understanding how the existing dispatch system worked. I needed to trace how partners were selected, how ETA was calculated, and how capacity and workload affected assignment.

**How I handled it:** I inspected the main service logic, supporting models, fixtures, and existing tests before making changes.

## 2. Identifying the Root Causes of Test Failures
The initial test run reported 65 failures. Some failures involved invalid ETA inputs, inactive partners, capacity checks, and cancellation handling. The challenge was to identify the underlying logic errors rather than fixing individual test cases with hardcoded conditions.

**How I handled it:** I examined the failing tests, traced the relevant functions, and made changes to the shared logic.

## 3. Handling Invalid Input Safely
The system needed to handle invalid numeric values, including negative numbers, booleans, NaN, and infinity. These values could otherwise lead to incorrect ETA calculations or unexpected assignment results.

**How I handled it:** I improved input validation so that invalid values are rejected before they affect calculations.

## 4. Preventing Unwanted Data Mutation
Cancellation handling was challenging because modifying a partner's order list or workload could unintentionally modify the original data structure.

**How I handled it:** I copied the partner data and relevant mutable structures before applying cancellation updates. I also added regression tests to verify that the original data remains unchanged.

## 5. Making Cancellation Idempotent
Repeated cancellation requests could cause the same cancellation to be processed more than once. This could lead to incorrect order and workload updates.

**How I handled it:** I added a check for previously processed cancellation IDs so duplicate requests do not repeat the operation.

## 6. Verifying the Final Implementation
After making the changes, I needed to ensure that the fixes did not break existing functionality.

**How I handled it:** I added regression tests for the identified edge cases and ran the complete test suite.

Final verification result: `241 passed in 0.26s`.

## Conclusion
The biggest learning from this task was that fixing a bug requires understanding the underlying logic, not just making a failing test pass. I also learned the importance of input validation, safe data handling, regression testing, and verifying changes against the complete test suite.