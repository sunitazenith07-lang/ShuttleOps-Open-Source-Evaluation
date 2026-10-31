# DISPATCH_NOTES.md — Dispatch Architecture and Worked Examples

**Project:** SmartDispatch — Delivery Partner Assignment and ETA Engine  
**Author:** Candidate Submission  
**Repository:** `SmartDispatch-Open-Source-Evaluation`  

---

## 1. Worked ETA Example (From Official Demo Fixture)

This example illustrates the end-to-end dispatch decision using the actual synthetic records defined in `fixtures.py` and run by `main.py`.

### Input Setup
- **Current Simulation Time (`now`):** `0` minutes
- **Order (`order`):**
  - `order_id`: `"O-7"`
  - `restaurant_id`: `"R-2"`
  - `destination_zone`: `"Z-9"`
  - `prep_minutes`: `10`
- **Candidate Partners (`partners`):**
  - **Partner P-2:** Zone `"Z-1"`, `active=True`, `capacity=2`, `workload_minutes=5`, `active_order_ids=['OLD-1']`
  - **Partner P-1:** Zone `"Z-3"`, `active=True`, `capacity=2`, `workload_minutes=2`, `active_order_ids=[]`
- **Available Travel Time Matrix (`travel`):**
  - `("Z-1", "R-2")`: `8` minutes (P-2 to restaurant)
  - `("Z-3", "R-2")`: `12` minutes (P-1 to restaurant)
  - `("R-2", "Z-9")`: `12` minutes (Restaurant to customer destination)

### Step 1: Partner Eligibility & Capacity Assessment
1. **Partner P-2:**
   - Active status: `partner['active'] is True` $\to$ **Eligible**
   - Capacity check: `active_orders = 1`, `capacity = 2` ($1 < 2$) $\to$ **Eligible**
   - Route availability: Both `("Z-1", "R-2") = 8` and `("R-2", "Z-9") = 12` exist and are valid numbers $\to$ **Eligible**
2. **Partner P-1:**
   - Active status: `partner['active'] is True` $\to$ **Eligible**
   - Capacity check: `active_orders = 0`, `capacity = 2` ($0 < 2$) $\to$ **Eligible**
   - Route availability: Both `("Z-3", "R-2") = 12` and `("R-2", "Z-9") = 12` exist and are valid numbers $\to$ **Eligible**

### Step 2: ETA Calculation Trace
1. **Candidate P-2 Calculation:**
   $$\text{pickup\_minutes} = \text{now} + \text{leg1} + \text{workload} = 0 + 8 + 5 = 13\text{ minutes}$$
   $$\text{eta\_minutes} = \text{pickup} + \text{prep\_minutes} + \text{leg2} = 13 + 10 + 12 = 35\text{ minutes}$$
2. **Candidate P-1 Calculation:**
   $$\text{pickup\_minutes} = \text{now} + \text{leg1} + \text{workload} = 0 + 12 + 2 = 14\text{ minutes}$$
   $$\text{eta\_minutes} = \text{pickup} + \text{prep\_minutes} + \text{leg2} = 14 + 10 + 12 = 36\text{ minutes}$$

### Step 3: Selection Decision & Final Output
- Comparing ETA estimates: $\text{ETA}(\text{P-2}) = 35 < \text{ETA}(\text{P-1}) = 36$.
- Partner **P-2** is selected as the optimal dispatch choice.
- **Actual Result returned by `assign_order()`:**
  ```python
  {
      'order_id': 'O-7',
      'partner_id': 'P-2',
      'pickup_minutes': 13,
      'eta_minutes': 35,
      'reason': 'assigned'
  }
  ```

---

## 2. No-Eligible-Partner Example

When dispatch cannot find an eligible partner capable of fulfilling the order, the engine returns a structured unassigned response.

### Scenario: Fleet Overloaded and Missing Route Data
- **Order:** `new_order("O-99", "REST-9", "DEST-9", prep_minutes=15)`
- **Candidates Provided:**
  - **Partner A:** `active=False` (Off-duty / inactive).
  - **Partner B:** `capacity=2`, `active_order_ids=['O-1', 'O-2']` (At maximum capacity: $2 \ge 2$).
  - **Partner C:** `active=True`, `capacity=2`, `active_order_ids=[]`, located in zone `"Z-X"`.
