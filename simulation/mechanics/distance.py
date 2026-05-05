"""
Distance calculations using Haversine formula.
Pre-computes all pairwise distances for O(1) lookup during simulation.
"""

import math
from typing import Dict, Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Coordinates of point 1 (in degrees)
        lat2, lon2: Coordinates of point 2 (in degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km

    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def precompute_distance_matrix(countries: list) -> Dict[Tuple[str, str], float]:
    """
    Pre-compute all pairwise distances between countries.

    Args:
        countries: List of dicts with 'code', 'lat', 'lon' keys

    Returns:
        Dictionary mapping (origin_code, dest_code) → distance_km
    """
    matrix = {}

    for origin in countries:
        for dest in countries:
            if origin["code"] != dest["code"]:
                dist = haversine(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
                matrix[(origin["code"], dest["code"])] = dist

    return matrix


def get_distance(
    origin_code: str, dest_code: str, matrix: Dict[Tuple[str, str], float]
) -> float:
    """
    Get pre-computed distance between two countries.

    Args:
        origin_code: Origin country code
        dest_code: Destination country code
        matrix: Pre-computed distance matrix

    Returns:
        Distance in kilometers (0.0 if same country)
    """
    if origin_code == dest_code:
        return 0.0

    return matrix.get((origin_code, dest_code), 0.0)
