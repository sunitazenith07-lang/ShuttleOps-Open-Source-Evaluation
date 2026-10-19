# ShuttleOps: Campus Shuttle Route and Seat Management

**Zenith School of AI | Open-Source Evaluation | Python 3.10+ | JSON | GitHub**

## Challenge
ShuttleOps tracks campus routes, origins and destinations, intermediate stops, departures, passenger counts, capacity and trip status. Understand the starter, fix three organiser issue tickets announced at kick-off, improve search and filters, implement one operations feature and explain your decisions. Extend the existing code rather than rebuilding it.

## Start-up
```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```
Read README.md, models.py, service.py, fixtures.py, data/ and tests/test_contract.py. Create ARCHITECTURE.md with a project map, data model, numbered data flow, storage design, simple diagram and three improvements grounded in code.

## Mandatory work
1. Reproduce and fix the three issue tickets released by organisers; add a regression test for each.
2. Implement case-insensitive search that trims surrounding spaces; combine text, category and status filters and handle invalid filters, no matches and empty data safely.
3. Complete at least one feature:
   - Seat availability view that reports remaining seats for each active trip.
   - Route discovery filtering by origin, destination, and stops, combined with trip status/category.
   - Delay report that records an explanation for affected trips without overwriting the planned departure time.
4. Add tests, document at least five scenarios in TESTING.md and update README.md/PROJECT_NOTES.md.
5. Use focused branches and pull requests. Do not delete, skip, weaken or bypass tests.

## Test suite
The public suite contains 110 visible cases. The untouched starter should begin with 86 passing and 24 failing because of deliberate defects. The final evaluation adds 90 private checks, making 200 cases in total. Private evaluator material is not included here.

## Contribution workflow and submission
Use fix/issue-<number>-<summary> for fixes and feature/<short-name> for features. Pull requests should include root cause, summary, tests run and known limitations.

Submit repository/fork and PR links, README.md, ARCHITECTURE.md, TESTING.md, PROJECT_NOTES.md, a summary of fixes and features, and a two-minute demo. If AI tools are used, fill AI_USAGE.md: tool/model, purpose, what you verified/changed yourself, any displayed credits/tokens (or “not available”), and one suggestion accepted, modified or rejected with your reason. Never include secrets or private personal data. Be ready to explain and modify your code during viva.

## Evaluation — 100 marks

| Criterion | Marks |
|---|---:|
| Codebase understanding | 15 |
| Problem solving and root-cause analysis | 25 |
| Working prototype and requested features | 20 |
| Code quality | 10 |
| Testing and edge cases | 10 |
| Demo, communication and viva | 20 |
| **Total** | **100** |

All 300 students use the same rubric; the top 270 will be shortlisted by final score, subject to minimum competency criteria announced by organisers. Follow the latest official announcements for kick-off, code freeze, submission and demo timings.
