TESTING.md — Test Evidence

Test environment

* Python version: 3.14.2
* Command: python -m pytest -q

Automated run

* Total: 232
* Passed: 232
* Failed: 0
* Errors: 0
* Skipped: 0

Testing Notes

Scenario	Setup/input	Expected	Actual	Result
ETA calculation	Partner-to-restaurant: 8 min, preparation: 10 min, restaurant-to-destination: 12 min	ETA = 30 min; pickup = 8 min	Tests passed	Pass
Missing route	Either required travel route is missing	Partner is ineligible; ETA is unavailable	Tests passed	Pass
Invalid input	Negative or invalid travel/preparation time	Invalid data must not produce a valid assignment	Tests passed	Pass
Partner eligibility	Inactive partner or partner at full capacity	Partner must not be assigned	Tests passed	Pass
Cancellation	Same cancellation event processed more than once	Workload must only be released once	Tests passed	Pass
Tie-breaking	Two eligible partners have equal ETA	Partner with lexicographically smaller ID is selected	Tests passed	Pass

Regression tests

The test suite checks ETA calculations, missing travel data, invalid values, partner activity, capacity limits, deterministic tie-breaking, and duplicate cancellation handling.

Remaining limitations

The project uses synthetic travel-time data. It does not use live GPS, traffic information, or real-time maps. Dataset integration and the remaining project requirements should be reviewed separately.