# DISPATCH_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked ETA example

Order `O-7` is going from restaurant `R-2` to zone `Z-9`. It needs 10 minutes of restaurant preparation.

Partner `P-2` starts in zone `Z-1`, has 5 minutes of remaining workload, and needs 8 minutes to reach the restaurant. The restaurant-to-customer trip is 12 minutes. Current time in the example is `0`.

- Pickup time: `0 + 8 + 5 = 13`
- ETA: `13 + 10 + 12 = 35`
- Actual demo result: partner `P-2`, pickup time `13`, ETA `35`, reason `assigned`.

## 2. No-eligible-partner example

Order `O-8` needs a trip from `R-2` to `Z-9`. The only candidate, `FULL`, has capacity `1` and already has one active order. Even though both travel times are present, the partner is at capacity.

Actual result from the check: `partner_id` is `None`, `eta_minutes` is `None`, and the reason is `no eligible partner or missing time data`.

## 3. Three edge cases

1. **Negative travel time:** Travel times `-1` and `1` should make the ETA ineligible. The travel-time validation test passed.
2. **Full partner:** Capacity `1` with one active order should not be assigned another order. The capacity boundary test passed.
3. **Repeated cancellation:** Processing event `C` twice should not add `C` twice or release the order twice. The duplicate cancellation test passed.

## 4. Assumptions and limitations

- ETA ties are broken by partner ID in ascending string order.
- Missing required travel data makes a partner ineligible; it is not treated as zero minutes.
- Capacity is expected to be a positive integer, and `active_order_ids` is expected to be a list.
- A cancellation only removes workload when its order ID is currently active. Repeated event IDs are ignored, and workload is not reduced below zero.
- Orders marked `CANCELLED` are not assigned. Dataset tests also cover cancellation records with missing event IDs.
- The supplied 180 order records and 177 cancellation events were exercised in dataset integration tests. Hidden tests are not available in the repository.
