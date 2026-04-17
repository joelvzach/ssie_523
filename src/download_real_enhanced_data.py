"""
Real Enhanced Data Collection

Downloads REAL data from public sources:
1. UNESCO World Heritage Sites (open API)
2. Global Peace Index (manual download guide)
3. WHO Air Quality (Our World in Data)
4. Numbeo Cost of Living (Kaggle)
5. WorldClim Climate (manual download guide)
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# Paths
DATA_ROOT = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_ROOT / "enhanced_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 1. UNESCO World Heritage Sites - REAL DATA
# ============================================================================


def fetch_unesco_real():
    """
    Download UNESCO World Heritage Sites from Wikipedia/DBpedia.
    This uses SPARQL to query structured Wikipedia data.
    """
    print("\n" + "=" * 60)
    print("1. UNESCO World Heritage Sites - REAL DATA")
    print("=" * 60)

    # Use Wikipedia API to get list of World Heritage Sites by country
    print("\nFetching from Wikipedia/DBpedia...")

    # Better approach: Use Wikidata SPARQL
    wikidata_query = """
    SELECT ?country ?countryLabel (COUNT(?site) as ?count) 
    WHERE {
      ?site wdt:P31/wdt:P279* wd:Q9259 .  # World Heritage Site
      ?site wdt:P17 ?country .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    GROUP BY ?country ?countryLabel
    ORDER BY DESC(?count)
    LIMIT 200
    """

    try:
        endpoint = "https://query.wikidata.org/sparql"
        response = requests.get(
            endpoint,
            params={"query": wikidata_query, "format": "json"},
            headers={"User-Agent": "TourismResearch/1.0"},
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            results = data["results"]["bindings"]

            unesco_data = []
            for result in results:
                country = result.get("countryLabel", {}).get("value", "Unknown")
                count = int(result["count"]["value"])
                if country != "Unknown" and count > 0:
                    unesco_data.append({"country": country, "total_sites": count})

            df = pd.DataFrame(unesco_data)

            if len(df) > 0:
                # Save to file
                filepath = OUTPUT_DIR / "unesco_world_heritage_sites.csv"
                df.to_csv(filepath, index=False)
                print(f"✓ Saved {len(df)} countries to: {filepath.name}")
                print(f"\nTop 15 countries:")
                print(df.head(15).to_string())
                return df
            else:
                print("✗ No data retrieved")
                return None
        else:
            print(f"✗ HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


# ============================================================================
# 2. Global Peace Index - Download from visionofhumanity.org
# ============================================================================


def fetch_gpi_real():
    """
    Download Global Peace Index data.

    GPI data must be downloaded from their website.
    This creates a download script and attempts to fetch from alternative sources.
    """
    print("\n" + "=" * 60)
    print("2. Global Peace Index - REAL DATA")
    print("=" * 60)

    # Try to get data from Our World in Data (they have GPI data)
    print("\nAttempting to fetch from Our World in Data...")

    try:
        # Our World in Data has GPI data
        url = "https://ourworldindata.org/grapher/global-peace-index-by-country"

        # Direct CSV download link (OWID)
        csv_url = "https://ourworldindata.org/grapher/global-peace-index-by-country.csv"

        response = requests.get(csv_url, timeout=30)

        if response.status_code == 200:
            # Parse CSV
            from io import StringIO

            df = pd.read_csv(StringIO(response.text))

            # Save raw
            filepath = OUTPUT_DIR / "global_peace_index_raw.csv"
            df.to_csv(filepath, index=False)
            print(f"✓ Saved {len(df)} records to: {filepath.name}")

            # Process to get latest year by country
            if "Year" in df.columns and "Value" in df.columns:
                latest = df.loc[df.groupby("Entity")["Year"].idxmax()]
                latest_df = latest[["Entity", "Year", "Value"]].copy()
                latest_df.columns = ["country", "year", "gpi_score"]

                filepath_clean = OUTPUT_DIR / "global_peace_index.csv"
                latest_df.to_csv(filepath_clean, index=False)
                print(f"✓ Saved cleaned data: {len(latest_df)} countries")
                print(f"\nSample:")
                print(latest_df.head(10).to_string())

                return latest_df

            return df
        else:
            print(f"✗ HTTP {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Create download guide
    print("\nCreating manual download guide...")
    readme = OUTPUT_DIR / "GPI_DOWNLOAD_INSTRUCTIONS.md"
    readme.write_text(f"""# Global Peace Index - Download Instructions

## Source 1: Vision of Humanity (Official)
1. Visit: https://www.visionofhumanity.org/resources/
2. Download "Global Peace Index 2024" report
3. Data tables are in the appendix

## Source 2: Our World in Data (Recommended)
1. Visit: https://ourworldindata.org/grapher/global-peace-index-by-country
2. Click "Download" → "CSV"
3. Save to: `data/enhanced_data/global_peace_index.csv`

## Source 3: World Bank WGI (Alternative)
1. Visit: https://data.worldbank.org/indicator/IQ.CPA.PUBS.XQ
2. Download "Worldwide Governance Indicators"
3. Use "Political Stability and Absence of Violence"

## Expected Columns
- country: Country name
- year: Year
- gpi_score: GPI score (1=most peaceful, 5=least peaceful)

## Last Updated
{datetime.now().strftime("%Y-%m-%d")}
""")
    print(f"✓ Created download guide: {readme.name}")

    return None


# ============================================================================
# 3. WHO Air Quality - Download from Our World in Data
# ============================================================================


def fetch_air_quality_real():
    """
    Download air quality data from Our World in Data.
    This is REAL data from WHO sources.
    """
    print("\n" + "=" * 60)
    print("3. WHO Air Quality - REAL DATA")
    print("=" * 60)

    print("\nFetching from Our World in Data...")

    try:
        # PM2.5 air pollution data
        csv_url = "https://ourworldindata.org/grapher/annual-pm25-concentrations.csv"

        response = requests.get(csv_url, timeout=30)

        if response.status_code == 200:
            from io import StringIO

            df = pd.read_csv(StringIO(response.text))

            # Save raw
            filepath = OUTPUT_DIR / "who_air_quality_pm25.csv"
            df.to_csv(filepath, index=False)
            print(f"✓ Saved {len(df)} records to: {filepath.name}")

            # Get latest year by country
            if "Year" in df.columns and "Annual PM2.5" in df.columns:
                latest = df.loc[df.groupby("Entity")["Year"].idxmax()]
                latest_df = latest[["Entity", "Year", "Annual PM2.5"]].copy()
                latest_df.columns = ["country", "year", "pm25_concentration"]

                # Calculate air quality index (inverse of PM2.5)
                max_pm25 = latest_df["pm25_concentration"].max()
                latest_df["air_quality_index"] = 1 - (
                    latest_df["pm25_concentration"] / max_pm25
                )

                filepath_clean = OUTPUT_DIR / "who_air_quality.csv"
                latest_df.to_csv(filepath_clean, index=False)
                print(f"✓ Saved cleaned data: {len(latest_df)} countries")
                print(f"\nTop 10 best air quality:")
                best = latest_df.nlargest(10, "air_quality_index")
                print(
                    best[
                        ["country", "pm25_concentration", "air_quality_index"]
                    ].to_string()
                )

                return latest_df

            return df
        else:
            print(f"✗ HTTP {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")

    return None


# ============================================================================
# 4. Cost of Living - Download from Kaggle
# ============================================================================


def fetch_cost_of_living_real():
    """
    Download cost of living data from Kaggle.
    Numbeo datasets are available on Kaggle.
    """
    print("\n" + "=" * 60)
    print("4. Cost of Living - REAL DATA")
    print("=" * 60)

    print("\nCreating download guide...")

    readme = OUTPUT_DIR / "COST_OF_LIVING_DOWNLOAD.md"
    readme.write_text(f"""# Cost of Living Data - Download Instructions

## Source 1: Kaggle - Numbeo Cost of Living (Recommended)
1. Visit: https://www.kaggle.com/datasets/prasertk/numbeo-cost-of-living-2024
   OR: https://www.kaggle.com/datasets/ahmedshahriar/numbeo-cost-of-living-index
2. Download CSV file
3. Save to: `data/enhanced_data/numbeo_cost_of_living.csv`

## Source 2: Numbeo Direct
1. Visit: https://www.numbeo.com/cost-of-living/rankings_by_country.jsp
2. Scrape or manually copy data
3. Columns needed:
   - Country
   - Consumer Price Index
   - Rent Index
   - Consumer Price Plus Rent Index
   - Restaurant Price Index
   - Groceries Index

## Source 3: World Bank PPP (Alternative)
1. Visit: https://data.worldbank.org/indicator/PA.NUS.PPPC.RF
2. Download "Price level ratio of PPP conversion factor"
3. Save to: `data/enhanced_data/world_bank_ppp.csv`

## Expected Columns
- country: Country name
- consumer_price_index: Overall cost index
- rent_index: Accommodation costs
- restaurant_price_index: Dining costs
- groceries_index: Food prices

## Last Updated
{datetime.now().strftime("%Y-%m-%d")}
""")
    print(f"✓ Created download guide: {readme.name}")

    # Try alternative: World Bank PPP data (open API)
    print("\nAttempting World Bank PPP data...")

    try:
        url = "https://api.worldbank.org/v2/country/all/indicator/PA.NUS.PPPC.RF?format=json&per_page=300&date=2020:2024"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if len(data) >= 2:
                df = pd.DataFrame(data[1])
                df = df[["countryiso3code", "date", "value"]].dropna()
                df.columns = ["country_code", "year", "ppp_price_level"]
                df["year"] = df["year"].astype(int)

                # Get latest
                latest = df.loc[df.groupby("country_code")["year"].idxmax()]

                filepath = OUTPUT_DIR / "world_bank_ppp.csv"
                latest.to_csv(filepath, index=False)
                print(f"✓ Saved World Bank PPP: {len(latest)} countries")

                return latest
    except Exception as e:
        print(f"✗ World Bank PPP error: {e}")

    return None


# ============================================================================
# 5. Climate Data - Download from climate-data.org
# ============================================================================


def fetch_climate_real():
    """
    Download climate data.
    WorldClim requires manual download, but we can use climate-data.org API.
    """
    print("\n" + "=" * 60)
    print("5. Climate Data - REAL DATA")
    print("=" * 60)

    readme = OUTPUT_DIR / "CLIMATE_DATA_DOWNLOAD.md"
    readme.write_text(f"""# Climate Data - Download Instructions

## Source 1: Climate-Data.org (Easiest)
1. Visit: https://en.climate-data.org/
2. Search by country (e.g., "France")
3. Download climate data as CSV
4. Repeat for major tourism destinations

## Source 2: WorldClim (Research Grade)
1. Visit: https://www.worldclim.org/data/worldclim21.html
2. Download bioclimatic variables
3. Requires GIS software to process

## Source 3: NOAA Climate Data (US-focused)
1. Visit: https://www.ncdc.noaa.gov/cdo-web/
2. Download Global Summary of the Month (GSOM)
3. Global coverage

## Source 4: Our World in Data (Aggregated)
1. Visit: https://ourworldindata.org/grapher/average-deadly-heat-events
2. Download temperature/precipitation data
3. Save to: `data/enhanced_data/climate_data.csv`

## Expected Columns
- country: Country name
- temp_annual_avg: Annual average temperature (°C)
- temp_summer_avg: Summer average (°C)
- temp_winter_avg: Winter average (°C)
- precipitation_annual: Annual precipitation (mm)
- sunshine_hours: Annual sunshine hours

## Last Updated
{datetime.now().strftime("%Y-%m-%d")}
""")
    print(f"✓ Created download guide: {readme.name}")

    # Try Our World in Data for temperature
    print("\nAttempting temperature data from Our World in Data...")

    try:
        csv_url = (
            "https://ourworldindata.org/grapher/annual-average-surface-temperature.csv"
        )
        response = requests.get(csv_url, timeout=30)

        if response.status_code == 200:
            from io import StringIO

            df = pd.read_csv(StringIO(response.text))

            filepath = OUTPUT_DIR / "temperature_data.csv"
            df.to_csv(filepath, index=False)
            print(f"✓ Saved {len(df)} temperature records")

            return df
    except Exception as e:
        print(f"✗ Error: {e}")

    return None


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("REAL ENHANCED DATA COLLECTION")
    print("Downloading from actual sources...")
    print("=" * 80)

    datasets = {}

    # 1. UNESCO
    print("\n[1/5] UNESCO World Heritage Sites")
    datasets["unesco"] = fetch_unesco_real()

    # 2. Global Peace Index
    print("\n[2/5] Global Peace Index")
    datasets["gpi"] = fetch_gpi_real()

    # 3. Air Quality
    print("\n[3/5] WHO Air Quality")
    datasets["aqi"] = fetch_air_quality_real()

    # 4. Cost of Living
    print("\n[4/5] Cost of Living")
    datasets["cost"] = fetch_cost_of_living_real()

    # 5. Climate
    print("\n[5/5] Climate Data")
    datasets["climate"] = fetch_climate_real()

    # Summary
    print("\n" + "=" * 80)
    print("COLLECTION SUMMARY")
    print("=" * 80)

    for name, df in datasets.items():
        if df is not None:
            print(f"✓ {name}: {len(df)} records")
        else:
            print(f"⚠ {name}: Requires manual download")

    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
1. Review *_DOWNLOAD.md files for manual download instructions
2. Download remaining datasets:
   - Global Peace Index (if not auto-downloaded)
   - Cost of Living from Kaggle
   - Climate data from climate-data.org
3. Place downloaded files in: {OUTPUT_DIR}
4. Run analysis script
""")
