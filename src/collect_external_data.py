"""
External Data Collection Script

Collects data from:
1. OpenSky Network - Flight connectivity data
2. ACLED - Conflict/risk data
3. InsideAirbnb - Accommodation data
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# Paths
DATA_ROOT = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_ROOT / "external"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCES_LOG = DATA_ROOT / "SOURCES_LOG.md"


# ============================================================================
# 1. OPENSKY NETWORK - Flight Connectivity Data
# ============================================================================


def fetch_opensky_airport_traffic():
    """
    Fetch airport traffic data from OpenSky Network.

    Note: OpenSky requires free registration for API access.
    This script attempts to use their public API endpoints.

    API Docs: https://opensky-network.org/apidoc/
    """
    print("\n" + "=" * 60)
    print("1. OPENSKY NETWORK - Flight Data")
    print("=" * 60)

    # OpenSky API base URL (public endpoints, no auth required for limited access)
    base_url = "https://opensky-network.org/api"

    # Try to get airport statistics for major tourism hubs
    major_airports = [
        ("KJFK", "New York JFK", "USA"),
        ("KLAX", "Los Angeles LAX", "USA"),
        ("EGLL", "London Heathrow", "UK"),
        ("LFPG", "Paris CDG", "France"),
        ("EDDF", "Frankfurt", "Germany"),
        ("RJTT", "Tokyo Haneda", "Japan"),
        ("ZBAA", "Beijing Capital", "China"),
        ("WSSS", "Singapore Changi", "Singapore"),
        ("OMDB", "Dubai", "UAE"),
        ("VHHH", "Hong Kong", "Hong Kong"),
    ]

    airport_data = []

    print("\nAttempting to fetch airport traffic data...")
    print("Note: OpenSky API may require registration for full access")

    for airport_code, airport_name, country in major_airports:
        try:
            # Try public flight info endpoint
            url = f"{base_url}/flights/arrival?airport={airport_code}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                flights = response.json()
                airport_data.append(
                    {
                        "airport_code": airport_code,
                        "airport_name": airport_name,
                        "country": country,
                        "flights_sample": len(flights)
                        if isinstance(flights, list)
                        else 0,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                print(
                    f"  ✓ {airport_name}: {len(flights) if isinstance(flights, list) else 'N/A'} flights"
                )
            elif response.status_code == 401:
                print(f"  ⚠ {airport_name}: API requires authentication")
                break
            elif response.status_code == 403:
                print(
                    f"  ⚠ {airport_name}: Access forbidden (rate limit or auth required)"
                )
                break
            else:
                print(f"  ✗ {airport_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"  ✗ {airport_name}: {str(e)}")

    # If API access works, save data
    if airport_data:
        df = pd.DataFrame(airport_data)
        filepath = OUTPUT_DIR / "opensky_airport_traffic.csv"
        df.to_csv(filepath, index=False)
        print(f"\n  ✓ Saved {len(df)} airports to: {filepath}")
        return df
    else:
        print("\n  ⚠ No data retrieved - API may require registration")
        print("  Action required: Register at https://opensky-network.org/register")

        # Create placeholder with download instructions
        readme = OUTPUT_DIR / "OPENVSKY_README.md"
        readme.write_text("""# OpenSky Network Data

## Status
API requires free registration for full access.

## Next Steps
1. Register at: https://opensky-network.org/register
2. Request API credentials (username/password)
3. Update `src/collect_external_data.py` with credentials
4. Re-run data collection

## Available Endpoints (with auth)
- `/flights/arrival?airport={airport}` - Arrival flights
- `/flights/departure?airport={airport}` - Departure flights
- `/aircraft-states` - Real-time aircraft positions
- `/flights/all?begin_time={ts}&end_time={ts}` - Historical flights

## Data to Collect
- Airport traffic counts (monthly aggregations)
- Route networks (origin-destination pairs)
- Flight frequency by route

