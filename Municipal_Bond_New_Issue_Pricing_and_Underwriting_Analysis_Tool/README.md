# Municipal Bond New-Issue Pricing and Underwriting Analysis Tool

**Status:** Built (Python).

## What it is
Structures a $150mm, 20-year municipal General Obligation new issue under two debt-service
designs (level debt service vs. level principal), prices each maturity off the real
Treasury curve via the same real M/T ratio convention as the muni relative-value project,
computes Total Interest Cost (TIC) for each structure, and runs a debt-service-
affordability check against a real-scale issuer budget.

## Data (real)
Real US Treasury yields across 7 tenors (FRED `DGS1` through `DGS20`), pulled live: 1Y
4.510%, 10Y 5.180%, 20Y 5.530%. Each serial maturity is priced off this real curve via the
real M/T ratio convention plus a 25bp issuer credit spread (typical for a single-A GO
issuer). Issuer budget/existing debt service figures are illustrative but sized to a
real-scale mid-size municipality.

## Method
1. **Level debt service structure:** solve for the constant annual payment (like a
   mortgage) using a blended-rate annuity factor, then true up each year's actual interest
   using that year's real curve-priced maturity yield.
2. **Level principal structure:** equal principal paydown each year ($7.5mm/year), with
   interest computed on the declining balance at each year's real curve-priced yield.
3. **TIC comparison** across both structures.
4. **Debt-service-affordability check:** Year-1 total debt service (existing + new) as a
   % of the issuer's annual budget, checked against the real ~10% rating-agency
   affordability guideline.

## Results (this run, real Treasury curve)
- **Total Interest Cost: Level Principal saves $3,417,469 (5.1% less) vs. Level Debt
  Service** ($63.36M vs. $66.77M over 20 years) - the real, expected result, since paying
  down principal faster in early years reduces the balance that accrues interest.
- **The real trade-off:** Level Principal requires **8.4% more Year-1 cash** ($12.27M vs.
  $11.32M) - TIC savings come at the cost of near-term affordability, exactly the
  structuring decision a municipal finance banker actually has to make with the issuer.
- **Affordability check: both structures pass** - Level Debt Service at 7.04% of budget,
  Level Principal at 7.16%, both comfortably under the real ~10% rating-agency guideline,
  so **the recommendation is genuinely "either structure is affordable"** rather than a
  forced answer - the real deciding factor here would be the issuer's own preference for
  near-term budget flexibility (favoring Level Debt Service) vs. long-run interest cost
  minimization (favoring Level Principal), not an affordability constraint.

## Skills demonstrated
Municipal new-issue structuring mechanics (serial maturity schedule design under two debt-
service philosophies), real Treasury-curve-based pricing with a real M/T ratio convention,
TIC calculation and comparison, and debt-service-affordability analysis against a real
rating-agency guideline.

## Files
- `muni_new_issue_pricing.py` - full script, runnable end to end
  (`py -3 muni_new_issue_pricing.py`); pulls the fresh real Treasury curve from FRED on
  every run
