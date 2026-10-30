# SmartDispatch — Delivery Partner Assignment & ETA Engine

SmartDispatch is a small, offline Python decision engine for food delivery. Given one order and a list of delivery partners, it works out which partners can take the order, estimates when each of them could deliver it, and assigns the order to the partner with the earliest ETA. It also processes order cancellations so that a partner's workload and capacity stay consistent, even if the same cancellation event arrives more than once.

All data is synthetic. There is no app, map or live GPS: travel times come from a lookup table.

## Problem and objectives

A dispatcher has to decide quickly and has to be able to justify the decision. The engine therefore aims to:

- assign only to partners who can genuinely take the order (active, below capacity, with complete and valid data);
- compute ETAs from the formula in the problem statement, without guessing missing values;
- give the same answer for the same input, regardless of the order partners are listed in;
- leave an order unassigned, with a clear reason, rather than force a bad assignment;
- handle malformed records, unknown IDs and extreme values without crashing.

## Main features

| Function (`service.py`) | Purpose |
|---|---|
| `assign_order(order, partners, travel, now=0)` | Picks the eligible partner with the lowest ETA, or returns an unassigned result with counted rejection reasons. |
| `estimate_eta(order, partner, travel, now=0)` | Computes pickup time and ETA for one order–partner pair, or explains why no reliable ETA exists. |
| `process_cancellation(partner, order_id, event_id)` | Applies a cancellation to a copy of the partner record. Idempotent per `event_id`. |
| `explain_assignment(order, partners, travel, now=0)` | Optional stretch feature: the assignment result plus a per-partner verdict (ETA or rejection reason). |

## Dispatch workflow

1. **Validate the order.** `order_id`, `restaurant_id` and `destination_zone` must be non-empty strings, and `prep_minutes` must be a finite, non-negative number. An invalid order is returned unassigned straight away.
2. **Check each partner's eligibility** (`_partner_problem`): valid record and IDs, `active is True`, `capacity` an integer ≥ 1, fewer active orders than capacity, valid `workload_minutes`.
3. **Look up both travel legs** in the `(from, to) → minutes` map: partner zone → restaurant, and restaurant → destination zone. If either leg is missing or invalid, that partner gets no ETA. **Missing travel data is never treated as zero.**
4. **Compute the ETA** for every remaining partner.
5. **Select** the lowest ETA. An exact tie goes to the partner ID that comes first in ascending lexicographic (string) order.

## ETA calculation

```
pickup_minutes = now + partner_to_restaurant + workload_minutes
eta_minutes    = pickup_minutes + prep_minutes + restaurant_to_customer
```

All times are in minutes on one shared clock. `eta_minutes` is an absolute time; the delivery duration is `eta_minutes - now`. If the computed ETA is not a finite, non-negative number (for example, very large inputs overflowing to infinity), the partner is rejected with `'ETA out of range'`.

Worked example (the demo in `fixtures.py`): partner `P-2` is 8 minutes from the restaurant and has 5 minutes of existing work, so it can pick up at 13. The restaurant needs 10 minutes and the customer is 12 minutes away, so the ETA is 13 + 10 + 12 = **35**. The other partner, `P-1`, reaches 36, so `P-2` is assigned.

Every result has the same five keys:

```python
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

When nobody is eligible, `partner_id`, `pickup_minutes` and `eta_minutes` are `None`, and `reason` lists each rejection cause with a count, for example `'no eligible partner: partner at capacity (1), partner inactive (1)'`.

## Cancellation handling

`process_cancellation` never modifies the record passed in; it returns a deep copy.

- An `event_id` already in `processed_cancellation_ids` is ignored, so a duplicated event cannot release workload twice.
- For a new event on an active order: the order is removed from `active_order_ids`, its minutes are taken from `minutes_by_order`, and the workload is reduced, never below 0.
- An unknown order changes nothing, but the event is still recorded.
- Malformed data is never "repaired" into valid-looking values:
  - If `active_order_ids` or `processed_cancellation_ids` is present but not a list, the record is returned unchanged and the event is skipped. Overwriting the field could erase real orders, or erase the event history and allow a double release.
  - If `workload_minutes` is invalid (for example the string `'20'`), the order is still removed and the event recorded, but the workload value is left as it is.

## Technologies

- Python 3.10+ (developed and tested on 3.14.3; CI runs on 3.11).
- Standard library only (`math`, `copy`) for the engine.
- `pytest` for tests (`requirements-dev.txt`).

## Running the project

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q        # full test suite
python -m main             # offline demo
```