## Alternative
Download aggregated statistics from:
https://opensky-network.org/data/statistics
""")
        print(f"  ✓ Created download guide: {readme}")
        return None


# ============================================================================
# 2. ACLED - Conflict Data (Risk Factor)
# ============================================================================


def fetch_acled_conflict_data():
    """
    Fetch conflict event data from ACLED (Armed Conflict Location & Event Data).

    ACLED provides free data for academic/research use.
    Requires registration but offers public data exports.

    API Docs: https://www.acleddata.com/api/
    """
    print("\n" + "=" * 60)
    print("2. ACLED - Conflict/Risk Data")
    print("=" * 60)

    # ACLED API requires registration and API key
    # Public data exports available without API key
    base_url = "https://api.acleddata.com"

    print("\nAttempting to fetch conflict data...")
    print("Note: ACLED requires free registration for API access")

    # Try public data export endpoint
    try:
        # ACLED offers public data downloads
        # This is a sample endpoint - full access requires registration
        url = "https://www.acleddata.com/data-export/"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print("  ✓ ACLED data export page accessible")
            print("  ⚠ Full dataset requires registration")
        else:
            print(f"  ⚠ HTTP {response.status_code}")

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

    # Create download guide
    print("\n  Creating download instructions...")

    readme = OUTPUT_DIR / "ACLED_README.md"
    readme.write_text(f"""# ACLED Conflict Data

## Status
API requires free registration for research use.

## Data Description
ACLED (Armed Conflict Location & Event Data Project) provides:
- Conflict events by country
- Protest data
- Violence indicators
- Monthly updates from 1997-present

## Relevance for Tourism Simulation
- **Risk factor calibration**: Conflict intensity by country
- **Temporal dynamics**: Monthly risk scores
- **Geographic granularity**: Sub-national conflict locations

## Download Instructions

### Option 1: Web Export (No API)
1. Visit: https://www.acleddata.com/data-export/
2. Select parameters:
   - Regions: All (or select specific)
   - Date range: 2010-2024
   - Event types: All
   - Format: CSV
3. Submit request (data sent via email)

### Option 2: API Access (Recommended)
1. Register at: https://www.acleddata.com/registration/
2. Request API key (free for academic use)
3. Use API endpoint:
   ```
   GET https://api.acleddata.com/api.php?api_key=YOUR_KEY&event_type=All&country=All
   ```

### Option 3: Direct Download (Limited)
Some pre-packaged datasets available at:
https://github.com/ACLED

## Data Processing (After Download)
See download instructions at ACLED website for data format.

## Expected Output
File: `data/external/acled_conflict_data.csv`
Columns:
- country_code
- year
- conflict_events (count)
- fatalities (total)
- risk_index (0-1, normalized)

## Last Updated
{datetime.now().strftime("%Y-%m-%d")}
""")

    print(f"  ✓ Created download guide: {readme}")
    return None


# ============================================================================
# 3. INSIDEAIRBNB - Accommodation Data
# ============================================================================


def fetch_insideairbnb_data():
    """
    Fetch accommodation data from InsideAirbnb.

    InsideAirbnb provides free, open data for 100+ cities worldwide.
    Data includes listings, prices, reviews, and availability.

    Data: http://insideairbnb.com/get-the-data/
    """
    print("\n" + "=" * 60)
    print("3. INSIDEAIRBNB - Accommodation Data")
    print("=" * 60)

    # InsideAirbnb data URLs (public, no auth required)
    base_url = "http://data.insideairbnb.com"

    # Major tourism cities with available data
    tourism_cities = [
        ("paris", "France", "Europe"),
        ("london", "UK", "Europe"),
        ("new-york", "USA", "Americas"),
        ("barcelona", "Spain", "Europe"),
        ("rome", "Italy", "Europe"),
        ("tokyo", "Japan", "Asia-Pacific"),
        ("singapore", "Singapore", "Asia-Pacific"),
        ("amsterdam", "Netherlands", "Europe"),
        ("lisbon", "Portugal", "Europe"),
        ("bangkok", "Thailand", "Asia-Pacific"),
    ]

    city_data = []

    print("\nAttempting to fetch Airbnb listing summaries...")

    for city, country, region in tourism_cities:
        try:
            # Listings summary endpoint
            listings_url = f"{base_url}/{country.lower().replace(' ', '-')}/{city}/data/listings_summary.csv"

            # Try to fetch
            response = requests.head(listings_url, timeout=5)

            if response.status_code == 200:
                print(f"  ✓ {city}: Data available")
                city_data.append(
                    {
                        "city": city,
                        "country": country,
                        "region": region,
                        "data_url": listings_url,
                        "status": "available",
                    }
                )
            else:
                # Try alternative URL format
                alt_url = f"{base_url}/{city}/data/listings_summary.csv"
                response = requests.head(alt_url, timeout=5)
                if response.status_code == 200:
                    print(f"  ✓ {city}: Data available (alt URL)")
                    city_data.append(
                        {
                            "city": city,
                            "country": country,
                            "region": region,
                            "data_url": alt_url,
                            "status": "available",
                        }
                    )
                else:
                    print(f"  ⚠ {city}: Not found or different format")

        except Exception as e:
            print(f"  ✗ {city}: {str(e)}")

    # Save available city list
    if city_data:
        df = pd.DataFrame(city_data)
        filepath = OUTPUT_DIR / "insideairbnb_available_cities.csv"
        df.to_csv(filepath, index=False)
        print(f"\n  ✓ Saved {len(df)} cities to: {filepath}")

        # Create download script
        create_airbnb_download_script()

        return df
    else:
        print("\n  ⚠ No cities found - URL structure may vary")
        return None


def create_airbnb_download_script():
    """Create a script to download full Airbnb datasets."""

    script_path = OUTPUT_DIR / "download_airbnb_data.py"
    script_path.write_text('''"""
