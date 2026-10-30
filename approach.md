# Approach and implementation decisions

## 1. Baseline

Starting commit: `fcfe44d935c55509dbfeb0e78c93a8d44345c380`, branch
`fix/dispatch-evaluation`, clean working tree. GitHub and `git ls-remote` confirmed
upstream main still matched this commit.

Before changing code, Windows commands produced:

```text
python --version                         Python 3.14.6
python -m pip install -r requirements-dev.txt
                                         succeeded; pytest 9.2.0 already installed
python -m pytest -q                       65 failed, 164 passed in 1.27s
python -m main                           O-7 -> P-2, pickup 13, ETA 35
```

The demo already calculated its example correctly. That did not establish input
safety or correct partner eligibility. This work used Codex under a user-reported
verbal faculty exception; the published AI prohibition remains. See `AI_USAGE.md`.

## 2. Codebase understanding

`models.py` builds dictionaries. `fixtures.py` supplies the demo; `main.py` calls
`assign_order`. In `service.py`, `estimate_eta` computes a candidate,
`assign_order` selects the minimum `(ETA, partner ID)`, and `process_cancellation`
returns a deep copy of changed partner state.

The original tests, dataset, templates, configuration and both workflows were
inspected. The seven rules in `STUDENT_PROBLEM_STATEMENT.md` are the contract.
A later PDF cross-check found an older rubric in the bundled PDF; the Markdown
rubric takes precedence. The README's central guide URL returned 404.

Travel rows use `from`, `to`, `minutes`; dataset tests convert them to tuple keys.
Capacity is the length of `active_order_ids`. Assignment makes a decision without
reserving capacity; the caller owns later state changes.

## 3. Investigation and implementation strategy

Initial hypotheses were absent eligibility checks and unchecked cancellation
history. Source inspection and reproductions confirmed these causes. Added
safety regressions ran against the starter: **50 failed, 8 passed**.

| Symptom and reproduction | Component and confirmed cause | Chosen correction and reason | Alternative considered | Regression and actual validation |
|---|---|---|---|---|
| Travel `"2"` raises TypeError; workload -5 gives pickup -4 | `estimate_eta` performs unchecked arithmetic | Validate finite non-negative numbers, excluding booleans; reject non-finite sums | Coercion/clamping silently changes invalid input | Original time matrices, `test_malformed_partner_fields_are_ineligible`, `test_float_sum_overflow_is_rejected`; pass |
| Inactive/full P is selected by original contract tests | `assign_order` trusts every numeric ETA | Enforce eligibility in `estimate_eta`, also protecting direct calls | Filtering only in assignment leaves inconsistent estimates | `test_lowest_eta_is_selected_after_eligibility_filtering`; pass |
| None order raises AttributeError; blank order ID assigns P | Shapes/IDs unchecked before `.get` and route lookup | Validate records and non-blank string IDs before lookup | Broad exception handling would hide coding mistakes | `test_malformed_records_are_safe`, `test_missing_required_order_field_is_rejected`; pass |
| Event C cancels A, then its replay cancels B | `process_cancellation` records IDs but never checks them | Check ID before any change; validate release amount and remove stale minutes entry | Order-only deduplication misses reused IDs with different payloads | `test_same_event_with_different_payload_is_ignored`; pass, B keeps workload 6 |

## 4. Implementation decisions

Shared checks keep numeric and identifier rules consistent. Zero and finite
fractions remain valid. Required order fields cannot be missing. Missing workload
and active-order lists retain the starter defaults of zero/empty. Capacity must
be a positive integer; only boolean True means active.

The original minimum-selection method remains. String IDs sort lexicographically:
P-10 comes before P-2. Missing travel never becomes zero. Unassigned results keep
the original fields/general reason; rejected direct estimates add a specific reason.

Invalid cancellation IDs/state are a no-op. A present order with missing/invalid
per-order minutes stays unchanged because its workload cannot safely be guessed.
Valid unknown-order events are recorded once but release nothing. History is
scoped to the supplied partner. Inputs are not mutated.

## 5. Verification

The first focused dispatch run passed 216 cases; focused cancellation passed 71.
The integrated suite passed **469 tests**. The demo still reports pickup 13 and
ETA 35. Compilation and `git diff --check` passed. See `TESTING.md` for environments.

An independent reference calculation checks all 180 dataset orders and reversed
partner input. A separate state model checks all 177 cancellation events.
Original tests and workflows are unchanged. Visible tests cannot prove every
input correct. No route registry, concurrent reservation, durable event storage
or optional batch/priority scheduling was added. Independent human review and
live explanation remain necessary.
