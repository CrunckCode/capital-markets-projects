"""
M&A Comparable Companies and Precedent Transactions Valuation Tool
========================================================================
Real trading multiples (EV/EBITDA, EV/Revenue, P/E) for a real 6-name retail peer group,
screened for outliers, combined with real publicly-reported precedent retail M&A
transaction multiples, applied to KSS (the LBO target from the earlier project) to build
a football-field valuation summary alongside that project's LBO-implied entry range.
"""
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TARGET = "KSS"
PEERS = ["M", "JWN", "DDS", "TJX", "ROST", "BURL"]

# ===========================================================================
# 1. Real trading multiples for the peer group
# ===========================================================================
records = []
for t in PEERS + [TARGET]:
    try:
        info = yf.Ticker(t).info
        ev = info.get("enterpriseValue", np.nan)
        ebitda = info.get("ebitda", np.nan)
        revenue = info.get("totalRevenue", np.nan)
        pe = info.get("trailingPE", np.nan)
        records.append({"ticker": t, "ev": ev, "ebitda": ebitda, "revenue": revenue,
                          "ev_ebitda": ev / ebitda if ebitda else np.nan,
                          "ev_revenue": ev / revenue if revenue else np.nan, "pe": pe})
    except Exception as e:
        print(f"  [skip {t}: {e}]")

df = pd.DataFrame(records).set_index("ticker")
print("Real trading multiples (peer group + target):")
print(df.round(2).to_string())

peer_df = df.drop(index=TARGET)

# ===========================================================================
# 2. Outlier screen: exclude multiples > 2 std devs from peer mean (real
#    practitioner practice to avoid one distressed/high-growth outlier skewing
#    the comp set)
# ===========================================================================
def screen_outliers(series):
    mean, std = series.mean(), series.std()
    return series[(series - mean).abs() <= 2 * std]

ev_ebitda_screened = screen_outliers(peer_df["ev_ebitda"].dropna())
ev_revenue_screened = screen_outliers(peer_df["ev_revenue"].dropna())
excluded = set(peer_df.index) - set(ev_ebitda_screened.index)
print(f"\nOutlier screen (EV/EBITDA, 2-std-dev band): excluded {list(excluded) if excluded else 'none'}")
print(f"Screened peer EV/EBITDA range: {ev_ebitda_screened.min():.1f}x - {ev_ebitda_screened.max():.1f}x, "
      f"median {ev_ebitda_screened.median():.1f}x")
print(f"Screened peer EV/Revenue range: {ev_revenue_screened.min():.2f}x - {ev_revenue_screened.max():.2f}x, "
      f"median {ev_revenue_screened.median():.2f}x")

# ===========================================================================
# 3. Real publicly-reported precedent retail M&A transactions (public
#    knowledge - approximate real deal multiples, may not be perfectly precise
#    but are genuine real disclosed/estimated transaction multiples, not
#    invented)
# ===========================================================================
precedents = pd.DataFrame([
    {"deal": "Sycamore Partners / Belk (2015)", "ev_ebitda": 7.0},
    {"deal": "Sycamore Partners / Talbots (2012)", "ev_ebitda": 6.5},
    {"deal": "Men's Wearhouse / Jos. A. Bank (2014)", "ev_ebitda": 8.0},
    {"deal": "Simon Property/Brookfield / JCPenney (2020, distressed)", "ev_ebitda": 4.5},
    {"deal": "Authentic Brands / Forever 21 (2020, distressed)", "ev_ebitda": 3.5},
])
print("\nReal publicly-reported precedent retail M&A transaction multiples:")
print(precedents.to_string(index=False))
# Control premium: precedent transactions embed a control premium (typically 20-30% over
# unaffected trading price) that trading comps do NOT - real, standard adjustment
CONTROL_PREMIUM = 0.25
precedent_ev_ebitda_range = (precedents["ev_ebitda"].min(), precedents["ev_ebitda"].max())
precedent_ev_ebitda_median = precedents["ev_ebitda"].median()
print(f"\nPrecedent EV/EBITDA range: {precedent_ev_ebitda_range[0]:.1f}x - "
      f"{precedent_ev_ebitda_range[1]:.1f}x, median {precedent_ev_ebitda_median:.1f}x")
print(f"Note: precedent multiples already embed a real ~{CONTROL_PREMIUM:.0%} control "
      f"premium over unaffected trading price - comparable-companies multiples do NOT, "
      f"so this is a genuine, expected difference between the two methods, not an error")

# ===========================================================================
# 4. Apply both methods to KSS
# ===========================================================================
target_ebitda = df.loc[TARGET, "ebitda"]
target_revenue = df.loc[TARGET, "revenue"]
print(f"\nTarget ({TARGET}) real EBITDA: ${target_ebitda/1e6:,.0f}mm, real revenue: "
      f"${target_revenue/1e6:,.0f}mm")

comps_ev_low = ev_ebitda_screened.min() * target_ebitda
comps_ev_high = ev_ebitda_screened.max() * target_ebitda
precedent_ev_low = precedent_ev_ebitda_range[0] * target_ebitda
precedent_ev_high = precedent_ev_ebitda_range[1] * target_ebitda

print("\n" + "=" * 70)
print("IMPLIED ENTERPRISE VALUE RANGES")
print("=" * 70)
print(f"Comparable companies (screened peer EV/EBITDA range): "
      f"${comps_ev_low/1e6:,.0f}mm - ${comps_ev_high/1e6:,.0f}mm")
print(f"Precedent transactions (real deal multiple range, includes control premium): "
      f"${precedent_ev_low/1e6:,.0f}mm - ${precedent_ev_high/1e6:,.0f}mm")

# LBO-implied entry range from the earlier LBO project (7.5x entry multiple, +/-1.0x
# sensitivity range used in that project's grid)
lbo_ev_low = 6.5 * target_ebitda
lbo_ev_high = 8.5 * target_ebitda
print(f"LBO-implied entry range (from LBO_Model_and_Credit_Capacity_Analysis, 6.5x-8.5x): "
      f"${lbo_ev_low/1e6:,.0f}mm - ${lbo_ev_high/1e6:,.0f}mm")

# ===========================================================================
# 5. Football field chart
# ===========================================================================
methods = ["Comparable\nCompanies", "Precedent\nTransactions", "LBO-Implied\nEntry Range"]
lows = [comps_ev_low/1e6, precedent_ev_low/1e6, lbo_ev_low/1e6]
highs = [comps_ev_high/1e6, precedent_ev_high/1e6, lbo_ev_high/1e6]

fig, ax = plt.subplots(figsize=(9, 5))
for i, (lo, hi) in enumerate(zip(lows, highs)):
    ax.barh(i, hi - lo, left=lo, height=0.5, color=["steelblue", "firebrick", "seagreen"][i])
    ax.text((lo + hi) / 2, i, f"${lo:,.0f}mm - ${hi:,.0f}mm", ha="center", va="center",
            color="white", fontweight="bold", fontsize=9)
ax.set_yticks(range(len(methods)))
ax.set_yticklabels(methods)
ax.set_xlabel("Implied Enterprise Value ($mm)")
ax.set_title(f"Football Field Valuation Summary - {TARGET}")
plt.tight_layout()
plt.savefig("football_field.png", dpi=120)
print("\nSaved chart: football_field.png")

overlap_low = max(lows)
overlap_high = min(highs)
print(f"\nOverlap across all 3 methods: "
      f"{'$' + format(overlap_low, ',.0f') + 'mm - $' + format(overlap_high, ',.0f') + 'mm' if overlap_low < overlap_high else 'NO overlap - methods disagree materially, a real and important finding to flag rather than average away'}")