Download InsideAirbnb Data

This script downloads full datasets for available cities.
Run after reviewing insideairbnb_available_cities.csv
"""

import pandas as pd
import requests
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
AIRBNB_DIR = OUTPUT_DIR.parent / "insideairbnb"
AIRBNB_DIR.mkdir(parents=True, exist_ok=True)

# Read available cities
cities_df = pd.read_csv(OUTPUT_DIR / "insideairbnb_available_cities.csv")

print("Downloading InsideAirbnb datasets...")

for idx, row in cities_df.iterrows():
    if row['status'] == 'available':
        city = row['city']
        country = row['country']
        url = row['data_url']
        
        print(f"\\nDownloading {city}, {country}...")
        
        try:
            # Download listings summary
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Save to file
                filepath = AIRBNB_DIR / f"{city}_listings.csv"
                filepath.write_bytes(response.content)
                print(f"  ✓ Saved: {filepath.name}")
            else:
                print(f"  ✗ HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

print("\\nDownload complete!")
''')

    print(f"  ✓ Created download script: {script_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EXTERNAL DATA COLLECTION")
    print("Sources: OpenSky Network, ACLED, InsideAirbnb")
    print("=" * 80)

    # 1. OpenSky Network
    print("\n[1/3] OpenSky Network")
    opensky_data = fetch_opensky_airport_traffic()

    # 2. ACLED
    print("\n[2/3] ACLED Conflict Data")
    acled_data = fetch_acled_conflict_data()

    # 3. InsideAirbnb
    print("\n[3/3] InsideAirbnb")
    airbnb_data = fetch_insideairbnb_data()

    # Summary
    print("\n" + "=" * 80)
    print("COLLECTION SUMMARY")
    print("=" * 80)

    print("\nOpenSky Network:")
    if opensky_data is not None:
        print(f"  ✓ Data collected: {len(opensky_data)} airports")
    else:
        print(f"  ⚠ Registration required - see {OUTPUT_DIR}/OPENVSKY_README.md")

    print("\nACLED:")
    if acled_data is not None:
        print(f"  ✓ Data collected: {len(acled_data)} records")
    else:
        print(f"  ⚠ Registration required - see {OUTPUT_DIR}/ACLED_README.md")

    print("\nInsideAirbnb:")
    if airbnb_data is not None:
        print(f"  ✓ Cities identified: {len(airbnb_data)}")
        print(f"  ✓ Download script created: {OUTPUT_DIR}/download_airbnb_data.py")
    else:
        print(f"  ⚠ Manual download required")

    print("\n" + "=" * 80)
    print("Output directory:", OUTPUT_DIR)
    print("=" * 80)
