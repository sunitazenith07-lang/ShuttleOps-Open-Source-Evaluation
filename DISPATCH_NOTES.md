# DISPATCH_NOTES.md — Dispatch Engine Operational Notes

## 1. Worked ETA example
### Inputs:
- **Order:**
  ```python
  order = {
      'order_id': 'O-7',
      'restaurant_id': 'R-2',
      'destination_zone': 'Z-9',
      'prep_minutes': 10
  }
  ```
- **Candidate Delivery Partner:**
  ```python
  partner = {
      'partner_id': 'P-2',
      'zone': 'Z-1',
      'active': True,
      'capacity': 2,
      'active_order_ids': ['OLD-1'],
      'workload_minutes': 5
  }
  ```
- **Current Simulation Time (`now`):** `0`
- **Travel Matrix Entries:**
  - Partner-to-restaurant leg (`('Z-1', 'R-2')`): `8` minutes
  - Restaurant-to-customer leg (`('R-2', 'Z-9')`): `12` minutes

### Step-by-Step Calculation:
1. **Eligibility Check:**
   - Active status: `partner['active'] is True` (Passed)
   - Capacity: `capacity = 2`, `len(active_order_ids) = 1` ($1 < 2$) (Passed)
   - Route availability: Both legs present in travel matrix with non-negative numbers (Passed)
2. **Pickup Time Calculation:**
   $$\text{Pickup Time} = \text{now} + \text{leg1} + \text{workload} = 0 + 8 + 5 = 13\text{ minutes}$$
3. **Delivery ETA Calculation:**
   $$\text{ETA} = \text{Pickup Time} + \text{Prep Time} + \text{leg2} = 13 + 10 + 12 = 35\text{ minutes}$$
4. **Actual Observed Result:**
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

## 2. No-eligible-partner example
### Scenario:
An order is submitted for dispatch, but all delivery partners in the system are ineligible.

### Inputs:
- **Order:**
  ```python
  order = {
      'order_id': 'ORD-FAIL-1',
      'restaurant_id': 'REST-A',
      'destination_zone': 'ZONE-CUSTOMER',
      'prep_minutes': 15
  }
  ```
- **Candidates Evaluated:**
  1. `PARTNER-101`: `active = False` (Partner off-duty / inactive).
  2. `PARTNER-102`: `capacity = 2`, `active_order_ids = ['ORD-91', 'ORD-92']` (Partner at max order capacity: $2 \ge 2$).
  3. `PARTNER-103`: `active = True`, `capacity = 2`, `zone = 'ZONE-REMOTE'`, but travel route `('ZONE-REMOTE', 'REST-A')` is missing from the travel dictionary.
- **Travel Matrix:** Missing route between `ZONE-REMOTE` and `REST-A`.

### Decision Trace:
- `PARTNER-101` is pruned immediately during candidate filtering because `partner.get('active') is not True`.
- `PARTNER-102` is pruned because `len(active_order_ids) >= capacity`.
- `PARTNER-103` passes initial filters, but `estimate_eta` discovers that `travel.get(('ZONE-REMOTE', 'REST-A'))` is `None`. Missing travel times must never be assumed as zero, so `eligible` evaluates to `False`.

### Actual Observed Output:
```python
{
    'order_id': 'ORD-FAIL-1',
    'partner_id': None,
    'eta_minutes': None,
    'reason': 'no eligible partner or missing time data'
}
```

---

## 3. Three edge cases

### Case 1: Special Non-Numeric Values in Travel Times (`NaN` / `Inf` / `bool`)
- **Input:**
  - `travel = {('ZONE-A', 'REST-1'): float('nan'), ('REST-1', 'DEST-1'): 10}`
  - `order = {'order_id': 'O-1', 'restaurant_id': 'REST-1', 'destination_zone': 'DEST-1', 'prep_minutes': 10}`
  - `partner = {'partner_id': 'P-1', 'zone': 'ZONE-A', 'active': True, 'capacity': 2}`
- **Expected Behaviour:** Reject `NaN` as an invalid route time; do not compute an invalid NaN float or crash.
- **Actual Result:** `{'partner_id': 'P-1', 'eta_minutes': None, 'eligible': False}`
- **Test:** `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[nan-1]`

### Case 2: Deterministic Tie-Breaking with Identical ETAs
- **Input:**
  - Two eligible partners `PARTNER-Z` and `PARTNER-A` both in zones yielding identical total ETA = 30 minutes.
  - Candidates passed in order `[PARTNER-Z, PARTNER-A]`.
- **Expected Behaviour:** Break the ETA tie by partner ID in ascending lexicographical order (`'PARTNER-A' < 'PARTNER-Z'`).
- **Actual Result:** Selected partner is `'PARTNER-A'`, not `'PARTNER-Z'`.
- **Test:** `tests/test_contract.py::test_tie_break_by_partner_id` and `tests/test_acceptance_matrix.py::test_ties_break_by_partner_id_independent_of_input_order`

### Case 3: Cancellation Idempotency and Workload Clamping Underflow
- **Input:**
  - Partner with `workload_minutes = 5`, `minutes_by_order = {'O-1': 10}` (order estimated minutes exceed recorded workload).
  - Cancellation event `event_id = 'C-01'` invoked twice sequentially.
- **Expected Behaviour:**
  1. First cancellation removes `'O-1'`, reduces workload to 0 (clamped, never negative), records `'C-01'`.
  2. Second duplicate cancellation detects `'C-01'` in `processed_cancellation_ids` and makes no modifications.
- **Actual Result:** `workload_minutes = 0`, `active_order_ids = []`, `processed_cancellation_ids = ['C-01']`.
- **Test:** `tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads` and `tests/test_regression.py::test_regression_cancellation_idempotency_and_clamping`

---

## 4. Assumptions and limitations
1. **Deterministic Tie-Breaking:** Ties are resolved strictly by ascending lexicographical comparison of `partner_id` converted to string (`str(item['partner_id'])`), ensuring identical selection regardless of candidate iteration order.
2. **Workload Accounting:** Workload minutes represent remaining committed time for in-flight deliveries. When an order is completed or cancelled, its allocated minutes are subtracted, clamped at a lower bound of `0`.
3. **Cancellation Idempotency:** Every cancellation event must supply an `event_id`. A partner tracks `processed_cancellation_ids` so duplicate event submissions are ignored.
4. **Unknown IDs and Malformed Records:** Orders with non-string, empty, or None IDs, or negative preparation times are safely rejected with `partner_id: None` and a descriptive failure `reason`.
5. **Route Completeness:** Missing travel routes are never defaulted to zero or inferred; missing data is treated as unknown, rendering that specific candidate ineligible.
