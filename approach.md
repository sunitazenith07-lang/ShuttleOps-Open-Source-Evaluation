# approach.md

## 1. Baseline
- **Commands run before editing:** `pytest -q` and `python main.py`.
- **Initial test result:** `65 failed, 164 passed in 1.94s` (189 test cases).
- **Demo/output observed:** `python main.py` returned `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding
- **Important files/functions inspected:** `service.py` (`estimate_eta`, `assign_order`, `process_cancellation`); `models.py` (`new_order`, `new_partner`); `fixtures.py` (`sample_inputs`); `main.py` (demo entry point); and `test_acceptance_matrix.py` (parameterized acceptance tests).
- **Candidate filtering, ETA calculation, and capacity flow traced:** `assign_order` loops through partners, calls `estimate_eta`, keeps estimates marked eligible, and selects the lowest ETA with partner ID as a tie-breaker. `estimate_eta` adds travel to the restaurant, partner workload, preparation time, and travel to the destination. The starter code does not filter inactive partners or check capacity. Cancellation removes an order and subtracts its recorded workload, but does not check whether the cancellation event was already processed.
- **How understanding was confirmed:** I compared the function flow with the fixtures, demo output, and acceptance tests, then ran the tests to observe which behaviors failed.

## 3. Investigation and implementation strategy

- **Issue 1 – ETA and input validation**
  - **Symptom:** Invalid or missing travel times, preparation times, and current-time values can be accepted or cause arithmetic errors.
  - **Evidence:** The acceptance matrix includes negative values, strings, booleans, `None`, NaN, and infinity. The baseline run failed cases for these invalid values, including `TypeError` cases.
  - **Planned fix:** Validate required order fields and ensure all time values are finite, non-negative numeric values; reject booleans rather than treating them as integers. Return an ineligible estimate when validation fails.

- **Issue 2 – Partner eligibility and capacity**
  - **Symptom:** The starter assignment flow considers partners without checking whether they are active or have free capacity.
  - **Evidence:** The baseline run failed inactive-partner and capacity-boundary cases. `assign_order` currently appends every estimate whose `eligible` field is true, while `estimate_eta` does not apply either check.
  - **Planned fix:** Filter out partners unless `active` is exactly `True` and capacity is a valid positive integer with `len(active_order_ids) < capacity`. Only compare valid candidates by ETA, using partner ID for deterministic tie-breaking.

- **Issue 3 – Duplicate cancellation events**
  - **Symptom:** Reprocessing the same cancellation event appends the event ID again.
  - **Evidence:** The baseline duplicate-cancellation tests report `['C', 'C']` instead of `['C']` after the same event is applied twice.
  - **Planned fix:** Check `processed_cancellation_ids` before applying a cancellation. If the event ID has already been processed, return an unchanged copy; otherwise release the order/workload and record the event once.

## 4. Implementation decisions
- **Main changes and why:** No implementation changes have been made in this review. The fixes listed above are the proposed changes indicated by the starter code and failing acceptance tests.
- **Alternatives considered and why rejected:** No alternatives have been implemented or experimentally compared. The proposed approach validates inputs at the ETA boundary and filters candidates before selection so invalid data does not enter the comparison.
- **Assumptions:** Time values are expressed in minutes. A partner is available only when `active is True` and the number of active orders is below a valid positive-integer capacity. Cancellation event IDs identify unique events.

## 5. Verification
- **Tests added or changed:** None during this review; the supplied `test_acceptance_matrix.py` was run unchanged.
- **Commands run and actual results:**
  - `pytest -q` — `61 failed, 128 passed in 0.83s`.
  - `python main.py` — printed the demo assignment shown in Section 1 and exited successfully.
- **Edge cases verified:** The supplied test matrix exercises missing/invalid travel times, invalid preparation and current-time values, inactive partners, capacity boundaries, ETA ties, duplicate cancellations, unknown order IDs, and workload not dropping below zero. The baseline run shows that several of these cases currently fail.
- **Remaining failures or known limitations:** The 61 baseline failures remain because the service code has not yet been changed. The demo output alone does not verify all eligibility and cancellation behaviors. Re-run the full test suite and demo after implementing the proposed fixes, then replace this baseline status with the actual results.

## 1. Finally after making changes.
- **Commands run after editing:** `pytest -q` and `python main.py`.
- **Initial test result:** `229 passed in 0.44s` (189 test cases).
- **Demo/output observed:** `python main.py` returned `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.