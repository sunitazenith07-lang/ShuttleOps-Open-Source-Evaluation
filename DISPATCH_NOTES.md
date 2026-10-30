# Dispatch Notes

## Worked ETA Example

### Order
- Order ID: `O-7`
- Restaurant ID: `R-2`
- Destination Zone: `Z-9`
- Preparation Time: 10 minutes

### Partner
- Partner ID: `P-2`
- Workload: 5 minutes

### Travel Times
- Partner to Restaurant: 8 minutes
- Restaurant to Customer: 12 minutes

### Calculation

**Pickup Time**

```text
Pickup Time = Current Time + Partner Travel Time + Workload
            = 0 + 8 + 5
            = 13 minutes
```

**ETA**

```text
ETA = Pickup Time + Preparation Time + Restaurant-to-Customer Travel Time
    = 13 + 10 + 12
    = 35 minutes
```

### Result

```text
partner_id = P-2
pickup_minutes = 13
eta_minutes = 35
```

---

## Example: No Eligible Partner

### Partner Status
- Partner A: Inactive
- Partner B: At capacity
- Partner C: Missing travel-time data

### Result

```text
partner_id = None
reason = no eligible partner
```

---

## Assumptions

- Active status must be strictly `True`.
- Capacity must be a positive integer.
- Travel times must be present and valid.
- Missing travel times must not be treated as zero.
- Preparation time must be non-negative.

---

## Important Edge Cases

### Edge Case 1: Missing Travel-Time Data
A partner with missing travel-time data must be rejected.

### Edge Case 2: Negative Preparation Time
An order with a negative preparation time must be rejected.

### Edge Case 3: Duplicate Cancellation Event
A cancellation event that has already been processed must not be applied again.
