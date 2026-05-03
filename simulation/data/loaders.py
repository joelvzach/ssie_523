"""
Data loading utilities for simulation.
Loads country data from merged datasets.
"""

import csv
from typing import List, Dict
from pathlib import Path


def load_country_data(data_dir: Path = None) -> List[Dict]:
    """
    Load country data from merged datasets.

    Args:
        data_dir: Path to data directory (defaults to project data/merged)

    Returns:
        List of country dicts with required fields
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data" / "merged"

    countries = []

    # Load from comprehensive dataset
    data_file = data_dir / "tourism_comprehensive_1995_2024.csv"

    if not data_file.exists():
        print(f"Warning: Data file not found: {data_file}")
        return _create_placeholder_countries()

    # Read most recent year (2024) for each country
    country_data = {}

    with open(data_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("country_code", row.get("Code", ""))
            if not code:
                continue

            # Keep most recent year
            year = row.get("year", row.get("Year", "2024"))
            if code not in country_data or year > country_data[code]["year"]:
                # Helper to safely convert to float
                def safe_float(val, default=0.0):
                    if val is None or val == "":
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default

                def safe_int(val, default=None):
                    if val is None or val == "":
                        return default
                    try:
                        return int(float(val))
                    except (ValueError, TypeError):
                        return default

                country_data[code] = {
                    "year": year,
                    "code": code,
                    "name": row.get("country_name", row.get("Country", "")),
                    "arrivals": safe_float(row.get("inbound_arrivals", 0)),
                    "hotel_beds": None,  # Will estimate from arrivals
                    "ttdi": safe_float(row.get("ttdi_score", 3.5)),
                    "cost_index": safe_float(row.get("cost_index", 50.0)),
                    "risk_score": safe_float(row.get("risk_score", 0.2)),
                    "lat": safe_float(row.get("latitude", 0.0)),
                    "lon": safe_float(row.get("longitude", 0.0)),
                }

    # Convert to list with estimated hotel beds from arrivals
    for code, data in country_data.items():
        # Estimate hotel beds from annual arrivals
        # Assumption: 30% of annual arrivals stay in hotels
        # Average stay: 7 days, occupancy rate: 60%
        # hotel_beds = (arrivals * 0.30 * 7) / (365 * 0.60)
        # NOTE: arrivals in dataset are in THOUSANDS, convert to actual count
        arrivals = data.get("arrivals", 0) * 1000  # Convert thousands to actual
        estimated_hotel_beds = int((arrivals * 0.30 * 7) / (365 * 0.60))
        hotel_beds = max(1000, estimated_hotel_beds)  # Minimum 1000 beds

        countries.append(
            {
                "code": data["code"],
                "name": data["name"],
                "hotel_beds": hotel_beds,
                "attractiveness": data["ttdi"] if data["ttdi"] > 0 else 3.5,
                "cost_index": data["cost_index"] if data["cost_index"] > 0 else 50.0,
                "risk_score": data["risk_score"] if data["risk_score"] >= 0 else 0.2,
                "lat": data["lat"],
                "lon": data["lon"],
            }
        )

    print(f"Loaded {len(countries)} countries from {data_file}")
    return countries


def _create_placeholder_countries() -> List[Dict]:
    """
    Create placeholder countries for testing when data is unavailable.

    Returns:
        List of 10 placeholder country dicts
    """
    placeholders = [
        {"code": "FR", "name": "France", "lat": 46.2276, "lon": 2.2137},
        {"code": "US", "name": "United States", "lat": 37.0902, "lon": -95.7129},
        {"code": "CN", "name": "China", "lat": 35.8617, "lon": 104.1954},
        {"code": "ES", "name": "Spain", "lat": 40.4637, "lon": -3.7492},
        {"code": "IT", "name": "Italy", "lat": 41.8719, "lon": 12.5674},
        {"code": "GB", "name": "United Kingdom", "lat": 51.1657, "lon": -10.4515},
        {"code": "DE", "name": "Germany", "lat": 51.1657, "lon": 10.4515},
        {"code": "TH", "name": "Thailand", "lat": 15.8700, "lon": 100.9925},
        {"code": "AU", "name": "Australia", "lat": -25.2744, "lon": 133.7751},
        {"code": "BR", "name": "Brazil", "lat": -14.2350, "lon": -51.9253},
    ]

    countries = []
    for p in placeholders:
        countries.append(
            {
                "code": p["code"],
                "name": p["name"],
                "hotel_beds": 50000,
                "attractiveness": 4.0,
                "cost_index": 50.0,
                "risk_score": 0.2,
                "lat": p["lat"],
                "lon": p["lon"],
            }
        )

    print(f"Created {len(countries)} placeholder countries")
    return countries


def load_centroids(data_dir: Path = None) -> Dict[str, Dict]:
    """
    Load country centroids from derived data.

    Args:
        data_dir: Path to data directory

    Returns:
        Dict of country_code → {lat, lon}
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent.parent / "data" / "derived"

    centroids = {}
    centroids_file = data_dir / "country_centroids.csv"

    if not centroids_file.exists():
        return {}

    with open(centroids_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("code", row.get("country_code", ""))
            if code:
                centroids[code] = {
                    "lat": float(row.get("lat", row.get("latitude", 0.0))),
                    "lon": float(row.get("lon", row.get("longitude", 0.0))),
                }

    return centroids
