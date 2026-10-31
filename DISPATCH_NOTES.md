# Dispatch notes

The ETA is worked out in two steps:

```text
Pickup time = current time + trip to restaurant + partner workload
ETA = pickup time + food preparation time + trip to customer
```

## 1. Worked ETA example

This example uses the demo order `O-7` with `now = 5`.

- Restaurant: `R-2`
- Destination: `Z-9`
- Preparation time: 10 minutes
- Trip from `Z-1` to `R-2`: 8 minutes
- Trip from `Z-3` to `R-2`: 12 minutes
- Trip from `R-2` to `Z-9`: 12 minutes

Both partners are active and have room for another order.

| Partner | Workload | Pickup calculation | ETA calculation |
|---|---:|---|---|
| P-2, in zone Z-1 | 5 min | 5 + 8 + 5 = 18 | 18 + 10 + 12 = 40 min |
| P-1, in zone Z-3 | 2 min | 5 + 12 + 2 = 19 | 19 + 10 + 12 = 41 min |

**Actual result:** `assign_order` chose `P-2`, with pickup time 18 and ETA 40. It chose P-2 because its ETA was lower, even though P-2 had more workload. The `python -m main` demo uses `now = 0`; its recorded result is also P-2, with pickup time 13 and ETA 35.

## 2. No-eligible-partner example

Order `O-99` needs a trip from restaurant `R` to destination `D`. The available travel data is `{(Z1, R): 3, (Z2, R): 4, (R, D): 10}`.

- Partner A is inactive, so it cannot be selected.
- Partner B has capacity 1 and already has one active order, so it is full.
- Partner C is active and has space, but there is no travel time from `Z3` to `R`.

**Actual result:** the service returned `partner_id: None` and `eta_minutes: None`. It listed each partner's reason: not active, at capacity, or missing travel-time data. It did not treat the missing route as zero minutes.

The project notes also record a dataset example: order `DSP-ORD-0001` is unassigned because its `REST-101` to `DEST-01` route is missing. All 60 partners are rejected for that order.

## 3. Three edge cases

### 1. Negative preparation time

- **Input:** Order `O-1` has preparation time `-5`; the partner and routes are otherwise valid.
- **Expected:** Reject the order and do not calculate an ETA.
- **Actual:** The service returned no partner and the reason `invalid order: invalid or missing prep_minutes`.
- **Test:** `test_negative_prep_time_is_rejected` and `test_preparation_time_validation`.

### 2. Same cancellation sent twice

- **Input:** Partner P has order `O1`, workload 9, and `minutes_by_order` says O1 uses 9 minutes. The same cancellation ID, `C1`, is sent twice.
- **Expected:** Remove the order and its workload once, and record `C1` once.
- **Actual:** The order list became empty, workload became 0, and the processed ID list was `['C1']`.
- **Test:** `test_duplicate_cancellation_is_idempotent` and `test_duplicate_cancellation_is_idempotent_across_workloads`.

### 3. Invalid travel time

- **Input:** The trip from the restaurant to the customer is `NaN` (not a real number that can be used in an ETA).
- **Expected:** Do not use this route; mark the partner as ineligible.
- **Actual:** The service returned `eligible: False`, `eta_minutes: None`, and the reason `invalid travel-time data`.
- **Test:** `test_invalid_or_missing_travel_time_rejected`.

## 4. Assumptions and limitations

- **Tie-breaking:** The lowest ETA wins. If two partners have the same ETA, the smaller partner ID in alphabetical order wins. For example, `P10` comes before `P2`.
- **Partner checks:** A partner must have `active` set to exactly `True` and must have space below its capacity.
- **Workload:** When an active order is cancelled, its saved minutes are removed from the partner's workload. Workload is not allowed to go below zero. The cancelled order's minutes are also removed from `minutes_by_order`.
- **Repeated cancellations:** The event ID is used to recognize a repeated cancellation. Events without an ID are ignored because they cannot be reliably recognized as repeats.
- **Limitations:** The assignment function chooses a partner but does not update that partner's workload or active order list. It also does not check an order's status. The code has no overall record connecting every order to its assigned partner, so it cannot check whether a cancellation was sent to the right partner.
