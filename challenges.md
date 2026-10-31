# Challenges I Faced

## 1. Understanding where the main logic was

At first, I was looking at `main.py`, but it mostly takes the sample
input and calls the assignment function. The actual logic is in
`service.py`.

Once I understood this, I knew where I needed to focus my changes.

## 2. Understanding the ETA calculation

I had to understand how the pickup time and final ETA were connected.

The pickup time includes the current time, travel from the partner to
the restaurant, and the partner's existing workload. The final ETA then
adds restaurant preparation time and travel from the restaurant to the
customer.

Working through the sample values helped me check that I understood the
formula.

## 3. Missing travel-time information

One important issue was that missing travel data must not be treated as
zero. If I use zero when a route is missing, the ETA could look much
shorter than it really is.

I changed the checks so that a partner is not considered when a required
travel-time value is missing or invalid.

## 4. Checking partner eligibility

It was not enough to calculate an ETA for every partner. A partner also
needs to be active and below their order capacity.

I added checks for these conditions before considering a partner for
assignment.

## 5. Handling repeated cancellations

I learned that a cancellation event might be received more than once. If
the same event reduces workload every time, the partner's workload
becomes incorrect.

To avoid this, I check whether the event ID has already been processed.

## 6. Debugging with the tests

My first test run had 65 failures and 164 passes. That showed me that
the starter code was missing several required checks.

I used the failing tests to understand which behaviours needed fixing.
After an earlier set of fixes, all 229 tests passed. I then tried to
shorten the code, so I need to run the tests once more on that final
shorter version.

## What I learned

I learned that a program can give the correct answer for a normal
example but still fail when the input is missing, invalid, or repeated.
Testing these less common situations is important, especially when the
program is making decisions based on time and capacity.
