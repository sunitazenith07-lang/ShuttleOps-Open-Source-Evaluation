# TESTING.md — Required Submission

## Test command and environment

* Python version: Python 3.13.15
* Command run: `python -m pytest -q`
* Actual test summary: 229 passed in 0.28s.
* Test status: All 229 tests passed successfully.

## Edge-case evidence

### 1. Missing travel-time entry

* **Expected:** Partner should be excluded from ETA calculation.
* **Actual:** Full test suite passed (229 tests).
* **Evidence:** Individual test mapping not confirmed.

### 2. Inactive delivery partner

* **Expected:** Inactive partner should not receive a new order.
* **Actual:** Full test suite passed (229 tests).
* **Evidence:** Individual test mapping not confirmed.

### 3. Maximum partner capacity

* **Expected:** Partner should not receive another order after reaching capacity.
* **Actual:** Full test suite passed (229 tests).
* **Evidence:** Individual test mapping not confirmed.

### 4. Equal ETA

* **Expected:** Partner with lexicographically smaller ID should be selected.
* **Actual:** Full test suite passed (229 tests).
* **Evidence:** Individual test mapping not confirmed.

### 5. Duplicate cancellation

* **Expected:** Cancellation should be processed only once.
* **Actual:** Full test suite passed (229 tests).
* **Evidence:** Individual test mapping not confirmed.


## Regression tests added

The project test suite reports 229 passing tests.

The important behaviours documented in this project include:

1. Missing travel-time information is not treated as zero.
2. Duplicate cancellation events should not update workload twice.
3. Equal ETA values use deterministic partner ID ordering.
4. Invalid order fields should not result in partner assignment.
5. Inactive and full-capacity partners should not receive new orders.

## Remaining failures or limitations

* No failing tests were reported in the latest test run.
* A valid ETA cannot be calculated if required travel-time information is missing.
* Individual test-to-edge-case mappings have not all been independently verified.
