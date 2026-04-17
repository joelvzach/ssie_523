"""
Data Collection Module for Global Tourism Simulation

This module fetches tourism data from various APIs and sources.
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# Base paths
DATA_ROOT = Path(__file__).parent / "data"
SOURCES_LOG = DATA_ROOT / "SOURCES_LOG.md"


def fetch_world_bank_tourism_data():
    """
    Fetch tourism-related data from World Bank API.

    Available indicators:
    - ST.INT.ARVL: International tourist arrivals
    - ST.INT.RCPT: International tourism receipts
    - ST.INT.DPRT: International tourist departures

    Returns:
        pd.DataFrame: Combined tourism data
    """
    base_url = "https://api.worldbank.org/v2/country/all/indicator"

    indicators = {
        "ST.INT.ARVL": "tourist_arrivals",
        "ST.INT.RCPT": "tourism_receipts",
        "ST.INT.DPRT": "tourist_departures",
    }

    all_data = []

    for indicator, name in indicators.items():
        url = f"{base_url}/{indicator}?format=json&per_page=300&date=2010:2023"
        try:
            response = requests.get(url, timeout=30)
            data = response.json()

            if len(data) >= 2:
                df = pd.DataFrame(data[1])
                df = df[["countryiso3code", "date", "value"]]
                df = df.rename(
                    columns={
                        "countryiso3code": "country_code",
                        "date": "year",
                        "value": name,
                    }
                )
                df = df[df["year"] != ""]
                df["year"] = df["year"].astype(int)
                all_data.append(df)
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    if all_data:
        merged = all_data[0]
        for df in all_data[1:]:
            merged = pd.merge(merged, df, on=["country_code", "year"], how="outer")
        return merged

    return None


def fetch_un_tourism_data():
    """
    Fetch data from UN Tourism (UNWTO) API.

    Note: UNWTO doesn't have a public API, so we'll use their open data portal
    or scrape from their statistics pages.

    For now, using the UNESCO/UNWTO open data endpoints where available.
    """
    print(
        "UN Tourism data: Manual download required from https://www.untourism.int/tourism-statistics/tourism-statistics-database"
    )
    print(
        "Alternative: Using World Bank as proxy for UNWTO data (World Bank sources from UNWTO)"
    )
    return None


def save_data(df, source_name, filename):
    """Save data to appropriate folder and log it."""
    folder = DATA_ROOT / source_name
    folder.mkdir(parents=True, exist_ok=True)

    filepath = folder / filename
    df.to_csv(filepath, index=False)

    # Log the download
    log_download(source_name, filename, filepath)

    return filepath


def log_download(source, filename, filepath):
    """Append download entry to SOURCES_LOG.md"""
    date = datetime.now().strftime("%Y-%m-%d")
    size = filepath.stat().st_size

    log_entry = (
        f"| {date} | {source} | {filename} | {filepath.name} | {size / 1024:.1f} KB |\n"
    )

    with open(SOURCES_LOG, "r") as f:
        content = f.read()

    if "|------|--------|---------|-----------|-------|" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "|------|--------|---------|-----------|-------|" in line:
                lines.insert(i + 1, log_entry.strip())
                break
        content = "\n".join(lines)
        with open(SOURCES_LOG, "w") as f:
            f.write(content)


if __name__ == "__main__":
    print("=" * 60)
    print("GLOBAL TOURISM DATA COLLECTION")
    print("=" * 60)

    # World Bank data
    print("\n1. Fetching World Bank tourism data...")
    df_wb = fetch_world_bank_tourism_data()

    if df_wb is not None:
        print(f"   Retrieved {len(df_wb)} records")
        print(f"   Countries: {df_wb['country_code'].dropna().nunique()}")
        print(f"   Year range: {df_wb['year'].min()} - {df_wb['year'].max()}")

        filepath = save_data(df_wb, "World_Bank", "tourism_indicators.csv")
        print(f"   Saved to: {filepath}")
    else:
        print("   Failed to fetch data")

    # UN Tourism
    print("\n2. UN Tourism data...")
    fetch_un_tourism_data()

    print("\n" + "=" * 60)
    print("Data collection complete!")
    print("=" * 60)
