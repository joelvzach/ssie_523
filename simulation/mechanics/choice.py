"""
Softmax choice mechanism for destination selection.
Probabilistic choice with segment-specific temperature.
"""

import math
import random
from typing import List, Optional

from simulation.mechanics.utility import SEGMENT_TEMPERATURE


def softmax(utilities: List[float], temperature: float) -> List[float]:
    """
    Convert utilities to probabilities using softmax with temperature.

    Args:
        utilities: List of utility scores
        temperature: Control parameter (lower = more deterministic)

    Returns:
        List of probabilities (sum to 1.0)
    """
    if not utilities:
        return []

    # Numerical stability: subtract max utility
    max_u = max(utilities)

    # Compute exp(u/τ) for each utility
    exp_utils = [math.exp((u - max_u) / temperature) for u in utilities]

    # Normalize to probabilities
    total = sum(exp_utils)
    if total == 0:
        # Fallback to uniform if all utilities are -inf
        n = len(utilities)
        return [1.0 / n] * n if n > 0 else []

    probabilities = [e / total for e in exp_utils]
    return probabilities


def weighted_random_choice(choices: List, probabilities: List[float]):
    """
    Make weighted random choice from list of options.

    Args:
        choices: List of options to choose from
        probabilities: List of probabilities (should sum to 1.0)

    Returns:
        Selected choice
    """
    if not choices or not probabilities:
        return None

    # Ensure probabilities sum to 1.0 (handle floating point errors)
    total = sum(probabilities)
    if total <= 0:
        return random.choice(choices)

    # Normalize
    probs = [p / total for p in probabilities]

    # Cumulative sum
    cumsum = []
    running_total = 0.0
    for p in probs:
        running_total += p
        cumsum.append(running_total)

    # Random draw
    r = random.random()

    # Find first cumulative probability >= r
    for i, cum_prob in enumerate(cumsum):
        if cum_prob >= r:
            return choices[i]

    # Fallback (should rarely happen due to floating point)
    return choices[-1]


def choose_destination(
    tourist,
    destinations: List,
    distance_matrix: dict,
    visa_lookup_func=None,
    event_bonus_func=None,
    tick: int = 0,
    capture_decision_data: bool = False,
) -> Optional[str]:
    """
    Choose destination using softmax probabilistic choice.

    Args:
        tourist: Tourist agent
        destinations: List of Destination objects (typically top 50)
        distance_matrix: Pre-computed distance matrix
        visa_lookup_func: Function to get visa friction (country_code, origin_code)
        event_bonus_func: Function to get event bonus (destination, tourist, tick)
        tick: Current simulation tick
        capture_decision_data: If True, store detailed decision breakdown in tourist.last_decision

    Returns:
        Selected destination country code (or None if no accessible destinations)
    """
    from simulation.mechanics.utility import calculate_utility, SEGMENT_WEIGHTS
    from simulation.data.visa_restrictions import get_visa_friction

    # 1. Filter by visa restrictions (exclude BANNED only)
    accessible = []
    for dest in destinations:
        if visa_lookup_func:
            # Use home_country_code for visa lookup (numeric/ISO3 code)
            origin_code = tourist.home_country_code
            friction = visa_lookup_func(dest.country_code, origin_code)
            if friction >= 1.0:  # BANNED
                continue
        accessible.append(dest)

    if not accessible:
        return None

    # 2. Calculate utilities for each accessible destination
    utilities = []
    destination_data = []
    for dest in accessible:
        # Use home_country_code for distance lookup
        origin_code = tourist.home_country_code
        distance = distance_matrix.get((origin_code, dest.country_code), 0.0)

        event_bonus = 0.0
        if event_bonus_func:
            event_bonus = event_bonus_func(dest, tourist, tick)

        visa_friction = 0.0
        if visa_lookup_func:
            visa_friction = get_visa_friction(dest.country_code, origin_code)

        utility = calculate_utility(
            tourist,
            dest,
            distance,
            event_bonus=event_bonus,
            visa_friction=visa_friction,
        )
        utilities.append(utility)

        # Capture factor breakdown for decision transparency
        if capture_decision_data:
            weights = SEGMENT_WEIGHTS[tourist.segment]
            att_norm = dest.attractiveness / 5.0
            cost_norm = dest.cost_index / 100.0
            crowd_norm = dest.get_crowding_ratio()
            risk_norm = dest.risk_score / 10.0
            dist_norm = min(distance / 10000.0, 1.0)
            memory_norm = 1.0 if dest.country_code in tourist.visited_destinations else 0.0

            destination_data.append({
                "country_code": dest.country_code,
                "country_name": dest.country_name,
                "utility": utility,
                "attractiveness": weights["α"] * att_norm,
                "cost": -weights["β"] * cost_norm,
                "crowding": -weights["γ"] * crowd_norm,
                "risk": -weights["δ"] * risk_norm,
                "distance": -weights["η"] * dist_norm,
                "memory": weights["ζ"] * memory_norm,
                "event_bonus": event_bonus,
                "visa_friction": -visa_friction,
            })

    # 3. Apply softmax with segment temperature
    tau = SEGMENT_TEMPERATURE[tourist.segment]
    probabilities = softmax(utilities, tau)

    # 4. Weighted random choice
    chosen = weighted_random_choice(accessible, probabilities)

    # 5. Capture decision data for dashboard visualization
    if capture_decision_data and hasattr(tourist, 'agent_id'):
        decision_data = {
            "tick": tick,
            "agent_id": tourist.agent_id,
            "segment": tourist.segment,
            "home_country": tourist.home_country,
            "home_country_code": tourist.home_country_code,
            "chosen": chosen.country_code if chosen else None,
            "destinations": [],
        }

        for i, dest_data in enumerate(destination_data):
            dest_data["probability"] = probabilities[i]
            decision_data["destinations"].append(dest_data)

        # Sort by probability (descending)
        decision_data["destinations"].sort(key=lambda x: x["probability"], reverse=True)

        # Store in agent for dashboard access
        tourist.last_decision = decision_data

    return chosen.country_code if chosen else None
