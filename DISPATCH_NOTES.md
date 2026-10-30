DISPATCH_NOTES.md — Dispatch Behaviour

1. Worked ETA Example

Example input:

* Partner ID: P1
* Partner zone: Z1
* Restaurant ID: R1
* Destination zone: D1
* Partner-to-restaurant travel time: 8 minutes
* Partner workload: 0 minutes
* Preparation time: 10 minutes
* Restaurant-to-destination travel time: 12 minutes
* Current time: 0

Calculation:

* Pickup time = 0 + 8 + 0 = 8 minutes
* ETA = 8 + 10 + 12 = 30 minutes

Expected result: Partner P1 is eligible, pickup time is 8 minutes, and ETA is 30 minutes.

2. No-Eligible-Partner Example

If every partner is inactive, at full capacity, or has missing or invalid travel-time data, the order must remain unassigned.

Expected result:

* partner_id: None
* eta_minutes: None
* A reason explaining that no eligible partner or valid travel data is available.

3. Edge Cases

Case	Expected behaviour	Verification
Missing travel route	Partner is ineligible	Automated tests passed
Partner at full capacity	Partner is not assigned	Automated tests passed
Duplicate cancellation event	Workload is released only once	Automated tests passed

4. Assumptions

* workload_minutes represents the partner’s remaining workload.
* minutes_by_order stores workload associated with individual active orders.
* A partner is eligible only when active and below capacity.
* Missing travel-time entries are treated as unavailable, not as zero.
* Lowest ETA wins; equal ETAs are resolved using ascending lexicographical partner ID.
* A cancellation event must not be applied more than once.

5. Limitations

* Travel times come from the supplied synthetic data.
* The implementation does not use live GPS or traffic information.
* Real-world travel times may differ from the supplied estimates.