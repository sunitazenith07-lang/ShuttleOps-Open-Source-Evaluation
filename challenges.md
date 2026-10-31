# Challenges

## 1. Challenge or confusing behaviour

The most confusing part was that many tests failed at once. At first, it looked like there were dozens of separate problems. I also had to understand why a repeated cancellation still failed a test even when the workload did not go below zero.

Another tricky detail was that Python treats `True` like the number `1` in some checks. That could make a travel time or capacity look valid when it should not be.

## 2. Evidence

- The first test run had 65 failures and 164 passes. Grouping the failures showed that several shared causes were behind them, such as missing capacity checks and missing input checks.
- A travel-time test using `True` failed because the starter treated it like one minute.
- A capacity test using `True` also failed because the partner was selected when it should have been rejected.
- The duplicate-cancellation test showed `processed_cancellation_ids` as `['C', 'C']`. The workload was already zero, so the problem was that the event was recorded twice.
- The sample cancellation data also includes events without an ID and repeated IDs.

## 3. What I tried

1. I grouped the failed tests by test name to see which failures might share a cause. This showed that many failures came from a few missing rules.
2. I read the test cases and their inputs, including the cases where times or capacity were `True`, text, missing, or negative.
3. I ran a specific duplicate-cancellation case and compared the workload with the list of processed IDs. This showed that the workload was not the cause of that test failure; the event ID was being added twice.
4. I checked the sample cancellation data for missing and repeated IDs, then used regression tests to check cancellation handling across the event stream.

## 4. Resolution

I added shared checks for valid times and IDs, and checked partner activity and capacity before calculating ETAs. The time check excludes booleans as well as negative and non-finite numbers.

For cancellations, the code now checks whether an event ID was already processed. If it was, it returns the copied partner record without changing it. Events without an ID are ignored because the code cannot use an ID to recognize a repeat. These changes address the missing checks that caused the failures instead of handling individual test examples separately.

## 5. Proof and regression prevention

The project notes record that the original 229 tests passed after the fixes, and that 214 regression tests were added. The full recorded result is 443 passing tests.

Some useful regression tests are `test_truthy_non_bool_active_flag_is_not_treated_as_active`, `test_reused_event_id_with_different_payload_is_ignored`, `test_cancellation_without_event_id_is_not_applied`, and `test_dataset_cancellation_stream_never_double_releases`. The new tests also check the dataset orders and other invalid inputs.

A related case that could still cause trouble is a cancellation sent to the wrong partner. The current function is given a partner record directly and has no overall record that maps each order to its assigned partner.

## 6. Unresolved challenge or next step

The assignment function does not update a partner's workload or active orders after choosing them. A next step would be to decide where that update should happen and add tests for assigning several orders in a row.

The code also does not check an order's status, so an order marked cancelled could still be considered for assignment. The next step would be to confirm the expected rule with the project instructions and add a test before changing the code. It could also be useful to check that a cancellation is sent to the right partner.
