"""
Create Comprehensive Merged Tourism Dataset

This script merges all available data sources into a single source of truth:
- UN Tourism (arrivals, departures, expenditure)
- OECD (economic indicators, nights spent)
- ACLED (conflict/risk data)
- WEF TTDI (attractiveness scores)
- Numbeo (cost of living)
- WHO (air quality)
- UNESCO (heritage sites)
- World Bank (political stability, policy assessment)
- Climate data (temperature extremes)

Output: tourism_comprehensive_1995_2024.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

# Setup paths
DATA_ROOT = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_ROOT / "merged"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("CREATING COMPREHENSIVE MERGED TOURISM DATASET")
print("=" * 80)

# ============================================================================
# 1. LOAD ALL DATA SOURCES
# ============================================================================

print("\n[1/8] Loading data sources...")

# 1.1 UN Tourism - Inbound Arrivals (primary metric)
print("  Loading UN Tourism inbound arrivals...")
un_arrivals = pd.read_csv(
    DATA_ROOT / "UN_Tourism/extracted/UN_Tourism_inbound_arrivals_12_2025.csv"
)
# Filter to total visitors
un_arrivals = un_arrivals[
    un_arrivals["indicator_code"] == "INBD_TRIP_TOTL_TOTL_VSTR"
].copy()
un_arrivals = un_arrivals.rename(
    columns={
        "reporter_area_code": "country_code",
        "reporter_area_label": "country_name",
        "year": "year",
        "value": "tourist_arrivals",
    }
)[["country_code", "country_name", "year", "tourist_arrivals"]]

# 1.2 UN Tourism - Inbound Expenditure
# FIX: Filter to TOTAL indicator only to avoid duplication
# The dataset contains 3 indicators: passenger transport, travel, and total
# TOTAL = passenger transport + travel, so we use only TOTAL to avoid 3x duplication
print("  Loading UN Tourism inbound expenditure (TOTAL indicator only)...")
un_expenditure = pd.read_csv(
    DATA_ROOT / "UN_Tourism/extracted/UN_Tourism_inbound_expenditure_12_2025.csv"
)
# Filter to TOTAL indicator (includes both passenger transport and travel)
un_expenditure = un_expenditure[
    un_expenditure["indicator_code"] == "INBD_EXPD_BPAY_TOTL_VSTR"
].copy()
un_expenditure = un_expenditure.rename(
    columns={
        "reporter_area_code": "country_code",
        "reporter_area_label": "country_name",
        "year": "year",
        "value": "tourism_expenditure_usd_millions",
    }
)[["country_code", "country_name", "year", "tourism_expenditure_usd_millions"]]

# 1.3 OECD - Economic Indicators
print("  Loading OECD economic indicators...")
oecd_economic = pd.read_csv(
    DATA_ROOT / "OECD/key_tourism_economic_indicators.csv", low_memory=False
)
# Filter to GDP share
oecd_gdp = oecd_economic[oecd_economic["Measure"] == "GDP_SH"].copy()
oecd_gdp = oecd_gdp.rename(
    columns={
        "Reference area": "country_name",
        "Time period": "year",
        "Observation value": "tourism_gdp_share_pct",
    }
)[["country_name", "year", "tourism_gdp_share_pct"]]

# 1.4 ACLED - Conflict Events (risk factor)
print("  Loading ACLED conflict data...")
acled_files = [
    "Africa_aggregated_data_up_to_week_of-2026-03-21.csv",
    "Asia-Pacific_aggregated_data_up_to_week_of-2026-03-28.csv",
    "Europe-Central-Asia_aggregated_data_up_to_week_of-2026-03-28.csv",
    "Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-03-21.csv",
    "Middle-East_aggregated_data_up_to_week_of-2026-03-21.csv",
    "US-and-Canada_aggregated_data_up_to_week_of-2026-03-28.csv",
]

acled_data = []
for f in acled_files:
    filepath = DATA_ROOT / "ACLED" / "csv" / f
    if filepath.exists():
        df = pd.read_csv(filepath)
        if "YEAR" in df.columns:
            acled_data.append(df[["COUNTRY", "YEAR", "EVENTS", "FATALITIES"]])

if acled_data:
    acled_merged = pd.concat(acled_data, ignore_index=True)
    acled_merged = (
        acled_merged.groupby(["COUNTRY", "YEAR"])[["EVENTS", "FATALITIES"]]
        .sum()
        .reset_index()
    )
    acled_merged = acled_merged.rename(
        columns={
            "COUNTRY": "country_name",
            "YEAR": "year",
            "EVENTS": "conflict_events",
            "FATALITIES": "conflict_fatalities",
        }
    )
else:
    acled_merged = pd.DataFrame()

# 1.5 WEF TTDI - Attractiveness Scores
print("  Loading WEF TTDI scores...")
ttdi = pd.read_csv(DATA_ROOT / "WEF" / "ttdi_scores_2024.csv")
ttdi = ttdi.rename(columns={"country": "country_name", "year": "year"})
# TTDI is only for 2024, will need to forward-fill for earlier years

# 1.6 Numbeo - Cost of Living
print("  Loading Numbeo cost of living...")
numbeo = pd.read_csv(DATA_ROOT / "enhanced_data" / "numbeo_cost_of_living.csv")
numbeo = numbeo.rename(
    columns={"Country": "country_name", "Cost of Living Index": "cost_of_living_index"}
)[["country_name", "cost_of_living_index"]]

# 1.7 WHO - Air Quality
print("  Loading WHO air quality data...")
who_aq = pd.read_csv(DATA_ROOT / "enhanced_data" / "who_air_quality_pm25.csv")
who_aq = who_aq.rename(
    columns={
        "Entity": "country_name",
        "Year": "year",
        "PM2.5 air pollution, mean annual exposure (micrograms per cubic meter)": "pm25_concentration",
    }
)[["country_name", "year", "pm25_concentration"]]

# 1.8 UNESCO - Heritage Sites
print("  Loading UNESCO heritage sites...")
unesco = pd.read_csv(DATA_ROOT / "enhanced_data" / "unesco_world_heritage_sites.csv")
unesco = unesco.rename(
    columns={"country": "country_name", "total_sites": "unesco_heritage_sites"}
)

# 1.9 World Bank - Political Stability
print("  Loading World Bank political stability...")
wb_stability = pd.read_csv(
    DATA_ROOT / "enhanced_data" / "world_bank_political_stability.csv"
)
wb_stability = wb_stability.rename(
    columns={
        "country_code": "country_code",
        "year": "year",
        "political_stability": "political_stability_score",
    }
)

# ============================================================================
# 2. STANDARDIZE COUNTRY NAMES
# ============================================================================

print("\n[2/8] Standardizing country names...")

# Create a country name mapping for consistency
country_mapping = {
    "Korea, Rep.": "South Korea",
    "United States": "United States",
    "United Kingdom": "United Kingdom",
    "Türkiye": "Turkey",
    "Iran, Islamic Rep.": "Iran",
    "Viet Nam": "Vietnam",
    "Lao PDR": "Laos",
    "Kyrgyz Republic": "Kyrgyzstan",
    "Côte d'Ivoire": "Ivory Coast",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Trinidad and Tobago": "Trinidad and Tobago",
    "North Macedonia": "North Macedonia",
    "Slovak Republic": "Slovakia",
    "People's Republic of China": "China",
    "Russian Federation": "Russia",
    "Islamic Republic of Iran": "Iran",
}


def standardize_country_name(name):
    """Standardize country names across datasets"""
    if pd.isna(name):
        return name
    name = str(name).strip()
    return country_mapping.get(name, name)


# Apply standardization to all datasets
for df in [un_arrivals, un_expenditure, oecd_gdp, ttdi, numbeo, who_aq, unesco]:
    if "country_name" in df.columns:
        df["country_name"] = df["country_name"].apply(standardize_country_name)

if not acled_merged.empty:
    acled_merged["country_name"] = acled_merged["country_name"].apply(
        standardize_country_name
    )

# ============================================================================
# 3. CREATE COUNTRY CODE MAPPING
# ============================================================================

print("\n[3/8] Creating country code mapping...")

# Use UN Tourism country codes as the reference
country_codes = un_arrivals[["country_code", "country_name"]].drop_duplicates()

# Create mapping dictionary
code_to_name = dict(zip(country_codes["country_code"], country_codes["country_name"]))
name_to_code = dict(zip(country_codes["country_name"], country_codes["country_code"]))

# ============================================================================
# 4. MERGE DATASETS
# ============================================================================

print("\n[4/8] Merging datasets...")

# Start with UN Tourism arrivals as the base
merged = un_arrivals.copy()

# Merge UN Tourism expenditure
merged = pd.merge(
    merged, un_expenditure, on=["country_code", "country_name", "year"], how="left"
)

# Merge OECD GDP share
merged = pd.merge(merged, oecd_gdp, on=["country_name", "year"], how="left")

# Merge ACLED conflict data
if not acled_merged.empty:
    merged = pd.merge(merged, acled_merged, on=["country_name", "year"], how="left")

# Merge WHO air quality
merged = pd.merge(merged, who_aq, on=["country_name", "year"], how="left")

# Merge WEF TTDI (only 2024, will forward-fill later)
ttdi_2024 = ttdi[ttdi["year"] == 2024][["country_name", "ttdi_score"]].drop_duplicates()
merged = pd.merge(merged, ttdi_2024, on="country_name", how="left")

# Merge Numbeo cost of living (cross-sectional, no year)
merged = pd.merge(
    merged,
    numbeo[["country_name", "cost_of_living_index"]],
    on="country_name",
    how="left",
)

# Merge UNESCO heritage sites (cross-sectional, no year)
merged = pd.merge(merged, unesco, on="country_name", how="left")

# ============================================================================
# 5. CALCULATE DERIVED METRICS
# ============================================================================

print("\n[5/8] Calculating derived metrics...")

# Risk score from ACLED data (normalize 0-1)
if "conflict_events" in merged.columns:
    max_events = merged["conflict_events"].max()
    if max_events > 0:
        merged["risk_score"] = merged["conflict_events"] / max_events
    else:
        merged["risk_score"] = 0.0
else:
    merged["risk_score"] = 0.0

# Air quality index (normalize, inverse - lower PM2.5 = better)
if "pm25_concentration" in merged.columns:
    max_pm25 = merged["pm25_concentration"].max()
    if max_pm25 > 0:
        merged["air_quality_index"] = 1 - (merged["pm25_concentration"] / max_pm25)
    else:
        merged["air_quality_index"] = 1.0
else:
    merged["air_quality_index"] = 1.0

# Cost index (normalize 0-1, inverse - lower cost = better for budget travelers)
if "cost_of_living_index" in merged.columns:
    max_cost = merged["cost_of_living_index"].max()
    if max_cost > 0:
        merged["cost_index"] = merged["cost_of_living_index"] / max_cost
        merged["affordability_index"] = 1 - merged["cost_index"]
    else:
        merged["cost_index"] = 0.5
        merged["affordability_index"] = 0.5
else:
    merged["cost_index"] = 0.5
    merged["affordability_index"] = 0.5

# Normalize TTDI score (0-1 scale)
if "ttdi_score" in merged.columns:
    # TTDI scores range from ~2.8 to ~5.2
    merged["attractiveness_index"] = (merged["ttdi_score"] - 2.5) / 3.0
    merged["attractiveness_index"] = merged["attractiveness_index"].clip(0, 1)
else:
    merged["attractiveness_index"] = 0.5

# Heritage sites per capita (proxy for cultural attractiveness)
if "unesco_heritage_sites" in merged.columns:
    merged["heritage_sites"] = merged["unesco_heritage_sites"]
else:
    merged["heritage_sites"] = 0

# ============================================================================
# 6. FORWARD-FILL TIME-SERIES DATA
# ============================================================================

print("\n[6/8] Forward-filling time-series data...")

# Sort by country and year
merged = merged.sort_values(["country_code", "year"]).reset_index(drop=True)

# Forward fill TTDI scores (assume relatively stable)
merged["ttdi_score"] = merged.groupby("country_code")["ttdi_score"].ffill().bfill()
merged["attractiveness_index"] = (
    merged.groupby("country_code")["attractiveness_index"].ffill().bfill()
)

# Forward fill cross-sectional data
for col in ["cost_of_living_index", "affordability_index", "heritage_sites"]:
    if col in merged.columns:
        merged[col] = merged.groupby("country_code")[col].ffill().bfill()

# ============================================================================
# 7. DATA QUALITY CHECKS
# ============================================================================

print("\n[7/8] Running data quality checks...")

print(f"\n  Total records: {len(merged):,}")
print(f"  Countries: {merged['country_name'].nunique()}")
print(f"  Year range: {merged['year'].min()} - {merged['year'].max()}")

# Check completeness
completeness = {
    "tourist_arrivals": merged["tourist_arrivals"].notna().mean() * 100,
    "tourism_expenditure": merged["tourism_expenditure_usd_millions"].notna().mean()
    * 100,
    "ttdi_score": merged["ttdi_score"].notna().mean() * 100,
    "risk_score": merged["risk_score"].notna().mean() * 100,
    "cost_of_living": merged["cost_of_living_index"].notna().mean() * 100,
    "air_quality": merged["pm25_concentration"].notna().mean() * 100,
}

print(f"\n  Data completeness:")
for metric, pct in completeness.items():
    print(f"    {metric:25s}: {pct:5.1f}%")

# ============================================================================
# 8. SAVE MERGED DATASET
# ============================================================================

print("\n[8/8] Saving merged dataset...")

# Select final columns
final_columns = [
    "country_code",
    "country_name",
    "year",
    "tourist_arrivals",
    "tourism_expenditure_usd_millions",
    "tourism_gdp_share_pct",
    "ttdi_score",
    "attractiveness_index",
    "cost_of_living_index",
    "affordability_index",
    "pm25_concentration",
    "air_quality_index",
    "conflict_events",
    "conflict_fatalities",
    "risk_score",
    "heritage_sites",
]

# Keep only columns that exist
final_columns = [c for c in final_columns if c in merged.columns]

merged_final = merged[final_columns].copy()

# Save to CSV
output_file = OUTPUT_DIR / "tourism_comprehensive_1995_2024.csv"
merged_final.to_csv(output_file, index=False)

print(f"\n  ✓ Saved: {output_file}")
print(f"  File size: {output_file.stat().st_size / 1e6:.2f} MB")

# ============================================================================
# 9. SUMMARY STATISTICS
# ============================================================================

print("\n" + "=" * 80)
print("MERGED DATASET SUMMARY")
print("=" * 80)

print(
    f"\nDimensions: {merged_final.shape[0]:,} records × {merged_final.shape[1]} columns"
)
print(
    f"Time period: {merged_final['year'].min():.0f} - {merged_final['year'].max():.0f}"
)
print(f"Countries: {merged_final['country_name'].nunique()}")

print(f"\nKey variables:")
print(f"  Tourist arrivals: {merged_final['tourist_arrivals'].sum() / 1e9:.2f}B total")
print(
    f"  TTDI score: {merged_final['ttdi_score'].mean():.2f} avg (range: {merged_final['ttdi_score'].min():.2f}-{merged_final['ttdi_score'].max():.2f})"
)
print(f"  Risk score: {merged_final['risk_score'].mean():.3f} avg")
print(f"  Air quality: {merged_final['air_quality_index'].mean():.3f} avg")

print(f"\nSample records:")
print(merged_final.head(10).to_string(index=False))

print("\n" + "=" * 80)
print("MERGING COMPLETE")
print("=" * 80)
