# My Approach

## What I was trying to do

The main goal was to assign each order to a delivery partner who can
complete it in the least amount of time.

I kept the existing structure of the project instead of changing
everything. The main logic is in `service.py`, so most of my changes
were made there.

## 1. Checking the input

Before calculating an ETA, I check that the important inputs are in the
expected format.

I also check that the important IDs and zones are present. This helps
avoid errors when some information is missing or incorrect.

## 2. Calculating the ETA

There are two travel parts:

-   Partner to restaurant
-   Restaurant to customer

The calculation is:

`pickup time = current time + partner-to-restaurant travel time + partner workload`

`ETA = pickup time + restaurant preparation time + restaurant-to-customer travel time`

I make sure the travel times and other time values are valid and are not
negative. If a travel-time entry is missing, I do not treat it as zero.
In that case, the partner cannot get a reliable ETA.

## 3. Choosing a delivery partner

I go through the partners one by one.

A partner is considered only if they are active and have space for
another order. I also check whether the ETA can be calculated properly.

After collecting the eligible partners, I choose the one with the lowest
ETA.

If two partners have the same ETA, I use the partner ID to decide. The
partner ID that comes first alphabetically is selected.

If no partner is eligible, the order stays unassigned and the function
returns a reason.

## 4. Handling cancellation

When a cancellation happens, I remove the order from the partner's
active orders and reduce the partner's workload.

I also keep a list of cancellation event IDs that have already been
processed. Before processing a cancellation, I check this list. This
stops the same cancellation event from reducing the workload more than
once.

## Why I used this approach

I tried to keep the code close to the starter code and make changes only
where they were needed. This made it easier for me to understand what
each part does and explain the changes.
