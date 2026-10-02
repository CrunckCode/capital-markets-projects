"""
LBO Model and Credit Capacity Analysis
===========================================
Full LBO model (sources and uses, debt schedule with cash-flow sweep, interest-expense
circularity handled iteratively, sponsor returns) on a REAL public mid-cap target's real
historical financials, plus a credit-capacity overlay capping leverage at a real
interest-coverage covenant threshold.
"""
import numpy as np
import pandas as pd
import yfinance as yf

TICKER = "KSS"  # real mid-cap retailer, real historical LBO-interest rumors - illustrative target

# ===========================================================================
# 1. Real historical financials as the LBO base case
# ===========================================================================
tk = yf.Ticker(TICKER)
financials = tk.financials
info = tk.info
revenue = financials.loc["Total Revenue"].iloc[0] if "Total Revenue" in financials.index else np.nan
ebitda = (financials.loc["EBITDA"].iloc[0] if "EBITDA" in financials.index else
          financials.loc["Operating Income"].iloc[0] + financials.loc.get("Reconciled Depreciation", pd.Series([0])).iloc[0])
shares_out = info.get("sharesOutstanding", np.nan)
current_price = info.get("currentPrice", tk.history(period="1d")["Close"].iloc[-1])
market_cap = shares_out * current_price if shares_out else info.get("marketCap", np.nan)

print(f"Real target: {TICKER}")
print(f"Real most recent annual revenue: ${revenue/1e6:,.0f}mm")
print(f"Real most recent annual EBITDA (proxy): ${ebitda/1e6:,.0f}mm")
print(f"Real current share price: ${current_price:.2f}, shares out: {shares_out/1e6:,.1f}mm, "
      f"market cap: ${market_cap/1e6:,.0f}mm")

EBITDA_0 = ebitda / 1e6  # $mm
REVENUE_0 = revenue / 1e6

# ===========================================================================
# 2. LBO assumptions
# ===========================================================================
ENTRY_MULTIPLE = 7.5
EXIT_MULTIPLE = 7.5
HOLD_YEARS = 5
REVENUE_GROWTH = 0.02
EBITDA_MARGIN_IMPROVEMENT = 0.005  # 50bp/year operational improvement (typical PE thesis)
CAPEX_PCT_REV = 0.03
NWC_PCT_REV_CHANGE = 0.005
TAX_RATE = 0.25

# Real leveraged-loan-style debt structure and pricing (consistent with the CLO project's
# real rating-to-spread conventions)
DEBT_TRANCHES = [
    {"name": "Term Loan B", "leverage_x": 3.5, "rate": 0.0850, "amort_pct": 0.01, "sweep": True},
    {"name": "Senior Notes", "leverage_x": 1.5, "rate": 0.0950, "amort_pct": 0.00, "sweep": False},
]
TOTAL_LEVERAGE = sum(d["leverage_x"] for d in DEBT_TRANCHES)

# ===========================================================================
# 3. Sources and uses
# ===========================================================================
purchase_ev = EBITDA_0 * ENTRY_MULTIPLE
total_debt = EBITDA_0 * TOTAL_LEVERAGE
sponsor_equity = purchase_ev - total_debt + purchase_ev * 0.02  # + 2% fees funded by equity

print("\n" + "=" * 70)
print("SOURCES AND USES")
print("=" * 70)
print(f"Purchase Enterprise Value ({ENTRY_MULTIPLE}x EBITDA of ${EBITDA_0:,.0f}mm): "
      f"${purchase_ev:,.0f}mm")
for d in DEBT_TRANCHES:
    tranche_amt = EBITDA_0 * d["leverage_x"]
    print(f"  {d['name']} ({d['leverage_x']}x, {d['rate']:.2%}): ${tranche_amt:,.0f}mm")
print(f"Total debt ({TOTAL_LEVERAGE}x): ${total_debt:,.0f}mm")
print(f"Sponsor equity (plug + 2% fees): ${sponsor_equity:,.0f}mm")

# ===========================================================================
# 4. 5-year projection with debt schedule and interest-expense circularity
#    (solved iteratively - a real, standard approach to avoid needing a full
#    circular-reference solver)
# ===========================================================================
def run_projection(leverage_multiples, entry_multiple, exit_multiple):
    tranche_balances = {d["name"]: EBITDA_0 * lev for d, lev in zip(DEBT_TRANCHES, leverage_multiples)}
    revenue, ebitda_margin = REVENUE_0, EBITDA_0 / REVENUE_0
    results = []
    for year in range(1, HOLD_YEARS + 1):
        revenue *= (1 + REVENUE_GROWTH)
        ebitda_margin += EBITDA_MARGIN_IMPROVEMENT
        ebitda_yr = revenue * ebitda_margin
        capex = revenue * CAPEX_PCT_REV
        nwc_change = revenue * NWC_PCT_REV_CHANGE

        # Iteratively solve interest expense / cash sweep circularity (3 iterations
        # converges well for this structure)
        interest_expense = sum(bal * d["rate"] for bal, d in zip(tranche_balances.values(), DEBT_TRANCHES))
        for _ in range(5):
            ebt = ebitda_yr - interest_expense - capex * 0  # capex handled via FCF, not EBT, simplified
            taxes = max(ebt, 0) * TAX_RATE
            fcf_pre_sweep = ebitda_yr - interest_expense - taxes - capex - nwc_change
            mandatory_amort = sum(EBITDA_0 * d["leverage_x"] * d["amort_pct"] for d in DEBT_TRANCHES)
            sweep_available = max(fcf_pre_sweep - mandatory_amort, 0)
            new_interest = 0
            temp_balances = dict(tranche_balances)
            for d in DEBT_TRANCHES:
                temp_balances[d["name"]] = max(temp_balances[d["name"]] - EBITDA_0 * d["leverage_x"] * d["amort_pct"], 0)
            sweep_remaining = sweep_available
            for d in DEBT_TRANCHES:
                if d["sweep"] and sweep_remaining > 0:
                    paydown = min(sweep_remaining, temp_balances[d["name"]])
                    temp_balances[d["name"]] -= paydown
                    sweep_remaining -= paydown
            new_interest_expense = sum(bal * dd["rate"] for bal, dd in zip(temp_balances.values(), DEBT_TRANCHES))
            interest_expense = new_interest_expense

        tranche_balances = temp_balances
        total_debt_balance = sum(tranche_balances.values())
        results.append({"year": year, "revenue": revenue, "ebitda": ebitda_yr,
                          "interest_expense": interest_expense, "fcf_pre_sweep": fcf_pre_sweep,
                          "total_debt": total_debt_balance,
                          "leverage_x": total_debt_balance / ebitda_yr})
    exit_ev = results[-1]["ebitda"] * exit_multiple
    exit_equity = exit_ev - results[-1]["total_debt"]
    return results, exit_equity

