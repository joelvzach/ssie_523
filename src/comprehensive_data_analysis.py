"""
Comprehensive Data Analysis for Global Tourism Simulation

Analyzes all available datasets: UN Tourism, OECD, World Bank
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Setup paths
DATA_ROOT = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_ROOT / "analysis_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Set plot style
sns.set_theme(style="whitegrid", font_scale=1.1)

print("=" * 80)
print("COMPREHENSIVE GLOBAL TOURISM DATA ANALYSIS")
print("=" * 80)

# ============================================================================
# 1. UN TOURISM DATA ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 1: UN TOURISM DATA")
print("=" * 80)

un_tourism_dir = DATA_ROOT / "UN_Tourism/extracted"

# Load key datasets
print("\nLoading UN Tourism datasets...")

datasets = {
    "inbound_arrivals": "UN_Tourism_inbound_arrivals_12_2025.csv",
    "outbound_departures": "UN_Tourism_outbound_departures_12_2025.csv",
    "domestic_trips": "UN_Tourism_domestic_trips_12_2025.csv",
    "inbound_expenditure": "UN_Tourism_inbound_expenditure_12_2025.csv",
    "outbound_expenditure": "UN_Tourism_outbound_expenditure_12_2025.csv",
}

un_data = {}
for name, filename in datasets.items():
    filepath = un_tourism_dir / filename
    if filepath.exists():
        df = pd.read_csv(filepath)
        un_data[name] = df
        print(
            f"  ✓ {name}: {len(df):,} records, {df['reporter_area_label'].nunique()} countries"
        )

# Focus on total arrivals for main analysis
df_arrivals = un_data["inbound_arrivals"]

# Filter to total arrivals (all visitors)
# Available: INBD_TRIP_TOTL_TOTL_VSTR (total visitors), INBD_TRIP_TOTL_TOTL_TOUR (tourists only)
total_arrivals = df_arrivals[
    df_arrivals["indicator_code"] == "INBD_TRIP_TOTL_TOTL_VSTR"
].copy()

print(f"\n=== Total International Arrivals (All Visitors) ===")
print(f"Records: {len(total_arrivals):,}")
print(f"Countries: {total_arrivals['reporter_area_label'].nunique()}")
print(f"Year range: {total_arrivals['year'].min()} - {total_arrivals['year'].max()}")

# Aggregate by year (global totals)
global_arrivals = total_arrivals.groupby("year")["value"].sum().reset_index()
global_arrivals.columns = ["year", "total_arrivals"]

print(f"\nGlobal Arrivals by Year (millions):")
for _, row in global_arrivals.iterrows():
    print(f"  {row['year']}: {row['total_arrivals'] / 1e6:.1f}M")

# Top destinations (2019 pre-pandemic)
arrivals_2019 = total_arrivals[total_arrivals["year"] == 2019].copy()
top_2019 = arrivals_2019.nlargest(20, "value")

print(f"\nTop 20 Destinations (2019):")
for _, row in top_2019.iterrows():
    print(f"  {row['reporter_area_label']:25s}: {row['value'] / 1e6:>8.1f}M")

# Pandemic impact analysis
arrivals_2020 = total_arrivals[total_arrivals["year"] == 2020].copy()

# Merge 2019 and 2020 for comparison
comparison = pd.merge(
    arrivals_2019[["reporter_area_label", "value"]].rename(
        columns={"value": "arrivals_2019"}
    ),
    arrivals_2020[["reporter_area_label", "value"]].rename(
        columns={"value": "arrivals_2020"}
    ),
    on="reporter_area_label",
    how="inner",
)
comparison["change_pct"] = (
    (comparison["arrivals_2020"] - comparison["arrivals_2019"])
    / comparison["arrivals_2019"]
    * 100
)

print(f"\n=== Pandemic Impact (2020 vs 2019) ===")
print(f"Countries with data: {len(comparison)}")
print(f"Average change: {comparison['change_pct'].mean():.1f}%")
print(f"Median change: {comparison['change_pct'].median():.1f}%")

# Most affected countries
most_affected = comparison.nsmallest(10, "change_pct")
print(f"\nMost Affected Countries (Top 10 declines):")
for _, row in most_affected.iterrows():
    print(f"  {row['reporter_area_label']:25s}: {row['change_pct']:.1f}%")

# Recovery analysis (2024 vs 2019)
arrivals_2024 = total_arrivals[total_arrivals["year"] == 2024].copy()

recovery = pd.merge(
    arrivals_2019[["reporter_area_label", "value"]].rename(
        columns={"value": "arrivals_2019"}
    ),
    arrivals_2024[["reporter_area_label", "value"]].rename(
        columns={"value": "arrivals_2024"}
    ),
    on="reporter_area_label",
    how="inner",
)
recovery["recovery_pct"] = recovery["arrivals_2024"] / recovery["arrivals_2019"] * 100

print(f"\n=== Recovery Status (2024 vs 2019 baseline) ===")
print(f"Countries with data: {len(recovery)}")
print(f"Average recovery: {recovery['recovery_pct'].mean():.1f}%")
print(f"Median recovery: {recovery['recovery_pct'].median():.1f}%")
print(
    f"Countries fully recovered (>100%): {(recovery['recovery_pct'] > 100).sum()} ({(recovery['recovery_pct'] > 100).mean() * 100:.1f}%)"
)

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Global arrivals over time
ax1 = axes[0, 0]
ax1.plot(
    global_arrivals["year"],
    global_arrivals["total_arrivals"] / 1e9,
    marker="o",
    linewidth=2,
    markersize=6,
)
ax1.set_xlabel("Year", fontsize=12)
ax1.set_ylabel("Billions of Arrivals", fontsize=12)
ax1.set_title(
    "Global International Tourist Arrivals (1995-2024)", fontsize=14, fontweight="bold"
)
ax1.grid(True, alpha=0.3)
ax1.axvspan(2020, 2024, alpha=0.2, color="red", label="Pandemic period")
ax1.legend()

# Plot 2: YoY growth rate
ax2 = axes[0, 1]
global_arrivals["yoy_growth"] = global_arrivals["total_arrivals"].pct_change() * 100
ax2.bar(
    global_arrivals["year"], global_arrivals["yoy_growth"], color="steelblue", alpha=0.7
)
ax2.set_xlabel("Year", fontsize=12)
ax2.set_ylabel("YoY Growth (%)", fontsize=12)
ax2.set_title("Year-over-Year Growth Rate", fontsize=14, fontweight="bold")
ax2.grid(True, alpha=0.3, axis="y")
ax2.axhline(y=0, color="red", linestyle="--", alpha=0.5)
ax2.axvspan(2020, 2024, alpha=0.2, color="red")

# Plot 3: 2019 ranking (top 20)
ax3 = axes[1, 0]
top_20_countries = arrivals_2019.nlargest(20, "value")
ax3.barh(range(len(top_20_countries)), top_20_countries["value"] / 1e6, color="coral")
ax3.set_yticks(range(len(top_20_countries)))
ax3.set_yticklabels(top_20_countries["reporter_area_label"])
ax3.set_xlabel("Millions of Arrivals (2019)", fontsize=12)
ax3.set_title("Top 20 Destinations (Pre-Pandemic 2019)", fontsize=14, fontweight="bold")
ax3.grid(True, alpha=0.3)

# Plot 4: Recovery distribution
ax4 = axes[1, 1]
ax4.hist(
    recovery["recovery_pct"], bins=30, color="seagreen", alpha=0.7, edgecolor="black"
)
ax4.set_xlabel("Recovery Rate (% of 2019)", fontsize=12)
ax4.set_ylabel("Number of Countries", fontsize=12)
ax4.set_title(
    "Recovery Status Distribution (2024 vs 2019)", fontsize=14, fontweight="bold"
)
ax4.axvline(x=100, color="red", linestyle="--", linewidth=2, label="Full recovery")
ax4.axvline(
    x=recovery["recovery_pct"].mean(),
    color="blue",
    linestyle="-",
    linewidth=2,
    label=f"Mean: {recovery['recovery_pct'].mean():.0f}%",
)
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "un_tourism_analysis.png", dpi=300, bbox_inches="tight")
print(f"\n✓ Saved visualization: {OUTPUT_DIR / 'un_tourism_analysis.png'}")
plt.close()

# ============================================================================
# 2. OECD DATA ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 2: OECD TOURISM DATA")
print("=" * 80)

oecd_dir = DATA_ROOT / "OECD"

# Load OECD datasets
print("\nLoading OECD datasets...")

oecd_files = {
    "inbound": "inbound_tourism.csv",
    "outbound": "outbound_tourism.csv",
    "domestic": "domestic_tourism.csv",
    "economic": "key_tourism_economic_indicators.csv",
}

oecd_data = {}
for name, filename in oecd_files.items():
    filepath = oecd_dir / filename
    if filepath.exists():
        df = pd.read_csv(filepath, low_memory=False)
        oecd_data[name] = df
        print(f"  ✓ {name}: {len(df):,} records")

# Analyze inbound tourism
df_oecd_inbound = oecd_data["inbound"]

# Extract country and year data
oecd_countries = df_oecd_inbound["Reference area"].unique()
print(f"\n=== OECD Inbound Tourism ===")
print(f"Countries: {len(oecd_countries)}")
print(f"Sample countries: {list(oecd_countries[:10])}")

# Filter to nights spent (most complete metric)
nights_data = df_oecd_inbound[df_oecd_inbound["Measure"] == "NIGHTS_ACCOM"].copy()

if len(nights_data) > 0:
    # Aggregate by country and year
    nights_pivot = nights_data.pivot_table(
        index=["Reference area", "Time period"],
        values="Observation value",
        aggfunc="sum",
    ).reset_index()

    print(f"\nNights spent data: {len(nights_pivot):,} records")

    # Latest year (2023 or most recent)
    latest_year = nights_pivot["Time period"].max()
    nights_2023 = nights_pivot[nights_pivot["Time period"] == latest_year]

    print(f"\nTop 10 OECD destinations by nights spent ({latest_year}):")
    top_10 = nights_2023.nlargest(10, "Observation value")
    for _, row in top_10.iterrows():
        print(
            f"  {row['Reference area']:20s}: {row['Observation value'] / 1e6:>6.1f}M nights"
        )

# Economic indicators
df_oecd_economic = oecd_data["economic"]

print(f"\n=== OECD Economic Indicators ===")
measures = df_oecd_economic["Measure"].unique()
print(f"Available measures: {list(measures)}")

# Tourism GDP share
gdp_share = df_oecd_economic[df_oecd_economic["Measure"] == "GDP_SH"].copy()
if len(gdp_share) > 0:
    latest_gdp = gdp_share.groupby("Time period")["Observation value"].mean()
    print(f"\nAverage tourism share of GDP (OECD):")
    for year, value in latest_gdp.items():
        if pd.notna(value):
            print(f"  {year}: {value:.2f}%")

# ============================================================================
# 3. DATA COMPARISON: UN TOURISM vs OECD
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 3: DATA COMPARISON (UN Tourism vs OECD)")
print("=" * 80)

# Compare arrivals for overlapping countries
# Get UN Tourism totals by indicator
un_totals = total_arrivals[total_arrivals["year"] == 2019].copy()

# Get OECD totals (approximate from nights)
oecd_2019 = (
    nights_pivot[nights_pivot["Time period"] == 2019].copy()
    if "nights_pivot" in dir()
    else None
)

print("\n=== Coverage Comparison ===")
print(f"UN Tourism countries (2019): {len(un_totals)}")
print(f"OECD countries (2019): {len(oecd_2019) if oecd_2019 is not None else 'N/A'}")

# Find overlapping countries
if oecd_2019 is not None:
    un_countries = set(un_totals["reporter_area_label"])
    oecd_countries_set = set(oecd_2019["Reference area"])
    overlap = un_countries & oecd_countries_set
    print(f"Overlapping countries: {len(overlap)}")
    print(f"UN Tourism only: {len(un_countries - oecd_countries_set)}")
    print(f"OECD only: {len(oecd_countries_set - un_countries)}")

# ============================================================================
# 4. KEY INSIGHTS FOR SIMULATION
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 4: KEY INSIGHTS FOR SIMULATION")
print("=" * 80)

# Calculate baseline growth rate (pre-pandemic)
pre_pandemic = global_arrivals[global_arrivals["year"] < 2020].copy()
pre_pandemic["yoy"] = pre_pandemic["total_arrivals"].pct_change()
baseline_cagr = (
    pre_pandemic.loc[pre_pandemic["year"] == 2019, "total_arrivals"].values[0]
    / pre_pandemic.loc[pre_pandemic["year"] == 2010, "total_arrivals"].values[0]
) ** (1 / 9) - 1

print("\n=== Baseline Parameters ===")
print(f"Pre-pandemic CAGR (2010-2019): {baseline_cagr * 100:.2f}%")
print(f"Average YoY growth (2010-2019): {pre_pandemic['yoy'].mean() * 100:.2f}%")
print(f"Growth volatility (std dev): {pre_pandemic['yoy'].std() * 100:.2f}%")

# Pandemic shock magnitude
arrivals_2019_total = global_arrivals[global_arrivals["year"] == 2019][
    "total_arrivals"
].values[0]
arrivals_2020_total = global_arrivals[global_arrivals["year"] == 2020][
    "total_arrivals"
].values[0]
shock_magnitude = (arrivals_2020_total - arrivals_2019_total) / arrivals_2019_total

print(f"\n=== Shock Parameters ===")
print(f"Pandemic shock magnitude (2020 vs 2019): {shock_magnitude * 100:.1f}%")
print(
    f"Recovery time (to 100%): {(recovery['recovery_pct'] > 100).mean() * 100:.1f}% of countries by 2024"
)

# Heterogeneity insights
print(f"\n=== Heterogeneity Insights ===")
print(f"Recovery rate std dev: {recovery['recovery_pct'].std():.1f}%")
print(
    f"Best recovery: {recovery.nlargest(1, 'recovery_pct')['reporter_area_label'].values[0]} ({recovery['recovery_pct'].max():.0f}%)"
)
print(
    f"Worst recovery: {recovery.nsmallest(1, 'recovery_pct')['reporter_area_label'].values[0]} ({recovery['recovery_pct'].min():.0f}%)"
)

# Regional analysis
print(f"\n=== Regional Patterns (2024 Recovery) ===")
# Simple regional grouping by first letter or known regions
regions = {
    "Europe": [
        "France",
        "Germany",
        "Italy",
        "Spain",
        "United Kingdom",
        "Greece",
        "Portugal",
        "Netherlands",
    ],
    "Asia-Pacific": [
        "China",
        "Japan",
        "Thailand",
        "Australia",
        "Singapore",
        "Malaysia",
        "Indonesia",
    ],
    "Americas": [
        "United States",
        "Canada",
        "Mexico",
        "Brazil",
        "Argentina",
        "Colombia",
    ],
    "Middle East": [
        "United Arab Emirates",
        "Saudi Arabia",
        "Turkey",
        "Israel",
        "Egypt",
    ],
    "Africa": ["South Africa", "Morocco", "Tunisia", "Kenya"],
}

for region, countries in regions.items():
    region_recovery = recovery[recovery["reporter_area_label"].isin(countries)]
    if len(region_recovery) > 0:
        avg_recovery = region_recovery["recovery_pct"].mean()
        print(f"  {region:15s}: {avg_recovery:.0f}% of 2019 (n={len(region_recovery)})")

# ============================================================================
# 5. SAVE SUMMARY STATISTICS
# ============================================================================

summary_stats = {
    "metric": [
        "Total countries (UN Tourism)",
        "Time coverage",
        "Pre-pandemic CAGR",
        "Pandemic shock (2020)",
        "Recovery rate (2024 avg)",
        "Countries fully recovered",
        "OECD countries",
        "OECD avg tourism GDP share",
    ],
    "value": [
        f"{total_arrivals['reporter_area_label'].nunique()}",
        f"{total_arrivals['year'].min()}-{total_arrivals['year'].max()}",
        f"{baseline_cagr * 100:.2f}%",
        f"{shock_magnitude * 100:.1f}%",
        f"{recovery['recovery_pct'].mean():.1f}%",
        f"{(recovery['recovery_pct'] > 100).sum()}",
        f"{len(oecd_countries)}",
        f"{gdp_share['Observation value'].mean():.2f}%"
        if len(gdp_share) > 0
        else "N/A",
    ],
}

summary_df = pd.DataFrame(summary_stats)
summary_df.to_csv(OUTPUT_DIR / "summary_statistics.csv", index=False)
print(f"\n✓ Saved summary statistics: {OUTPUT_DIR / 'summary_statistics.csv'}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"\nOutput files saved to: {OUTPUT_DIR}")
print(f"  - un_tourism_analysis.png (visualizations)")
print(f"  - summary_statistics.csv (key metrics)")
