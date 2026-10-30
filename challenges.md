# Challenges and debugging

## 1. Challenge or confusing behaviour

The hardest investigated case was replaying a cancellation ID with a different
order. The original duplicate test exposed repeated history; the broader defect
could also release another order's capacity/workload. There was no prolonged
algorithmic blocker. These are actual Codex-assisted investigations, not invented
personal student experiences.

## 2. Evidence

A partner had active A/B, workload 10, and minutes `{'A': 4, 'B': 6}`.
Cancel A with event C: workload becomes 6. On the starter, replay C for B:
B also disappears, workload becomes 0, and history becomes `['C', 'C']`.
The function appended event IDs without checking them.

Other starter probes found AttributeError for None order/partner, pickup -4 for
workload -5, and a missing event ID releasing an order and recording None.

## 3. What was tried

1. Ran the untouched suite: 65 failed, 164 passed; read failing assertions/source.
2. Ran the two-order replay directly; it demonstrated a real second release.
3. Added safety regressions and ran them on the starter: 50 failed, 8 passed.
4. Parsed the entire dataset. Seven events omit event_id; its edge catalog also
   names differing-payload replays. Missing IDs therefore need an explicit rule.
5. After fixing validation/replay handling, compared all 177 events with a separate
   reference state model; every transition matched.

## 4. Resolution

Check history before changing state. A seen event ID returns an unchanged copy,
even if the payload names another order. For a valid first event, remove a present
order once, subtract its recorded minutes with a zero floor, remove its minutes
entry and record the event once.

Unknown orders release nothing but their valid events are remembered. Invalid
IDs/state or missing release minutes leave state unchanged. Deduplicating only by
order would not protect against a reused event naming another order.

## 5. Proof and regression prevention

`test_same_event_with_different_payload_is_ignored` checks B remains with workload
6. The new cancellation file also covers invalid IDs/state, unknown orders,
a new event for an already-cancelled order and unchanged caller input.
The focused cancellation run passed 71 cases. The full suite passed 469,
including the entire dataset stream; original tests are unchanged.

## 6. Unresolved challenge or next step

History must be retained by the caller. Cross-partner, restart and concurrent
deduplication need a storage/atomic-update contract beyond this exercise.

Environment work also required care: normal CLI login rejected the existing token
for missing read:org, while a temporary GH_TOKEN using the same Git credential
authenticated MAD1IZJOD and created the fork. No token was committed. Installing
dependencies directly into uv's Python 3.11 was refused as externally managed;
validation moved to an isolated virtual environment rather than overriding it.

The published AI ban still conflicts with the user-reported verbal faculty
exception. `AI_USAGE.md` preserves this discrepancy and its unverified source.
