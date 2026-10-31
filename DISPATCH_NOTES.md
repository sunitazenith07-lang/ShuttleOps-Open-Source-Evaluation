# DISPATCH_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked ETA example
Show an order, the candidate partner, partner-to-restaurant travel time, remaining workload, restaurant preparation time, restaurant-to-customer travel time, the ETA calculation, and the actual result.

- **Order (`order`)**:
  ```python
  {'order_id': 'O-7', 'restaurant_id': 'R-2', 'destination_zone': 'Z-9', 'prep_minutes': 10}
  ```
- **Candidate Partner (`p2` from `fixtures.py`)**:
  ```python
  {
      'partner_id': 'P-1',
      'zone': 'Z-3',
      'active': True,
      'capacity': 2,
      'active_order_ids': [],
      'workload_minutes': 2,
      'minutes_by_order': {},
      'processed_cancellation_ids': []
  }
  ```
- **Time Components (`now = 0`)**:
  - **Partner-to-restaurant travel time (`leg1` for `('Z-3', 'R-2')`)**: $12\text{ minutes}$
  - **Remaining workload (`workload_minutes`)**: $2\text{ minutes}$
  - **Restaurant preparation time (`prep_minutes`)**: $10\text{ minutes}$
  - **Restaurant-to-customer travel time (`leg2` for `('R-2', 'Z-9')`)**: $12\text{ minutes}$
- **ETA Calculation**:
  - $\text{Pickup Time} = \text{now} + \text{leg1} + \text{workload\_minutes} = 0 + 12 + 2 = 14\text{ minutes}$
  - $\text{ETA} = \text{Pickup Time} + \text{prep\_minutes} + \text{leg2} = 14 + 10 + 12 = 36\text{ minutes}$
- **Actual Result**:
  - Output from `estimate_eta(order, p2, travel, now=0)`:
    ```python
    {'partner_id': 'P-1', 'pickup_minutes': 14, 'eta_minutes': 36, 'eligible': True}
    ```
  - Output from `assign_order(order, [p1, p2], travel, now=0)` (where `p1` is `'P-2'` who also has an ETA of $36\text{ minutes}$, so `'P-1'` wins the lexicographic tie-break):
    ```python
    {'order_id': 'O-7', 'partner_id': 'P-1', 'pickup_minutes': 14, 'eta_minutes': 36, 'reason': 'assigned'}
    ```

## 2. No-eligible-partner example
Show why each candidate is ineligible (for example, capacity reached or required travel-time data missing) and how the service reports the order as unassigned.

- **Order (`order`)**:
  ```python
  {'order_id': 'O-7', 'restaurant_id': 'R-2', 'destination_zone': 'Z-9', 'prep_minutes': 10}
  ```
- **Travel Table (`travel`)**:
  ```python
  {('Z-1', 'R-2'): 8, ('R-2', 'Z-9'): 12}
  ```
- **Candidate Partners (`partners`) & Why Each is Ineligible**:
  1. **Partner `'P-1'` (`zone='Z-1', active=False, capacity=2, active_order_ids=[]`)**:
     - **Why ineligible**: Partner is inactive (`partner.get('active') is not True`), so `assign_order` skips them before calculating an ETA.
  2. **Partner `'P-2'` (`zone='Z-1', active=True, capacity=2, active_order_ids=['O-1', 'O-2']`)**:
     - **Why ineligible**: Partner has reached capacity (`len(active_order_ids) == 2 >= capacity`), so `assign_order` skips them.
  3. **Partner `'P-3'` (`zone='Z-5', active=True, capacity=2, active_order_ids=[]`)**:
     - **Why ineligible**: Required travel-time entry `('Z-5', 'R-2')` is missing from `travel` (`leg1 is None`). Missing travel times are never treated as zero, so `estimate_eta` returns `{'partner_id': 'P-3', 'eta_minutes': None, 'eligible': False}`.
- **How the Service Reports the Order as Unassigned**:
  - When `options` is empty after evaluating all candidates, `assign_order` returns:
    ```python
    {
        'order_id': 'O-7',
        'partner_id': None,
        'eta_minutes': None,
        'reason': 'no eligible partner or missing time data'
    }
    ```

## 3. Three edge cases
For each, state input, expected behaviour, actual observed result, and test that verifies it.

