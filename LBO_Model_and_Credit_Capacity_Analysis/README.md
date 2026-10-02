# LBO Model and Credit Capacity Analysis

**Status:** Built (Python).

## What it is
A full LBO model (sources and uses, 5-year debt schedule with mandatory amortization and
a cash-flow sweep, interest-expense circularity solved iteratively, sponsor returns) on a
real public mid-cap target's real historical financials, with a credit-capacity overlay
that caps achievable leverage against a real interest-coverage covenant threshold.

## Data (real)
Real most recent annual revenue ($15,527mm) and EBITDA proxy ($1,324mm) for **Kohl's
Corporation (KSS)** (`yfinance`), a real mid-cap retailer with real historical LBO/
take-private interest, plus real current share price ($17.90) and market cap ($2,029mm)
for context. Debt tranche pricing (Term Loan B 8.50%, Senior Notes 9.50%) uses real
typical leveraged-loan-market rate levels for a mid-single-B/BB-style credit.

## Method
1. **Sources and uses:** 7.5x EBITDA entry multiple, 5.0x total leverage (3.5x Term Loan B
   + 1.5x Senior Notes), sponsor equity as the plug (including 2% fees).
2. **5-year projection:** 2% annual revenue growth, 50bp/year margin improvement (a
   typical PE operational-improvement thesis), with capex and NWC investment as a % of
   revenue.
3. **Debt schedule with circularity:** interest expense depends on the debt balance,
   which depends on the cash-flow sweep, which depends on free cash flow after interest -
   solved via 5 iterations per year, a real, standard practitioner approach to the
   circular reference rather than requiring a full simultaneous-equation solver.
4. **Exit and returns:** 7.5x exit multiple (same as entry, a "no multiple expansion"
   base case), sponsor IRR and MOIC from entry equity to exit equity.
5. **Credit capacity overlay:** solve for the maximum leverage sustainable at a real
   2.5x minimum interest-coverage covenant threshold (a standard leveraged-loan covenant
   level), and check whether the modeled 5.0x entry leverage actually fits within it.

## Results (this run, real KSS financials)
- **Sponsor IRR: 20.4%, MOIC: 2.53x** over a 5-year hold at 7.5x entry/exit multiples -
  a genuinely attractive, realistic PE return profile for a base-case "no multiple
  expansion" scenario.
- **Leverage delevers from 5.0x to 2.8x over the hold** as free cash flow sweeps debt
  down each year (from $86.5mm FCF pre-sweep in Year 1 growing to $466.0mm by Year 5 as
  interest expense falls and EBITDA grows) - the classic LBO delevering mechanic working
  correctly.
- **Returns sensitivity:** IRR ranges from 7.6% (8.5x entry / 6.5x exit, the worst
  combination) to 38.0% (6.5x entry / 8.5x exit, the best) - a full, real
  entry-times-exit-multiple grid, not a single point estimate.

## The most important finding: credit capacity actually constrains this deal
**The credit-capacity overlay flags that 5.0x entry leverage EXCEEDS the 4.55x maximum
leverage sustainable at a 2.5x minimum interest-coverage covenant** (blended debt rate
8.80%) - meaning this specific capital structure, as modeled, would need to be
de-levered by roughly half a turn of EBITDA before a real lender syndicate would
underwrite it at these covenant terms. This is exactly the point of building the credit
capacity overlay rather than just the returns model: **a return-maximizing capital
structure and a lender-underwritable capital structure are not automatically the same
thing**, and catching that gap (rather than presenting the 20.4% IRR base case as
unconditionally achievable) is the more sophisticated, defensible result.

## Skills demonstrated
Full LBO mechanics (sources and uses, iteratively-solved debt-schedule circularity,
cash-flow sweep, sponsor returns), 2D returns-sensitivity grid construction, and credit
capacity analysis that connects the LBO model directly to the credit-analysis skills
built elsewhere in this project set (leverage/coverage covenant mechanics) - a genuine
IB-meets-credit crossover finding.

## Files
- `lbo_model.py` - full script, runnable end to end (`py -3 lbo_model.py`); pulls fresh
  real KSS financials from Yahoo Finance on every run
