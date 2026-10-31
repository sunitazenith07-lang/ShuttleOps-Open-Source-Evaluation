# Challenges and debugging evidence

## 1. Debugging method

The shared Checkpoint 7 discussion recommends treating test output as evidence, not as a list of independent fixes. For each failure, the useful questions are: What requirement applies? What input was supplied? What output was expected? What actually happened? Which shared condition explains the mismatch? After fixing that cause, rerun both focused behavior and the full suite to detect regressions.

That method mattered here because the baseline had **65 failing cases**, but the failures clustered around a small number of unimplemented rules.

## 2. Concrete failure groups

### Input validation and ETA arithmetic

Travel-time tests showed that negative values and invalid types could be accepted or reach arithmetic; a string could produce `TypeError`. Other tests supplied invalid preparation time, `now`, workload, or required order identifiers. The core issue was that the starter checked route absence but did not validate the data used in the formula.

**Resolution:** reject missing/invalid route values and malformed required fields before arithmetic; accept zero; reject negatives, Booleans, numeric strings, NaN and infinity. Guard the result too, because finite inputs can overflow when added.

### Partner status and capacity

The acceptance matrix combines active status with remaining capacity. A candidate must satisfy both conditions. The starter calculated an ETA and treated that alone as eligibility, so inactive and full candidates could be selected.

**Resolution:** filter on exact active status, valid positive integer capacity and current active-order count before ETA comparison. Cases immediately below capacity remain eligible; at or above capacity are rejected.

### Cancellation state and repeated events

The same cancellation event can be delivered more than once. The baseline removed the order the first time, but appended the event ID again on replay; event history was therefore not idempotent.

**Resolution:** check the event ID before applying changes, process against a copy, remove only an active matching order, and clamp workload at zero. Explicitly reject malformed state containers rather than silently accepting them.

## 3. Experiments and observed evidence

- Baseline `python3 -m pytest -q --tb=no` on Python 3.14.7: **65 failed, 164 passed**.
- Baseline `python3 -m main`: assigned `P-2`, pickup 13, ETA 35.
- A post-fix example containing one full-capacity partner and one partner missing a required route returned an unassigned order with a non-empty reason.
- Final `python3 -m pytest -q`: **235 passed**.
- Final `python3 -m main`: same `P-2`, pickup 13 and ETA 35.

The baseline totals represent 229 cases. Six additional cases were added in `tests/test_regressions.py`: one malformed-partner mixture, three malformed-order parameter cases, one overflowing-ETA case and one cancellation-immutability case. Existing tests were not deleted, skipped, weakened or bypassed.

## 4. Hardest edge cases and what they establish

- Python treats `bool` as a subclass of `int`; validation must explicitly exclude Boolean values from numeric time and capacity fields.
- Zero is a valid duration, but a missing route is not equivalent to a zero-minute route.
- Capacity must be checked at the exact limit as well as below and above it.
- Correct ETA math is not enough if one required route is absent or invalid.
- A cancellation replay must leave both workload and the event list unchanged from the state after the first processing.
- Finite values can still overflow in aggregate, so validating inputs alone does not guarantee a finite output.

## 5. Remaining limitations

The test environment was Python 3.14.7; the repository workflow specifies Python 3.11, which was not tested locally. Cancellation history is held in partner state and must be persisted by an integrating caller to survive a restart. No persistence or live travel-time provider exists in this project.

## 6. Integrity and explanation

The linked Checkpoint 8 discussion stresses understanding a function's purpose, inputs, validation, processing, output, failure handling and verifying tests before a technical walkthrough. The implementation and evidence are summarized in `approach.md` and `TESTING.md`. AI assistance was used; the repository's checked-in integrity policy conflicts with the instructor clarification reported in this chat, so confirm the governing policy and keep the AI-use disclosure accurate.
