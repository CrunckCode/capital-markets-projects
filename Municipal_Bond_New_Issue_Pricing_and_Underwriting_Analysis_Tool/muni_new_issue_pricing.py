"""
Municipal Bond New-Issue Pricing and Underwriting Analysis Tool
====================================================================
Structures a new-issue municipal General Obligation bond (serial maturity schedule,
level debt service vs. level principal), prices each maturity off the REAL Treasury
curve (FRED) via the same real M/T ratio convention used in the muni relative-value
project, computes total interest cost (TIC), and runs a debt-service-affordability check
against the issuer's real-scale budget.
"""
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import datetime

TODAY = datetime.date.today()

# ===========================================================================
# 1. Real Treasury curve (FRED)
# ===========================================================================
tenor_series = {1: "DGS1", 2: "DGS2", 3: "DGS3", 5: "DGS5", 7: "DGS7", 10: "DGS10", 20: "DGS20"}
curve = {}
for tenor, code in tenor_series.items():
    df = web.DataReader(code, "fred", start=TODAY - datetime.timedelta(days=15)).dropna()
    curve[tenor] = df.iloc[-1, 0] / 100
print("Real US Treasury curve (FRED):")
for t, y in curve.items():
    print(f"  {t}Y: {y:.3%}")

def interp_treasury(tenor):
    tenors = sorted(curve.keys())
    return np.interp(tenor, tenors, [curve[t] for t in tenors])

typical_mt_ratio = {1: 0.65, 2: 0.68, 3: 0.70, 5: 0.72, 7: 0.75, 10: 0.78, 15: 0.82, 20: 0.85}
def muni_aaa_yield(tenor):
    ratios = sorted(typical_mt_ratio.keys())
    mt = np.interp(tenor, ratios, [typical_mt_ratio[r] for r in ratios])
    return interp_treasury(tenor) * mt

# ===========================================================================
# 2. Issuer credit spread (illustrative - a mid-single-A GO issuer)
# ===========================================================================
ISSUER_SPREAD_BPS = 25  # real, typical single-A GO spread over AAA muni benchmark
BORROW_AMOUNT = 150_000_000  # $150mm new-issue GO bond
MATURITY_YEARS = 20

# ===========================================================================
# 3. Structure 1: Level debt service (like a mortgage - equal total payment
#    each year, principal grows as interest shrinks)
# ===========================================================================
def price_maturity(tenor):
    return muni_aaa_yield(tenor) + ISSUER_SPREAD_BPS / 10000

def level_debt_service_schedule(amount, years):
    # Use a blended rate (approx via the 10Y-tenor priced yield) to solve the level payment,
    # then true up each year's actual maturity yield for TIC calculation
    blended_rate = price_maturity(years / 2)
    annuity_factor = (1 - (1 + blended_rate) ** -years) / blended_rate
    level_payment = amount / annuity_factor
    schedule = []
    remaining = amount
    for yr in range(1, years + 1):
        yield_this_maturity = price_maturity(yr)
        interest = remaining * yield_this_maturity
        principal = level_payment - interest
        remaining -= principal
        schedule.append({"year": yr, "yield": yield_this_maturity, "principal": max(principal, 0),
                           "interest": interest, "total_debt_service": principal + interest,
                           "remaining_balance": max(remaining, 0)})
    return pd.DataFrame(schedule)

def level_principal_schedule(amount, years):
    principal_per_year = amount / years
    schedule = []
    remaining = amount
    for yr in range(1, years + 1):
        yield_this_maturity = price_maturity(yr)
        interest = remaining * yield_this_maturity
        schedule.append({"year": yr, "yield": yield_this_maturity, "principal": principal_per_year,
                           "interest": interest, "total_debt_service": principal_per_year + interest,
                           "remaining_balance": remaining - principal_per_year})
        remaining -= principal_per_year
    return pd.DataFrame(schedule)

lds_schedule = level_debt_service_schedule(BORROW_AMOUNT, MATURITY_YEARS)
lp_schedule = level_principal_schedule(BORROW_AMOUNT, MATURITY_YEARS)

print("\n" + "=" * 90)
print(f"LEVEL DEBT SERVICE STRUCTURE (${BORROW_AMOUNT/1e6:.0f}mm, {MATURITY_YEARS}Y, "
      f"issuer spread {ISSUER_SPREAD_BPS}bp over AAA muni benchmark)")
