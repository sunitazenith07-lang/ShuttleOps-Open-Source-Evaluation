# Challenges

## Validation without changing the public API

The visible failures mixed wrong assignments with `TypeError` exceptions. For example, text travel times reached arithmetic, and invalid preparation times were accepted or crashed. The baseline result, 65 failures, and `test_invalid_or_missing_travel_time_rejected` made this reproducible.

I first mapped which values belong to an order, a partner, and a route. The resolution was to validate values at the boundary of `estimate_eta()` and keep its established result shape for invalid data: `eligible` is false and ETA is `None`. Assignment adds availability checks because ETA alone should not decide capacity or active status.

The other tricky case was cancellation idempotency. The original code released an order only once because the ID was removed, but still recorded the duplicate event. Checking `processed_cancellation_ids` before any change fixes both the duplicate record and the risk of future repeated side effects. `test_duplicate_cancellation_is_idempotent` and the added non-mutation test protect this behaviour.

There were no unresolved test failures. Concurrency remains outside this small in-memory API; a production caller would need an atomic reservation around selection and assignment.
