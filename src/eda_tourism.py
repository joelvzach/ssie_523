"""
Exploratory Data Analysis for Global Tourism Data

This notebook performs initial EDA on collected tourism data to identify:
- Global trends in tourist arrivals/departures
- Regional patterns
- Seasonal variations
- Correlations with economic indicators
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup paths
DATA_ROOT = Path(__file__).parent / "data" / "merged"
OUTPUT_DIR = Path(__file__).parent / "analysis" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load data (observed data only, 2010-2019)
print("Loading tourism data (2010-2019, pre-pandemic)...")
df = pd.read_csv(DATA_ROOT / "tourism_observed_2010_2019.csv")

# Convert year to integer
df["year"] = df["year"].astype(int)

print(f"Dataset shape: {df.shape}")
print(f"Year range: {df['year'].min()} - {df['year'].max()}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst few rows:")
print(df.head())

# Basic statistics
print("\n=== Basic Statistics ===")
print(df.describe())

# Check for missing values
print("\n=== Missing Values ===")
print(df.isnull().sum())

# Global trends over time
print("\n=== Global Trends ===")
global_trends = df.groupby("year")[["tourist_arrivals", "tourist_departures"]].sum()
print(global_trends)

# Create visualizations
print("\n=== Generating Visualizations ===")

# Set style
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Global arrivals over time
ax1 = axes[0, 0]
ax1.plot(
    global_trends.index,
    global_trends["tourist_arrivals"] / 1e9,
    marker="o",
    linewidth=2,
)
ax1.set_xlabel("Year")
ax1.set_ylabel("Billions of Tourists")
ax1.set_title("Global Tourist Arrivals (2010-2024)")
ax1.grid(True, alpha=0.3)

# Plot 2: Arrivals vs Departures comparison
ax2 = axes[0, 1]
ax2.plot(
    global_trends.index,
    global_trends["tourist_arrivals"] / 1e9,
    label="Arrivals",
    marker="o",
)
ax2.plot(
    global_trends.index,
    global_trends["tourist_departures"] / 1e9,
    label="Departures",
    marker="s",
)
ax2.set_xlabel("Year")
ax2.set_ylabel("Billions")
ax2.set_title("Arrivals vs Departures")
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Growth rate year-over-year
ax3 = axes[1, 0]
growth_rate = global_trends["tourist_arrivals"].pct_change() * 100
ax3.bar(growth_rate.index, growth_rate.values, color="steelblue", alpha=0.7)
ax3.set_xlabel("Year")
ax3.set_ylabel("Growth Rate (%)")
ax3.set_title("Year-over-Year Growth in Tourist Arrivals")
ax3.axhline(y=0, color="red", linestyle="--", alpha=0.5)
ax3.grid(True, alpha=0.3)

# Plot 4: Latest year comparison by country
ax4 = axes[1, 1]
latest_year = df["year"].max()
latest_data = df[
    (df["year"] == latest_year) & (df["tourist_arrivals"] > 0)
].sort_values("tourist_arrivals", ascending=True)
if len(latest_data) > 0:
    latest_data = latest_data.dropna(subset=["country_code"])
    ax4.barh(
        latest_data["country_code"].astype(str),
        latest_data["tourist_arrivals"] / 1e6,
        color="coral",
    )
    ax4.set_xlabel("Millions of Tourists")
    ax4.set_title(f"Tourist Arrivals by Country ({latest_year})")
    ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "tourism_overview.png", dpi=300, bbox_inches="tight")
print(f"Saved overview plot to: {OUTPUT_DIR / 'tourism_overview.png'}")
plt.close()

# Additional analysis: CAGR (Compound Annual Growth Rate)
print("\n=== Growth Analysis ===")
start_year = df["year"].min()
end_year = df["year"].max()

start_arrivals = global_trends.loc[start_year, "tourist_arrivals"]
end_arrivals = global_trends.loc[end_year, "tourist_arrivals"]

n_years = end_year - start_year
cagr = (end_arrivals / start_arrivals) ** (1 / n_years) - 1

print(f"CAGR ({start_year}-{end_year}): {cagr * 100:.2f}%")

# Save summary statistics
latest_year = global_trends.index.max()
summary = {
    "metric": [
        f"Total Arrivals ({latest_year})",
        f"Total Departures ({latest_year})",
        "CAGR Arrivals",
        "Peak Year",
        "Lowest Year",
    ],
    "value": [
        f"{global_trends.loc[latest_year, 'tourist_arrivals'] / 1e9:.2f}B",
        f"{global_trends.loc[latest_year, 'tourist_departures'] / 1e9:.2f}B",
        f"{cagr * 100:.2f}%",
        str(global_trends["tourist_arrivals"].idxmax()),
        str(global_trends["tourist_arrivals"].idxmin()),
    ],
}
summary_df = pd.DataFrame(summary)
summary_df.to_csv(OUTPUT_DIR / "summary_statistics.csv", index=False)
print(f"Saved summary statistics to: {OUTPUT_DIR / 'summary_statistics.csv'}")

print("\n=== EDA Complete ===")
print(f"Output files saved to: {OUTPUT_DIR}")
