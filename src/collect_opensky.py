"""
OpenSky Network Data Collection

Uses public API endpoints (no authentication required for limited access).
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

DATA_ROOT = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_ROOT / "external"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("OPENSKY NETWORK DATA COLLECTION")
print("=" * 60)

# OpenSky public API (no auth required for basic endpoints)
BASE_URL = "https://opensky-network.org/api"

# 1. Get real-time aircraft states (snapshot of current air traffic)
print("\n1. Fetching real-time aircraft states...")
try:
    response = requests.get(f"{BASE_URL}/states/all", timeout=30)
    if response.status_code == 200:
        data = response.json()
        print(f"   Timestamp: {datetime.fromtimestamp(data['time'])}")
        print(f"   Aircraft in air: {len(data['states'])}")

        # Parse aircraft data
        # State vector format: https://opensky-network.org/apidoc/rest.html#state-vectors
        states = data["states"]

        # Extract relevant fields
        aircraft_data = []
        for state in states[:1000]:  # Sample first 1000
            aircraft_data.append(
                {
                    "icao24": state[0],
                    "callsign": state[1].strip() if state[1] else None,
                    "origin_country": state[2],
                    "longitude": state[5],
                    "latitude": state[6],
                    "altitude": state[7],
                    "velocity": state[9],
                    "true_track": state[10],
                    "timestamp": data["time"],
                }
            )

        df_aircraft = pd.DataFrame(aircraft_data)

        # Save to file
        filepath = OUTPUT_DIR / "opensky_aircraft_snapshot.csv"
        df_aircraft.to_csv(filepath, index=False)
        print(f"   ✓ Saved {len(df_aircraft)} aircraft to: {filepath.name}")

        # Summary by country
        country_counts = df_aircraft["origin_country"].value_counts().head(20)
        print(f"\n   Top 20 countries by aircraft count:")
        for country, count in country_counts.items():
            print(f"      {country:30s}: {count}")

except Exception as e:
    print(f"   ✗ Error: {e}")

# 2. Get country metadata
print("\n2. Fetching country metadata...")
try:
    # Try to get country codes mapping
    response = requests.get(f"{BASE_URL}/metadata/countries", timeout=10)
    if response.status_code == 200:
        countries = response.json()
        df_countries = pd.DataFrame(countries)
        filepath = OUTPUT_DIR / "opensky_countries.csv"
        df_countries.to_csv(filepath, index=False)
        print(f"   ✓ Saved {len(df_countries)} countries")
    else:
        print(f"   ⚠ Country metadata not available (HTTP {response.status_code})")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 3. Create summary statistics
print("\n3. Creating summary statistics...")
if "df_aircraft" in locals():
    summary = {
        "metric": [
            "Total aircraft tracked",
            "Countries represented",
            "Top country",
            "Top country count",
            "Average altitude (m)",
            "Average velocity (m/s)",
        ],
        "value": [
            len(df_aircraft),
            df_aircraft["origin_country"].nunique(),
            country_counts.index[0] if len(country_counts) > 0 else "N/A",
            country_counts.iloc[0] if len(country_counts) > 0 else 0,
            f"{df_aircraft['altitude'].mean():.0f}",
            f"{df_aircraft['velocity'].mean():.0f}",
        ],
    }

    df_summary = pd.DataFrame(summary)
    filepath = OUTPUT_DIR / "opensky_summary.csv"
    df_summary.to_csv(filepath, index=False)
    print(f"   ✓ Saved summary to: {filepath.name}")

print("\n" + "=" * 60)
print("OPENVSKY DATA COLLECTION COMPLETE")
print("=" * 60)
print(f"\nOutput directory: {OUTPUT_DIR}")
print("\nNote: This is a snapshot of real-time data.")
print("For historical data, registration is required at:")
print("https://opensky-network.org/register")
