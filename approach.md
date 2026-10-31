# approach.md

## 1. Baseline

Before making changes, I wanted to understand the existing project and see how much of the starter code was already working.

**Commands I ran:**

```bash
python -m pytest -q
python -m main
```

**Initial test results:**

| Result | Count |
|---|---:|
| Passed | 164 |
| Failed | 65 |
| Total | 229 |

The initial test run helped me identify the areas that needed the most attention.

**Demo/output observed:**

When I ran the application using `python -m main`, it successfully assigned order `O-7` to delivery partner `P-2`.

The output showed:

- Order ID: O-7
- Assigned partner: P-2
- Pickup time: 13 minutes
- Estimated delivery time: 35 minutes
- Status: Assigned

This confirmed that the basic ETA calculation and partner selection were already working for the supplied example.

## 2. Codebase understanding

I started by exploring the repository and understanding the purpose of its main files.

The important files and functions I inspected were:

| File | Purpose |
|---|---|
| `service.py` | Contains the main ETA, assignment and cancellation logic |
| `models.py` | Defines the data structures used by the application |
| `fixtures.py` | Contains sample data for testing |
| `main.py` | Entry point for running the application |
| `tests/` | Contains acceptance, contract and edge-case tests |
| `data/records.json` | Contains the synthetic project records |

I focused particularly on understanding three functions in `service.py`:

**1. `estimate_eta()`**

This function calculates the pickup time and final delivery ETA using partner travel time, existing workload, restaurant preparation time and customer travel time.

**2. `assign_order()`**

This function evaluates delivery partners and selects the candidate with the lowest estimated delivery time. When two candidates have the same ETA, partner ID is used as a tie-breaker.

I also identified that the starter implementation needed proper active-status and capacity checks before selecting candidates.

**3. `process_cancellation()`**

This function handles order cancellations by removing cancelled orders and updating the delivery partner's remaining workload.

During my investigation, I noticed that duplicate cancellation events were not checked before processing them again.

To confirm my understanding, I compared the existing implementation with the problem statement and studied the assertions in the supplied tests.

## 3. Investigation and implementation strategy

I decided to work on the project incrementally, focusing on one problem at a time instead of rewriting the entire codebase.

### Issue 1: Travel-time validation

**Symptom:**

The existing function only checked whether travel-time values were `None`. Other invalid values could still be used during ETA calculation.

**My investigation:**

I looked at the different travel-time cases covered by the tests and realised that the existing condition was not sufficient.

**Fix chosen:**

I imported Python's `math` module and created a reusable helper function called `is_valid_time()`.

It checks whether a value is numeric, non-Boolean, finite and non-negative.

I then used this function to validate both required travel-time values before calculating the ETA.

**Result:**

I reran the relevant travel-time tests and confirmed that this validation issue was resolved.

### Issue 2: Preparation-time validation

**Symptom:**

Preparation time was retrieved directly from the order and used in the ETA formula without proper validation.

**My investigation:**

While reviewing `estimate_eta()`, I noticed that invalid or missing preparation times could reach the calculation.

**Fix chosen:**

The intended approach is to retrieve preparation time separately and reuse the existing `is_valid_time()` helper before performing the calculation.

This avoids duplicating validation logic and ensures that invalid preparation times do not produce unreliable ETAs.

### Issue 3: Partner eligibility and cancellation handling

**Symptom:**

The starter assignment logic did not properly filter inactive partners or partners who had reached their maximum capacity.

I also found that `process_cancellation()` recorded cancellation events without first checking whether the same event had already been processed.

**My investigation:**

I examined the partner selection logic and cancellation flow to understand how these behaviours could affect assignments, workload and available capacity.

**Fix chosen:**

My intended approach is to check partner activity and available capacity before calculating candidate ETAs.

For cancellations, I plan to check the event ID against previously processed cancellation IDs before changing active orders or workload.

These changes are being handled separately so that each behaviour can be tested properly.

## 4. Implementation decisions

One of my main decisions was to use reusable helper functions instead of writing the same validation conditions multiple times.

The `is_valid_time()` function is an example of this approach. It keeps validation consistent and makes the code easier to understand and maintain.

Other important decisions include:

- Keeping the existing ETA calculation formula rather than changing working mathematics.
- Treating missing travel information as unknown instead of assuming zero.
- Keeping partner selection deterministic using ETA followed by partner ID.
- Checking partner eligibility before considering a partner for assignment.
- Using duplicate cancellation detection to prevent workload and capacity inconsistencies.
- Making focused changes instead of unnecessarily rewriting working parts of the starter code.

I also wanted to avoid hard-coding values or writing solutions that only work for the supplied fixtures. The implementation should follow the problem statement and handle different valid inputs.

One assumption in the current implementation is that a missing partner workload defaults to zero, as in the starter code. This should be checked against the intended data contract.

## 5. Verification

Testing has been an important part of my development process.

I started with the existing test suite and used its failures to understand where the starter implementation needed improvement.

**Commands used:**

```bash
python -m pytest -q
```

```bash
python -m main
```

**Initial verification:**

- 164 tests passed.
- 65 tests failed.
- The supplied demo successfully assigned O-7 to P-2 with an ETA of 35 minutes.

After implementing the travel-time validation helper, I reran the relevant travel-related tests and confirmed that the issue was resolved.

**Important edge cases identified for verification:**

- Missing travel-time information.
- Negative and non-finite time values.
- Boolean values used as time inputs.
- Invalid preparation time.
- Inactive delivery partners.
- Partners already at maximum capacity.
- Two candidates with identical ETAs.
- Duplicate cancellation events.
- Empty partner lists.
- Malformed input records.

I have not added new regression tests yet, so this remains an important part of the work.

The complete test suite still needs to be rerun after all remaining changes, and the final test results will be recorded once that verification is complete.

## 6. Remaining work and known limitations

My next focus is to finish the remaining validation and assignment logic and verify the complete application.

The main areas I still need to work on are:

1. Complete preparation-time, current-time and workload validation.
2. Validate order identifiers and malformed records.
3. Ensure inactive and capacity-full partners are excluded.
4. Complete duplicate cancellation handling.
5. Add regression tests for the important edge cases.
6. Run the complete visible test suite again.
7. Review the final implementation before creating the pull request.

My overall approach has been to first understand how the existing system works, identify the actual causes of failing tests, and then make small changes that address those causes.

I want the final implementation to be reliable and understandable, rather than simply making the visible tests pass.