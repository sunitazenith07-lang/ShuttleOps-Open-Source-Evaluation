# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
 . python -m pip install -r requirements-dev.txt
 . python -m pytest-q
 . python -m main
- Initial test result (include the actual summary):
 . 164 passed
 . 65 failed
- Demo/output observed:
 . {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}

## 2. Codebase understanding
- Important files/functions inspected:
  . service.py
  . models.py
  . fixtures.py
  . main.p.
  . tests/test_contact.py
  . tests/test_acceptance_matrix.py
  . tests/test_edge_cases.py
- Candidate filtering, ETA calculation, and capacity flow traced:
  . ETA is calculated using: Pickup Time = Current Time  + Partner-to-Restaurant Travel + Workload
    ETA = Pickup Time + Preparation Time + Restaurant-to-Customer Travel
  . Partners must be active and below capacity to be considered.
- How you confirmed your understanding:
  . Reviewed the acceptance requirements.
  . Compared expected results in tests with current implementation
  . Traced estimate_eta(), assign_order(), and process_cancellation().

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1:
  . Symptom: Invalid travel times, preparation times, and current time values were accepted.
  . Evidence: Multiple failures in test_invalid_or_missing_travel_time_rejected and                     test_preparation_time_validation.
  . Fix: Added validation helpers to reject invalid, negative, non-finite, and boolean values.
- Issue 2:
  . Symptom: Inactive partners and full-capacity partners were still assigned orders.
  . Evidence: Failures in test_inactive_partner_not_assigned and test_capacity_boundary_matrix.
  . Fix: Added strict active-partner and capacity checks before ETA calculation.
- Issue 3 (if applicable):
  . Symptom: Duplicate cancellation events were processed multiple times.
  . Evidence: Failures in test_duplicate_cancellation_is_idempotent.
  . Fix: Ignored cancellation events that had already been processed.

## 4. Implementation decisions
- Main changes and why:
  . Added reusable validation helpers.
  . Added order validation before assignment.
  . Added partner eligibility filtering.
  . Added idempotent cancellation handling.
  . Preserved deterministic assignment through ETA sorting and tie-breaking.
- Alternatives considered and why rejected:
  . Converting invalid values automatically was rejected because the requirements state invalid         data must be rejected.
  . Using default values for missing travel times was rejected because missing travel data must not     be treated as zero.
- Assumptions:
  . Active status must be exactly True.
  . Capacity must be a positive integer.
  . Travel and preparation times must be finite, non-negative numbers.
## 5. Verification
- Tests added or changed:
  . Used the provided acceptance and contract tests to verify fixes.
- Commands run and actual results:
  . python -m pytest -q
  . Result: 229 passed, 0 failed
- Edge cases verified:
  . Missing travel-time records.
  . Negative preparation times.
  . Invalid IDs.
  . Full-capacity partners.
  . Duplicate cancellation events.
- Remaining failures or known limitations:
  . No known test failures after implementation.
Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.