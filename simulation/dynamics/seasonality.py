"""
Seasonality patterns by climate zone.
Latitude-based climate assignment with monthly multipliers.
"""

from typing import Dict


def assign_climate_zone(latitude: float) -> str:
    """
    Assign climate zone based on latitude.

    Args:
        latitude: Country centroid latitude (-90 to +90)

    Returns:
        Climate zone: 'Northern', 'Southern', or 'Tropical'
    """
    if abs(latitude) < 23.5:
        return "Tropical"
    elif latitude >= 23.5:
        return "Northern"
    else:
        return "Southern"


# Seasonal multipliers by month (1-12)
# Peak = 1.2 (20% boost), Shoulder = 1.0 (baseline), Low = 0.8 (20% reduction)
SEASONAL_PATTERNS: Dict[str, Dict[int, float]] = {
    "Northern": {
        1: 0.8,  # January - low
        2: 0.8,  # February - low
        3: 0.8,  # March - low
        4: 1.0,  # April - shoulder
        5: 1.0,  # May - shoulder
        6: 1.2,  # June - peak
        7: 1.2,  # July - peak
        8: 1.2,  # August - peak
        9: 1.0,  # September - shoulder
        10: 1.0,  # October - shoulder
        11: 0.8,  # November - low
        12: 1.2,  # December - peak (Christmas)
    },
    "Southern": {
        # Inverted: peak in Dec-Feb (their summer)
        1: 1.2,
        2: 1.2,
        3: 1.0,
        4: 1.0,
        5: 0.8,
        6: 1.2,
        7: 1.2,
        8: 0.8,
        9: 1.0,
        10: 1.0,
        11: 0.8,
        12: 1.2,
    },
    "Tropical": {
        # Dry season = peak, monsoon = low
        1: 1.2,
        2: 1.2,
        3: 1.0,
        4: 1.0,
        5: 0.8,
        6: 0.8,
        7: 1.2,
        8: 1.2,
        9: 1.0,
        10: 1.0,
        11: 0.8,
        12: 1.2,
    },
}


def get_seasonal_multiplier(climate_zone: str, month: int) -> float:
    """
    Get seasonal multiplier for a given climate zone and month.

    Args:
        climate_zone: 'Northern', 'Southern', or 'Tropical'
        month: Month number (1-12)

    Returns:
        Multiplier (0.8-1.2)
    """
    if climate_zone not in SEASONAL_PATTERNS:
        raise ValueError(f"Unknown climate zone: {climate_zone}")

    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}")

    return SEASONAL_PATTERNS[climate_zone][month]
