# SmartDispatch V5.1 — Evaluation Demo Enhancements

## Setup
From the inner repository root containing dashboard.py:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install streamlit pandas
python -m pytest -q
python -m streamlit run dashboard.py
```

## New demo-only sections
- Decision Replay: recorded decision inspection from snapshots, without re-executing assignment.
- Challenge Mode: seven fresh isolated scenarios, showing actual results beside expected results.
- Test Evidence: timestamped saved pytest result and requirements-focused test coverage description.
- Judge Walkthrough: four guided live demonstrations using isolated engine calls.
- Operations & Audit: recorded before/after cancellation state and a non-mutating repeated-event demonstration.

## Integrity and scope
The evaluated service.py engine and its public APIs are unchanged. Demo scenarios do not mutate session state. Test evidence is a historical snapshot and must not be mistaken for a test run on the viewer's own computer. No GitHub pull request has been opened. Browser interactions have not been verified in this environment.