1. **Infinite (`float('inf')`) or Boolean (`True`/`False`) Time Values**
   - **Input**: An order with `prep_minutes = float('inf')` (or a travel matrix with leg time `float('inf')`, or `prep_minutes = True`).
   - **Expected Behaviour**: Although `float('inf') >= 0` and `isinstance(True, int)` evaluate to `True` in Python, non-finite floats and booleans must be rejected as invalid time values, marking the ETA ineligible (`'eligible': False`) and leaving the order unassigned (`'partner_id': None`).
   - **Actual Observed Result**: `_is_non_neg_num` checks `not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0`. `estimate_eta` returns `{'partner_id': 'P-1', 'eta_minutes': None, 'eligible': False}` and `assign_order` returns `{'order_id': 'O-7', 'partner_id': None, 'eta_minutes': None, 'reason': 'invalid order or time data'}` (or `'no eligible partner or missing time data'` when travel leg is `inf`).
   - **Verifying Tests**: `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-inf]` and `tests/test_acceptance_matrix.py::test_preparation_time_validation[inf]`.

2. **Duplicate Cancellation Event (Idempotency)**
   - **Input**: Partner `'P-1'` has `active_order_ids = ['O-1', 'O-2']`, `workload_minutes = 20`, `minutes_by_order = {'O-1': 12, 'O-2': 8}`, and `processed_cancellation_ids = []`. We call `process_cancellation(partner, 'O-1', 'EVT-100')` twice with the same `'EVT-100'` event ID.
   - **Expected Behaviour**: The first call removes `'O-1'`, reduces `workload_minutes` from $20$ to $8$, and records `'EVT-100'` in `processed_cancellation_ids`. The second call with `'EVT-100'` must detect the duplicate event ID and return the partner state unchanged without deducting workload a second time.
   - **Actual Observed Result**: After both calls, `active_order_ids` is `['O-2']`, `workload_minutes` remains `8`, and `processed_cancellation_ids` is `['EVT-100']` (single entry, no double deduction).
   - **Verifying Test**: `tests/test_acceptance_matrix.py` (cancellation idempotency test cases).

3. **ETA Tie-Breaking Between Multiple Eligible Partners**
   - **Input**: Order `'O-7'` from `sample_inputs()` where partner `'P-2'` (`zone='Z-1'`, `leg1=8`, `workload=5` $\rightarrow$ `pickup=13`, `eta=35` or with `workload=6` $\rightarrow$ `pickup=14`, `eta=36`) and partner `'P-1'` (`zone='Z-3'`, `leg1=12`, `workload=2` $\rightarrow$ `pickup=14`, `eta=36`) both produce the exact same `eta_minutes = 36`, with `'P-2'` listed before `'P-1'` in the input list.
   - **Expected Behaviour**: Ties in `eta_minutes` must be broken deterministically by `partner_id` in ascending lexicographic order (`'P-1' < 'P-2'`), regardless of partner order in the input list.
   - **Actual Observed Result**: `assign_order` selects `'P-1'` and returns `{'order_id': 'O-7', 'partner_id': 'P-1', 'pickup_minutes': 14, 'eta_minutes': 36, 'reason': 'assigned'}`.
   - **Verifying Test**: `tests/test_acceptance_matrix.py` (deterministic tie-break test cases).

## 4. Assumptions and limitations
Document tie-breaking, workload accounting, cancellation idempotency, and any unresolved issue.

- **Tie-Breaking**:
  - Candidates are ranked using the tuple `(item['eta_minutes'], str(item['partner_id']))`. Lowest `eta_minutes` wins; exact ties are broken by comparing stringified `partner_id` values in standard ASCII/lexicographic ascending order (e.g., `'P-1'` precedes `'P-2'`, and `'P-10'` precedes `'P-2'`).
- **Workload Accounting**:
  - During ETA estimation, a partner's existing `workload_minutes` is added sequentially to `now + leg1` to compute `pickup_minutes`, and `prep_minutes` is added sequentially (`pickup_minutes + prep_minutes + leg2`) as required by the specification.
  - During cancellation, the cancelled order's workload is looked up via `minutes_by_order.get(order_id, 0)` and subtracted from `workload_minutes`, floored at `0` using `max(0, ...)` so workload can never become negative even if `minutes_by_order` contains inconsistent numbers.
  - `assign_order` is a pure decision function: it returns the chosen partner and ETA dictionary without mutating the chosen partner's `active_order_ids` or `workload_minutes` in place.
- **Cancellation Idempotency**:
  - `process_cancellation` deep-copies the input partner dictionary (`copy.deepcopy`) so the caller's dictionary is never mutated in place.
  - Every valid `event_id` is checked against `processed_cancellation_ids` before modifying state. If `event_id` is already present (or is not a valid non-empty string), the function returns the copy immediately without modifying `active_order_ids` or `workload_minutes`.
- **Unresolved Issues / Limitations**:
  - All state is held in memory using plain dictionaries and lists; `processed_cancellation_ids` grows linearly ($O(N)$ lookup per cancellation event) over the lifetime of a partner object.
  - Dispatch is greedy per single order and does not globally optimize assignments across a batch of concurrent orders.