"""
Additional Data Sources for Global Tourism Simulation

This module fetches data from alternative sources to fill gaps in World Bank data.
"""

import pandas as pd
import requests
from pathlib import Path

DATA_ROOT = Path(__file__).parent / "data"


def fetch_wef_travel_tourism_index():
    """
    Fetch World Economic Forum Travel & Tourism Development Index data.

    The WEF publishes this data in their annual report. No API available.
    Data must be manually downloaded from the WEF report.
    """
    print("WEF TTDI Data: Manual download required")
    print(
        "   Source: https://www3.weforum.org/docs/WEF_Travel_and_Tourism_Development_Index_2024.pdf"
    )
    print(
        "   Alternative: https://www.weforum.org/reports/the-travel-and-tourism-development-index-2024/"
    )

    # Create download guide instead of synthetic data
    folder = DATA_ROOT / "WEF"
    folder.mkdir(parents=True, exist_ok=True)

    readme = folder / "README.md"
    readme.write_text("""# WEF Travel & Tourism Development Index (TTDI)

## Source
https://www.weforum.org/reports/the-travel-and-tourism-development-index-2024/

## Download Instructions
1. Visit the WEF report page
2. Download the full dataset (Excel/CSV if available)
3. Or extract data from the PDF report appendix

## Key Indicators
- TTDI Score (overall)
- Enabling Environment
- Travel & Tourism Policy
- Infrastructure
- Natural & Cultural Resources
- Human Capital & Workforce

## Coverage
- ~140 countries
- Data year: 2024 (latest)

## Manual Entry Required
No API available. Data must be manually extracted or downloaded from WEF.
""")

    print(f"   Created download guide: {readme}")
    return None


def fetch_oecd_tourism_data():
    """
    Fetch tourism data from OECD Statistics.

    OECD provides detailed tourism statistics for member countries.
    API: https://stats.oecd.org/
    """
    print("Fetching OECD tourism statistics...")

    # OECD doesn't have a simple REST API, using manual download approach
    # For now, documenting the source
    print("   OECD data requires manual download from https://stats.oecd.org/")
    print("   Dataset: Tourism Statistics (TS)")

    # Create placeholder
    folder = DATA_ROOT / "OECD"
    folder.mkdir(parents=True, exist_ok=True)

    readme = folder / "README.md"
    readme.write_text("""# OECD Tourism Statistics

## Source
https://stats.oecd.org/

## Dataset
Tourism Statistics (TS)

## Download Instructions
1. Visit https://stats.oecd.org/
2. Search for "Tourism Statistics"
3. Select indicators:
   - International visitor arrivals
   - Tourism expenditure
   - Employment in tourism industries
4. Export to CSV

## Expected Variables
- ARRIVALS: International tourist arrivals
- EXPENDITURE: Tourism expenditure (USD)
- EMPLOYMENT: Employment in tourism (thousands)
- GDP_DIRECT: Direct tourism GDP contribution

## Coverage
- 38 OECD member countries
- Time series: 2010-2023 (annual)
""")

    print(f"   Created download guide: {readme}")
    return None


def create_synthetic_recent_data():
    """
    DEPRECATED: Synthetic data generation removed.

    Per project requirements, do NOT use synthetic data for 2020-2024.
    Analysis will use only actual observed data (2010-2019).
    """
    print("Synthetic data generation disabled per project requirements.")
    print("Analysis will use 2010-2019 data only.")
    return None


def merge_all_sources():
    """
    Merge all available data sources into a comprehensive dataset.
    Uses only observed data (no synthetic data for 2020-2024).
    """
    print("\nMerging all data sources...")

    datasets = []

    # World Bank data - filter to 2010-2019 only
    wb_file = DATA_ROOT / "World_Bank" / "tourism_indicators.csv"
    if wb_file.exists():
        df_wb = pd.read_csv(wb_file)
        # Filter out 2020-2024 (pandemic period with missing/incomplete data)
        df_wb = df_wb[(df_wb["year"] >= 2010) & (df_wb["year"] <= 2019)]
        datasets.append(df_wb)
        print(f"   Loaded World Bank (2010-2019): {len(df_wb)} records")

    if datasets:
        merged = pd.concat(datasets, ignore_index=True)
        merged = merged.sort_values(["country_code", "year"]).reset_index(drop=True)

        # Save merged dataset
        folder = DATA_ROOT / "merged"
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / "tourism_observed_2010_2019.csv"
        merged.to_csv(filepath, index=False)

        print(f"   Merged dataset: {len(merged)} records")
        print(f"   Saved to: {filepath}")

        return merged

    return None


if __name__ == "__main__":
    print("=" * 60)
    print("ADDITIONAL DATA SOURCES")
    print("=" * 60)

    # WEF data
    print("\n1. WEF Travel & Tourism Development Index")
    print("   STATUS: Manual download required (no API)")
    fetch_wef_travel_tourism_index()

    # OECD data
    print("\n2. OECD Tourism Statistics")
    print("   STATUS: Manual download required (no API)")
    fetch_oecd_tourism_data()

    # Merge all
    print("\n3. Merging Sources")
    df_merged = merge_all_sources()

    if df_merged is not None:
        print(
            f"\nFinal dataset: {len(df_merged)} records, {df_merged['year'].nunique()} years"
        )

    print("\n" + "=" * 60)
    print("NOTE: All data must be actively available online.")
    print("No synthetic or generated data is used.")
    print("=" * 60)
