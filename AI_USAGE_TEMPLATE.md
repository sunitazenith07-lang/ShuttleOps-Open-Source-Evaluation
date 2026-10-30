# AI-Use Declaration

For each tool/model or source, state the purpose, what you independently verified or changed, any displayed credits/tokens (or “not available”), and one suggestion accepted, changed or rejected with your reason. Never include secrets or private personal data.


## Tool and permission
- Tool: Claude Code (Claude Sonnet 5.5), used as a mentor for this evaluation.
- Credits/tokens: not available.

## Purpose
Explaining the codebase, proposing each change with its reason, and checking my work against the tests. The assistant did not edit any file or run git commands that change state. I typed every change in service.py and the tests, ran the tests, and made all commits myself.

## What I verified or changed myself
- Ran the baseline and every test run, and recorded the real counts (65 failed -> 0 failed).
- Ran the demo and manual probes, and mutation-checked tests by breaking the code and reverting.
- Rewrote the notes in my own words.