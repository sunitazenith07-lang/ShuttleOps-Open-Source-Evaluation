# Optimizations — SmartDispatch

## 1. Baseline and objective

The main objective was correctness and maintainability, not raw speed. The
starter implementation was small, but it accepted invalid time values, did not
filter inactive or full partners, and did not protect cancellation processing
from duplicate events. The baseline run of `python -m pytest -q` reported **65
failed, 164 passed**. That is evidence of missing behavior, not evidence of a
performance bottleneck.

I did not run a benchmark or profile the program. The final passing test run
reported 229 tests in 0.41 seconds, but a single pytest duration is not a
controlled before-and-after performance measurement, so I make no speedup
claim.

## 2. Options considered

1. **Validate once in `assign_order` or validate in both public functions.**
   Keeping validation only in assignment would avoid repeated checks there,
   but direct calls to `estimate_eta` could still accept invalid input.
   Validation only in the estimator would not check assignment-specific
   partner capacity and activity. I used small shared validation helpers and
   kept candidate eligibility checks in `assign_order`, so both entry points
   enforce the rules relevant to them.

2. **Sort every candidate by ETA or select the minimum.** Sorting would make
   the full candidate order available, but assignment needs only one winner.
   The implementation retains a single minimum-selection pass using ETA and
   partner ID as the key. It does not sort the candidate list.

3. **Track processed cancellation IDs in a set.** A set can make membership
   checks faster for large histories, but the partner record and existing
   contract represent processed IDs as a list, and result ordering is
   observable. Replacing it would require changing the record shape or
   maintaining two structures. I kept the list-based representation because
   the challenge data and tests do not establish that cancellation-history
   lookup is a bottleneck.

4. **Build a separate indexed or cached travel-time structure.** This could
   help if many orders repeatedly use a large route table, but the current
   function receives a mapping and performs only two direct lookups per
   candidate. There is no measured workload demonstrating that conversion or
   caching would help, so I did not add it.

## 3. Changes implemented

- **Shared input checks:** Added `_is_nonnegative_number`,
  `_is_valid_identifier`, and `_is_valid_order` to make validation rules
  consistent and avoid repeating the same detailed checks inline. This is a
  maintainability and correctness choice; I did not measure a runtime
  improvement.
- **Reject invalid ETA inputs early:** Invalid order, partner-zone, workload,
  current-time, travel mapping, or route values stop calculation before
  arithmetic. Calculated pickup and ETA values are also checked before
  returning an eligible estimate.
- **Filter candidates before estimating:** `assign_order` excludes inactive,
  malformed, and at-capacity partners before route lookup and ETA calculation.
  This avoids unnecessary calculations for candidates already known to be
  ineligible, while ensuring the assignment follows the capacity contract.
  No timing measurement was performed.
- **Retain a single-pass winner selection:** The candidate estimates are
  reduced with `min` using `(eta_minutes, partner_id)`. This gives the required
  stable tie-break without sorting all candidates.
- **Make cancellation application idempotent:** A previously processed event
  is returned without applying its order removal or workload subtraction
  again. This prevents a correctness failure; it is not presented as a
  performance optimization.
- **Correctness tests:** I did not add or modify tests. The supplied test suite
  covers ETA formulas, invalid and missing times, eligibility, capacity,
  deterministic tie-breaking, duplicate cancellation, and workload clamping.

## 4. Trade-offs

- The helper functions add a few lines but centralize rules that otherwise
  could diverge between direct ETA estimates and order assignment.
- Building an `options` list before calling `min` uses memory proportional to
  the number of eligible partners. An incremental best-candidate loop could
  reduce this temporary storage, but the current code is straightforward,
  considers each candidate once, and no large partner workload or memory
  constraint was measured.
- Cancellation history membership remains a linear list lookup. This preserves
  the current data representation and deterministic output. If histories
  become very large, a set-backed internal representation could be evaluated
  with compatibility and serialization requirements in mind.
- Strict validation intentionally rejects booleans as times even though
  Python treats `bool` as a subclass of `int`. This avoids accepting
  `True`/`False` as minute values and is covered by the acceptance tests.

## 5. Further improvements

- **Benchmark realistic dispatch sizes:** Generate representative partner and
  route counts, measure total assignment time and memory for repeated runs,
  and compare the current implementation with an incremental winner-selection
  loop. Keep the simpler version unless measurements show a meaningful gain.
- **Profile cancellation history sizes:** Measure event processing with
  realistic and unusually large histories. Only if list membership is shown
  to dominate should a set-backed or indexed representation be considered;
  validate that output format and event ordering remain compatible.
- **Validate broader malformed records:** Add contract tests for malformed
  top-level inputs and cancellation records as the accepted API schema becomes
  more explicit. Keep validation behavior aligned with documented caller
  expectations instead of silently inventing defaults.
- **Run the demo and full test suite after any future optimization:** An
  optimization should preserve ETA arithmetic, tie-breaking, partner
  eligibility, input immutability during cancellation, and idempotent event
  handling. Performance claims should be based on repeatable benchmark
  results, not just test-suite execution time.
