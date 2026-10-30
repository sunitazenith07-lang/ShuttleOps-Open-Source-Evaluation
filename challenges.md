# Challenges

## Challenge 1: Understanding the Root Cause of Multiple Failing Tests

### Problem
The initial test run produced:
- 164 passed
- 65 failed

Failures appeared across several test categories, including travel-time validation, preparation-time validation, partner assignment, capacity handling, and cancellation processing.

### Investigation
I reviewed:
- `service.py`
- `tests/test_contract.py`
- `tests/test_acceptance_matrix.py`

I compared the expected test behaviour with the existing implementation.

### Evidence
Examples of failing tests:
- `test_invalid_or_missing_travel_time_rejected`
- `test_preparation_time_validation`
- `test_capacity_boundary_matrix`
- `test_duplicate_cancellation_is_idempotent`

### Resolution
I found that `service.py` lacked validation logic for:
- Order fields
- Travel times
- Preparation times
- Partner activity
- Partner capacity

I added reusable validation helpers and updated the dispatch logic accordingly.

---

## Challenge 2: Duplicate Cancellation Handling

### Problem
Cancellation events were recorded even when the same event had already been processed.

### Evidence
The failing test showed:

```text
Expected:
['C1']

Actual:
['C1', 'C1']
```

### Resolution
I added a check for previously processed cancellation IDs before applying workload and active-order updates.

This made cancellation processing idempotent, so processing the same cancellation more than once does not duplicate its effects.

---

## Challenge 3: Capacity Boundary Cases

### Problem
Partners at full capacity were still considered eligible for new assignments.

### Investigation
I reviewed the acceptance requirements and the capacity-related tests.

### Resolution
I added capacity validation and ensured that a partner is eligible only when:

```text
active_orders < capacity
```

A partner whose active-order count is equal to or greater than capacity is therefore excluded from assignment.