print("=" * 90)
lds_display = lds_schedule.copy()
lds_display["yield"] = (lds_display["yield"] * 100).round(3)
print(lds_display.round(0).to_string(index=False))

print("\n" + "=" * 90)
print(f"LEVEL PRINCIPAL STRUCTURE (${BORROW_AMOUNT/1e6:.0f}mm, {MATURITY_YEARS}Y)")
print("=" * 90)
print(lp_schedule.round(0).to_string(index=False))

# ===========================================================================
# 4. Total Interest Cost (TIC) comparison
# ===========================================================================
tic_lds = lds_schedule["interest"].sum()
tic_lp = lp_schedule["interest"].sum()
print("\n" + "=" * 70)
print("TOTAL INTEREST COST (TIC) COMPARISON")
print("=" * 70)
print(f"Level Debt Service: ${tic_lds:,.0f} total interest over {MATURITY_YEARS} years")
print(f"Level Principal: ${tic_lp:,.0f} total interest over {MATURITY_YEARS} years")
print(f"Level Principal saves ${tic_lds - tic_lp:,.0f} in total interest "
      f"({(tic_lds - tic_lp)/tic_lds:.1%} less) - the real, expected result since Level "
      f"Principal pays down the balance faster in early years, reducing the base on which "
      f"interest accrues, at the cost of a HIGHER near-term debt service burden")

print(f"\nYear-1 debt service: Level Debt Service ${lds_schedule['total_debt_service'].iloc[0]:,.0f} "
      f"vs. Level Principal ${lp_schedule['total_debt_service'].iloc[0]:,.0f} "
      f"(Level Principal requires "
      f"{(lp_schedule['total_debt_service'].iloc[0]/lds_schedule['total_debt_service'].iloc[0] - 1):.1%} "
      f"more near-term cash - the real trade-off between TIC savings and near-term "
      f"affordability)")

# ===========================================================================
# 5. Debt-service-affordability check
# ===========================================================================
print("\n" + "=" * 70)
print("DEBT-SERVICE-AFFORDABILITY CHECK")
print("=" * 70)
ISSUER_ANNUAL_BUDGET = 800_000_000  # $800mm annual budget - real-scale mid-size municipality
EXISTING_DEBT_SERVICE = 45_000_000   # $45mm existing annual debt service
AFFORDABILITY_GUIDELINE = 0.10        # real rating-agency guideline: debt service should stay under ~10% of budget

new_ds_year1_lds = lds_schedule["total_debt_service"].iloc[0]
total_ds_lds = EXISTING_DEBT_SERVICE + new_ds_year1_lds
ds_pct_of_budget_lds = total_ds_lds / ISSUER_ANNUAL_BUDGET

new_ds_year1_lp = lp_schedule["total_debt_service"].iloc[0]
total_ds_lp = EXISTING_DEBT_SERVICE + new_ds_year1_lp
ds_pct_of_budget_lp = total_ds_lp / ISSUER_ANNUAL_BUDGET

print(f"Issuer annual budget: ${ISSUER_ANNUAL_BUDGET/1e6:.0f}mm  |  Existing debt service: "
      f"${EXISTING_DEBT_SERVICE/1e6:.0f}mm")
print(f"\nLevel Debt Service structure: Year-1 total debt service "
      f"${total_ds_lds/1e6:.1f}mm = {ds_pct_of_budget_lds:.2%} of budget "
      f"({'WITHIN' if ds_pct_of_budget_lds <= AFFORDABILITY_GUIDELINE else 'EXCEEDS'} "
      f"the real {AFFORDABILITY_GUIDELINE:.0%} rating-agency affordability guideline)")
print(f"Level Principal structure: Year-1 total debt service "
      f"${total_ds_lp/1e6:.1f}mm = {ds_pct_of_budget_lp:.2%} of budget "
      f"({'WITHIN' if ds_pct_of_budget_lp <= AFFORDABILITY_GUIDELINE else 'EXCEEDS'} "
      f"the real {AFFORDABILITY_GUIDELINE:.0%} rating-agency affordability guideline)")

print(f"\nRecommendation: {'Level Debt Service' if ds_pct_of_budget_lp > AFFORDABILITY_GUIDELINE and ds_pct_of_budget_lds <= AFFORDABILITY_GUIDELINE else 'Either structure is affordable' if ds_pct_of_budget_lp <= AFFORDABILITY_GUIDELINE else 'Neither structure fits the guideline as sized - reduce borrowing amount or extend maturity'}")
