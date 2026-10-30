# 🚚 Dispatch Notes

## 1. Worked ETA example

The offline demo creates order O-7 for restaurant R-2 and destination zone Z-9. Restaurant preparation takes 10 minutes. The demo starts at time 0.

| Candidate | Partner zone | Workload | To restaurant | Restaurant to destination | Pickup | ETA |
|---|---|---:|---:|---:|---:|---:|
| P-2 | Z-1 | 5 min | 8 min | 12 min | 0 + 8 + 5 = 13 | 13 + 10 + 12 = **35 min** |
| P-1 | Z-3 | 2 min | 12 min | 12 min | 0 + 12 + 2 = 14 | 14 + 10 + 12 = **36 min** |

The service assigns O-7 to P-2. Its ETA is lower. The observed demo output reports pickup at minute 13 and ETA at minute 35.

## 2. Example with no eligible partner

The full-capacity contract case creates an order with ID O, restaurant R, and destination D. Partner P has capacity 1 and already has active order A. Both travel entries are available and equal 1 minute, but the partner has no remaining slot.

Expected and tested behavior: the order remains unassigned and partner_id is None. Evidence: test_full_partner_not_assigned and test_capacity_boundary_matrix. The final visible suite passed these tests.

## 3. Edge cases

1. **Missing travel route:** If either required route is absent, no reliable ETA can be calculated. The candidate is ineligible and eta_minutes is None. Evidence: test_missing_travel_is_not_zero and test_eta_is_ineligible_when_either_required_route_is_missing.
2. **Invalid time input:** Negative or malformed travel, preparation, or current-time values must not produce an ETA or crash the calculation. Evidence: test_invalid_or_missing_travel_time_rejected, test_preparation_time_validation, and test_current_time_validation.
3. **Duplicate cancellation:** Sending the same cancellation event ID twice must remove the order and subtract its workload only once. Evidence: test_duplicate_cancellation_is_idempotent and test_duplicate_cancellation_is_idempotent_across_workloads.

All named tests passed in the final visible test run (233 passed total). A regression test also converts the expanded dataset travel rows into the tuple-key mapping and verifies one complete eligible route.

## 4. Assumptions and limitations

- ETA ties are settled by ascending lexicographic partner ID.
- Pickup time includes current time, travel to the restaurant, and the partner's remaining workload.
- Capacity is checked by comparing active order count with a positive integer capacity.
- A processed cancellation event ID is not applied again; cancellation handling returns a deep-copied partner record.
- Data is synthetic. The project does not integrate live GPS, maps, or real delivery records.
- The visible test suite passes. Pull-request CI and hidden evaluation checks remain pending.