leverage_multiples = [d["leverage_x"] for d in DEBT_TRANCHES]
proj, exit_equity = run_projection(leverage_multiples, ENTRY_MULTIPLE, EXIT_MULTIPLE)

print("\n" + "=" * 70)
print("5-YEAR PROJECTION (debt schedule with cash-flow sweep)")
print("=" * 70)
proj_df = pd.DataFrame(proj)
print(proj_df.round(1).to_string(index=False))

irr = (exit_equity / sponsor_equity) ** (1 / HOLD_YEARS) - 1
moic = exit_equity / sponsor_equity
print(f"\nExit EV ({EXIT_MULTIPLE}x Year-{HOLD_YEARS} EBITDA of ${proj[-1]['ebitda']:,.0f}mm): "
      f"${proj[-1]['ebitda']*EXIT_MULTIPLE:,.0f}mm")
print(f"Exit equity value: ${exit_equity:,.0f}mm")
print(f"Sponsor IRR: {irr:.1%}  |  MOIC: {moic:.2f}x")

# ===========================================================================
# 5. Returns sensitivity: entry multiple x exit multiple, leverage x exit multiple
# ===========================================================================
print("\n" + "=" * 70)
print("RETURNS SENSITIVITY: ENTRY MULTIPLE x EXIT MULTIPLE (IRR)")
print("=" * 70)
entry_range = [6.5, 7.0, 7.5, 8.0, 8.5]
exit_range = [6.5, 7.0, 7.5, 8.0, 8.5]
sensitivity = pd.DataFrame(index=entry_range, columns=exit_range, dtype=float)
for entry_mult in entry_range:
    ev_at_entry = EBITDA_0 * entry_mult
    debt_at_entry = EBITDA_0 * TOTAL_LEVERAGE
    equity_at_entry = ev_at_entry - debt_at_entry + ev_at_entry * 0.02
    _, exit_eq = run_projection(leverage_multiples, entry_mult, EXIT_MULTIPLE)
    for exit_mult in exit_range:
        exit_ev_s = proj[-1]["ebitda"] * exit_mult
        exit_eq_s = exit_ev_s - proj[-1]["total_debt"]
        sensitivity.loc[entry_mult, exit_mult] = (exit_eq_s / equity_at_entry) ** (1/HOLD_YEARS) - 1
sensitivity.index.name = "Entry Multiple"
sensitivity.columns.name = "Exit Multiple"
print((sensitivity * 100).round(1).to_string())

# ===========================================================================
# 6. Credit capacity overlay: max leverage supportable given a real covenant
#    threshold (min interest coverage 2.5x, standard leveraged-loan covenant level)
# ===========================================================================
print("\n" + "=" * 70)
print("CREDIT CAPACITY OVERLAY (max leverage at 2.5x min interest coverage covenant)")
print("=" * 70)
MIN_COVERAGE = 2.5
blended_rate = sum(d["leverage_x"] * d["rate"] for d in DEBT_TRANCHES) / TOTAL_LEVERAGE
max_leverage_by_coverage = EBITDA_0 / (EBITDA_0 / MIN_COVERAGE / blended_rate) if False else None
# Solve: EBITDA / (Total_Debt * blended_rate) >= MIN_COVERAGE  ->  Total_Debt <= EBITDA/(MIN_COVERAGE*rate)
max_debt_by_coverage = EBITDA_0 / (MIN_COVERAGE * blended_rate)
max_leverage_by_coverage_x = max_debt_by_coverage / EBITDA_0
print(f"Blended debt rate: {blended_rate:.2%}")
print(f"Max leverage supportable at {MIN_COVERAGE}x min interest coverage: "
      f"{max_leverage_by_coverage_x:.2f}x EBITDA (${max_debt_by_coverage:,.0f}mm)")
print(f"Current model leverage: {TOTAL_LEVERAGE:.2f}x - "
      f"{'WITHIN' if TOTAL_LEVERAGE <= max_leverage_by_coverage_x else 'EXCEEDS'} credit capacity")

if TOTAL_LEVERAGE <= max_leverage_by_coverage_x:
    headroom_x = max_leverage_by_coverage_x - TOTAL_LEVERAGE
    print(f"Leverage headroom: {headroom_x:.2f}x additional EBITDA turns before breaching "
          f"the covenant at Year 1")
else:
    print("Entry leverage already exceeds sustainable credit capacity at deal entry - "
          "this structure would need to be de-levered before closing")
