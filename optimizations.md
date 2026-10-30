# Optimizations

## Done
- **Single source of validation rules.** `_is_valid_id`, `_is_valid_time` and
  `_is_valid_capacity` replace scattered checks, so every time value is validated
  identically.
- **Cheap checks first.** Active and capacity filters run before `estimate_eta`, so
  ineligible partners cost no route lookups.
- **One-pass deterministic selection.** `min()` with key `(eta_minutes, str(partner_id))`
  is O(n) and independent of input order.
- **Explainability at no extra cost.** Rejection reasons are collected during the same
  loop and returned in `details`, so the no-eligible case explains itself.
- **No mutation of inputs.** `process_cancellation` works on a `deepcopy`, so repeated
  calls are deterministic.

## Possible next steps (not done)
- Replace `deepcopy` with a shallow copy of the dict and its two lists and the one
  dict; it would be cheaper for large partner records.
- Precompute per-restaurant lookups if the partner list becomes large.
- Stretch items (batch assignment in priority order, ETA recalculation after a prep
  change) were deliberately skipped so the required behaviour came first.
