# Testing

## Environment
Python Version: 3.x

## Commands Executed

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

## Baseline Results

Before any changes:

```text
164 passed
65 failed
```

## Final Results

After implementing the fixes:

```text
229 passed
0 failed
```

## Test Coverage

The following areas were verified:
- ETA calculation
- Travel-time validation
- Preparation-time validation
- Partner eligibility
- Capacity handling
- Tie-breaking
- Cancellation processing

## Edge-Case Tests

### Edge Case 1: Missing Travel-Time Data
- **Input:** Travel-time data is missing.
- **Expected:** The partner is ineligible.
- **Actual:** The partner is rejected correctly.

### Edge Case 2: Negative Preparation Time
- **Input:** Preparation time is negative.
- **Expected:** The order is rejected.
- **Actual:** The order is rejected correctly.

### Edge Case 3: Inactive Partner
- **Input:** The partner is inactive.
- **Expected:** The partner is not assigned.
- **Actual:** The partner is not assigned.

### Edge Case 4: Partner at Capacity
- **Input:** The partner is already at capacity.
- **Expected:** The partner is not assigned.
- **Actual:** The partner is not assigned.

### Edge Case 5: Duplicate Cancellation Event
- **Input:** The same cancellation event is processed more than once.
- **Expected:** The cancellation is processed only once.
- **Actual:** The duplicate event is ignored.

## Remaining Failures

None were observed in the final test run.
