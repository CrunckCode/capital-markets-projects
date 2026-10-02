# M&A Comparable Companies and Precedent Transactions Valuation Tool

**Status:** Built (Python).

## What it is
A comparable-companies trading-multiples analysis on a real 6-name retail peer group, a
real publicly-reported precedent-transactions table (with a control-premium adjustment
explicitly separated out), applied to KSS (the same LBO target as the earlier project),
combined into a football-field valuation chart alongside that project's LBO-implied entry
range - the three-method valuation triangulation a real IB analyst builds.

## Data (real)
Real enterprise value, EBITDA, revenue, and trailing P/E (`yfinance`) for KSS and a
6-name real retail peer group (M/Macy's, JWN/Nordstrom, DDS/Dillard's, TJX, ROST, BURL).
**Precedent transactions are real, publicly-known retail M&A deals** with their
approximate real publicly-reported/estimated multiples: Sycamore Partners/Belk (2015,
~7.0x), Sycamore Partners/Talbots (2012, ~6.5x), Men's Wearhouse/Jos. A. Bank (2014,
~8.0x), Simon Property/Brookfield-JCPenney (2020 distressed, ~4.5x), Authentic
Brands/Forever 21 (2020 distressed, ~3.5x).

## Method
1. Pull real trading multiples (EV/EBITDA, EV/Revenue, P/E) for the peer group.
2. Screen for outliers (exclude peers whose multiple sits beyond 2 standard deviations
   from the peer mean) - JWN dropped out of the screened set, but honestly this was
   because `yfinance` didn't return complete real financial data for JWN at run time, not
   because its multiple was a genuine statistical outlier; worth stating precisely rather
   than implying the outlier logic itself flagged it.
3. Build the real precedent-transactions table and explicitly note that precedent
   multiples embed a real ~25% control premium over unaffected trading price, which
   comparable-companies multiples do not - a genuine, expected source of difference
   between the two methods, not a modeling error.
4. Apply the screened comps range and the real precedent range to KSS's real EBITDA.
5. Combine with the LBO-implied entry range (6.5x-8.5x, from the LBO project's own
   sensitivity grid) into a football-field chart.

## Results (this run, real data)
| Method | Implied Enterprise Value |
|---|---|
| Comparable Companies (screened peer EV/EBITDA 6.9x-20.7x) | $8,273mm - $24,753mm |
| Precedent Transactions (real deal multiples 3.5x-8.0x) | $4,175mm - $9,544mm |
| LBO-Implied Entry Range (6.5x-8.5x) | $7,754mm - $10,140mm |

**All three methods genuinely overlap in a real, narrow band: $8,273mm - $9,544mm** -
this is a materially useful, non-trivial finding: an LBO sponsor's return-driven entry
multiple, a set of real observable public comps, and a set of real disclosed precedent
deals (which embed a real control premium) all triangulate to roughly the same
enterprise-value range for this target, which is exactly the cross-validation a real
valuation committee looks for before signing off on a number. The comps range is much
wider on the high end (up to $24.75bn) because it includes ROST/TJX/BURL, which are
structurally higher-multiple, higher-growth off-price retailers genuinely not
comparable to KSS's traditional department-store model - a real business-model caveat
worth stating rather than treating the full comps range as equally valid.

## Skills demonstrated
Comparable-companies screening (including correctly diagnosing why a peer dropped out of
the screened set), real precedent-transaction benchmarking with an explicit control-
premium caveat, and three-method valuation triangulation into a football-field summary -
directly answers "Equity Capital Markets Analyst" / general IB Analyst technical
requirements, and demonstrates connecting multiple project outputs (this project reuses
the LBO project's entry-range output) into one coherent valuation narrative.

## Files
- `ma_comps_precedents.py` - full script, runnable end to end
  (`py -3 ma_comps_precedents.py`); pulls fresh real trading multiples from Yahoo Finance
  on every run
- `football_field.png` - football-field valuation summary chart
