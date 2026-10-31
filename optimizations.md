# Optimizations

## 1. Baseline and objective

The main problem was correctness: the starter could choose inactive or full partners and accept invalid times. I focused on fixing those issues and keeping the rules easy to follow. The project notes record a dataset of 180 orders and 60 partners.

## 2. Options considered

- **Check partner eligibility before calculating an ETA — used.** This avoids doing extra work for partners that cannot take an order. The risk is low because those partners should not be considered anyway.
- **Use shared checks for times and IDs — used.** This keeps the same rules in one place. The trade-off is that the checks add a little code.
- **Cache travel times or use a set for cancellation IDs — not used.** These might help with much larger data, but they add complexity or change the current data format. The project is small, so I kept the simpler approach.

## 3. Changes implemented

- **Change and reason:** Partners are checked before ETA calculation. Shared validation checks are also used to make invalid inputs easier to reject consistently.
- **Tests that protect correctness:** The recorded tests cover capacity, inactive partners, invalid times, and cancellations. `test_dataset_assignment_is_independent_of_partner_order` also checks that partner order does not change the result.
- **Measurement:** The earlier project notes record a `timeit` comparison of about 6.7 ms per full dataset pass with filtering and 8.8 ms when estimating every partner. I have not rerun this timing while editing the notes, so I am not claiming a general speed improvement from it.

## 4. Trade-offs

Extra checks make the code a little longer, but they help prevent invalid assignments. Keeping cancellation IDs in a list is simple and matches the current record format, though checking a very long list could take more time.

## 5. Further improvements

If the project grows, I could test whether storing cancellation IDs in a set or caching repeated route lookups is useful. I would compare timings on a larger dataset and keep the change only if it helps without making the code harder to understand.