- **Travel Map:** Contains route `("Z-X", "REST-9") = 10`, but route `("REST-9", "DEST-9")` is **missing** (deliberately omitted).

### Evaluation Breakdown:
1. **Partner A:** Skipped immediately during candidate filtering because `partner.get('active') is not True`.
2. **Partner B:** Skipped during candidate filtering because `len(active_order_ids) >= capacity` ($2 \ge 2$).
3. **Partner C:** Passes active and capacity filters. However, during `estimate_eta()`, `travel.get(('REST-9', 'DEST-9'))` evaluates to `None`. In accordance with rule 5 ("Missing travel data must never be treated as zero"), `estimate_eta()` returns `eligible: False`.
4. **Final Result:** No eligible candidates remain in `options`. The engine returns:
   ```python
   {
       'order_id': 'O-99',
       'partner_id': None,
       'eta_minutes': None,
       'reason': 'no eligible partner or missing time data'
   }
   ```

---

## 3. Three Specific Edge Cases

### Edge Case 1: Deterministic Tie-Breaking Across Identical ETAs
- **Input:**
  - Order at `"REST-1"` delivering to `"DEST-1"`.
  - Candidate 1: `Partner "P-Z"` with pickup 5, delivery travel 10 $\to$ ETA = 25 minutes.
  - Candidate 2: `Partner "P-A"` with pickup 5, delivery travel 10 $\to$ ETA = 25 minutes.
- **Expected Behaviour:** Tie must be broken deterministically by partner ID in ascending lexicographical order (`"P-A"` before `"P-Z"`), regardless of input list sequence (`[P-Z, P-A]` vs. `[P-A, P-Z]`).
- **Actual Result:** `result['partner_id'] == 'P-A'`.
- **Test Evidence:** `tests/test_contract.py::test_tie_break_by_partner_id` and `tests/test_acceptance_matrix.py::test_ties_break_by_partner_id_independent_of_input_order`.

### Edge Case 2: Idempotent Handling of Duplicate Cancellation Events
- **Input:**
  - Partner has active order `"O1"` contributing `9` minutes to `workload_minutes`.
  - Cancellation event `"C1"` for order `"O1"` is received twice consecutively.
- **Expected Behaviour:**
  - Event 1: Releases order `"O1"`, subtracts 9 minutes from workload (workload becomes 0), records `"C1"` in `processed_cancellation_ids`.
  - Event 2: Recognizes `"C1"` as already processed. State remains unmodified (workload stays 0, not decremented below 0, `"C1"` not recorded twice).
- **Actual Result:** `twice['workload_minutes'] == 0` and `twice['processed_cancellation_ids'] == ['C1']`.
- **Test Evidence:** `tests/test_contract.py::test_duplicate_cancellation_is_idempotent`.

### Edge Case 3: Rejection of Invalid Preparation Time Types
- **Input:**
  - Order initialized with `prep_minutes=True` or `prep_minutes=float('nan')`.
- **Expected Behaviour:**
  - `True` must NOT be coerced to `1` minute.
  - `NaN` must NOT produce a `NaN` ETA that bypasses comparisons.
  - Candidate is marked ineligible, and order remains unassigned.
- **Actual Result:** `result['partner_id'] is None` and `result['eta_minutes'] is None`.
- **Test Evidence:** `tests/test_acceptance_matrix.py::test_preparation_time_validation[True]`, `[nan]`.

---

## 4. Key Assumptions and System Limitations

1. **Deterministic Lexicographical Tie-Breaking:**  
   When two candidates yield identical minimum ETA minutes, ties are resolved strictly by `str(partner_id)` ascending. This ensures full reproducibility across distributed runs.
2. **Workload Accounting & Non-Negative Invariance:**  
   Workload reductions during cancellation utilize `max(0, workload - order_minutes)`, guaranteeing that workload minutes can never become negative even if upstream records are slightly desynchronized.
3. **Unit Consistency:**  
   All time inputs (`now`, `prep_minutes`, travel legs, `workload_minutes`) are assumed to represent consistent units (minutes) and are validated as non-negative finite numeric quantities.
4. **Cancellation Scope:**  
   `process_cancellation()` operates on partner state. An event ID is considered duplicate only if that specific `event_id` was previously recorded for that partner.

---
*End of DISPATCH_NOTES.md*