## Testing summary

**288 tests pass, with 0 failures and 0 skips.** These are the 229 original tests from the starter repository, unmodified, plus 59 added:

- 54 regression and edge-case tests in `tests/test_regression.py`;
- 5 dataset tests in `tests/test_dataset.py`.

The dataset tests convert the 387 travel rows in `data/records.json` into the tuple-key map and replay all 180 orders and 177 cancellation events. Replaying the cancellations a second time leaves the state unchanged.

Before any changes, the untouched starter scored 65 failed / 164 passed. Full evidence is in [TESTING.md](TESTING.md).

## Project documentation

| Document | Contents |
|---|---|
| [approach.md](approach.md) | Baseline, root causes, implementation strategy, decisions and student contribution |
| [challenges.md](challenges.md) | Real problems encountered, evidence and how they were resolved |
| [optimizations.md](optimizations.md) | Options considered, measured timings, complexity and trade-offs |
| [TESTING.md](TESTING.md) | Test environment, verified results and 17 documented edge cases |
| [DISPATCH_NOTES.md](DISPATCH_NOTES.md) | Worked ETA, no-eligible-partner example, edge cases and assumptions |
| [VIVA_PREPARATION.md](VIVA_PREPARATION.md) | Walkthrough of the implementation, viva questions and live-change exercises |
| [AI_USAGE_TEMPLATE.md](AI_USAGE_TEMPLATE.md) | AI-use declaration and student contribution |

---

## Evaluation instructions (from the starter repository)

> **Central student guide:** [Read the complete Open-Source Evaluation Guide](https://github.com/sunitazenith07-lang/LabLedger-Open-Source-Evaluation/blob/main/OPEN_SOURCE_EVALUATION_STUDENT_GUIDE.md) — includes all four tracks, required reading, submission instructions, and the three compulsory documentation files.

Zenith School of AI | Individual Open-Source Evaluation | Python 3.10+ | Synthetic challenge data only

Logistics: partner eligibility, capacity, ETA calculation, tie-breaking and cancellation handling.

### Start here — read before coding

**Start with the [Student Reading Checklist](STUDENT_START_HERE.md).** It lists the required reading and every deliverable.

- **[Open problem statement PDF](docs/Problem_Statement.pdf)**
- [Read the full Markdown problem statement](STUDENT_PROBLEM_STATEMENT.md)
- [Open all student instructions and required-file checklist](STUDENT_START_HERE.md)

### Setup

1. Install Python 3.10+ and Git.
2. Install dependencies: `python -m pip install -r requirements-dev.txt`
3. Run visible tests: `python -m pytest -q`
4. Run the offline demo: `python -m main`

Some visible tests are expected to fail on the untouched starter because the required behaviour is incomplete. This is intentional. Never delete, skip, weaken or bypass tests to make the check green.

### Mandatory submission — code plus documentation

Submit one pull request from your fork to this original repository; **do not merge it**. Read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the [pull-request checklist](.github/PULL_REQUEST_TEMPLATE.md).

You must complete all three Markdown documents; they are part of the 100-mark evaluation:

- [`approach.md`](approach.md) — 5 marks
- [`challenges.md`](challenges.md) — **COMPULSORY**, 5 marks
- [`optimizations.md`](optimizations.md) — 5 marks

Also submit `TESTING.md` and the challenge-specific notes file named in [the problem statement](STUDENT_PROBLEM_STATEMENT.md). Code alone is not a complete submission. All notes must reflect the work you actually performed.

### Review the whole codebase

Before editing, read the student checklist and inspect the source files, synthetic data, every test under `tests/`, environment/configuration files, and the workflows under `.github/workflows/`. Understand what each file does before changing it.

The starter contains intentionally incomplete behaviour. Fix root causes and preserve the tests. Do not edit CI to evade failures. You must be able to explain your code and may be asked to make a small live modification.
