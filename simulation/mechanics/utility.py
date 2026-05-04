"""
6-factor utility function with segment-specific weights.
U = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk - η·Distance + ζ·Memory
"""

from typing import Dict


# Segment-specific utility weights (sum to 1.0)
SEGMENT_WEIGHTS = {
    "budget": {"α": 0.20, "β": 0.27, "γ": 0.11, "δ": 0.08, "η": 0.34, "ζ": 0.05},
    "luxury": {"α": 0.28, "β": 0.12, "γ": 0.09, "δ": 0.09, "η": 0.17, "ζ": 0.15},
    "adventure": {"α": 0.28, "β": 0.10, "γ": 0.09, "δ": 0.11, "η": 0.22, "ζ": 0.15},
    "family": {"α": 0.21, "β": 0.18, "γ": 0.14, "δ": 0.14, "η": 0.40, "ζ": 0.02},
}

# Default weights for decision breakdown (use budget as default)
WEIGHTS = SEGMENT_WEIGHTS["budget"]

# Segment-specific temperature for softmax choice
SEGMENT_TEMPERATURE = {
    "budget": 1.2,  # More random exploration
    "luxury": 0.8,  # More deterministic
    "adventure": 1.5,  # Highly exploratory
    "family": 1.0,  # Moderate
}

# Business probability by segment (produces ~11% overall)
BUSINESS_PROBABILITY = {
    "budget": 0.15,
    "luxury": 0.40,
    "adventure": 0.05,
    "family": 0.00,
}

# Normalization ranges for utility factors
NORM_RANGES = {
    "attractiveness": (2.78, 5.24),  # TTDI range
    "cost": (26.6, 135.8),  # Numbeo range
    "crowding": (0.0, 2.0),  # Can exceed 1.0 (overcrowded)
    "risk": (0.0, 1.0),  # Already normalized
    "distance": (0.0, 20000.0),  # Max Earth distance in km
    "memory": (-1.0, 1.0),  # Satisfaction score
}


def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize value to 0-1 range.

    Args:
        value: Raw value
        min_val: Minimum of range
        max_val: Maximum of range

    Returns:
        Normalized value (clamped to 0-1)
    """
    if max_val == min_val:
        return 0.5

    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def calculate_utility(
    tourist,
    destination,
    distance_km: float,
    event_bonus: float = 0.0,
    visa_friction: float = 0.0,
) -> float:
    """
    Calculate utility for a tourist considering a destination.

    Args:
        tourist: Tourist agent with segment, purpose, utility_weights
        destination: Destination with attractiveness, cost, risk, crowding
        distance_km: Distance from home to destination
        event_bonus: Optional bonus from planned events
        visa_friction: Friction from visa restrictions (0.0-1.0)

    Returns:
        Utility score (higher = more attractive)
    """
    # Get weights for this tourist's segment
    weights = SEGMENT_WEIGHTS[tourist.segment]

    # Normalize all factors to 0-1
    att_norm = normalize(destination.attractiveness, *NORM_RANGES["attractiveness"])
    cost_norm = normalize(destination.cost_index, *NORM_RANGES["cost"])
    crowd_norm = normalize(destination.get_crowding_ratio(), *NORM_RANGES["crowding"])
    risk_norm = normalize(destination.risk_score, *NORM_RANGES["risk"])
    dist_norm = normalize(distance_km, *NORM_RANGES["distance"])

    # Memory score (-1 to +1, normalized to utility contribution)
    memory_score = destination.get_memory_score(tourist)
    memory_norm = (memory_score + 1) / 2  # Convert -1..1 to 0..1

    # Calculate base utility
    utility = (
        weights["α"] * att_norm
        - weights["β"] * cost_norm
        - weights["γ"] * crowd_norm
        - weights["δ"] * risk_norm
        - weights["η"] * dist_norm
        + weights["ζ"] * memory_norm
    )

    # Business purpose modifier (Peng et al.: less price-sensitive)
    if tourist.purpose == "business":
        # Reduce cost sensitivity by 70%
        utility += weights["β"] * cost_norm * 0.70

    # Add event bonus
    utility += event_bonus

    # Subtract visa friction
    utility -= visa_friction * 0.5  # Scale factor for visa impact

    return utility
