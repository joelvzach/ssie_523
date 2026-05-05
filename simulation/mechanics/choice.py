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

    # 2. Two-stage choice: First decide trip type (regional vs long-haul)
    # This mimics real tourism: people first decide "nearby or far?" then pick place
    import random
    
    regional_prob = {
        'budget': 0.70,
        'luxury': 0.60,
        'adventure': 0.55,
        'family': 0.75,
    }.get(tourist.segment, 0.65)
    
    trip_type_roll = random.random()
    prefer_regional = trip_type_roll < regional_prob
    
    # Load ISO3 to numeric mapping for distance lookup
    import csv
    from pathlib import Path
    project_root = Path("/Users/joelvzach/Code/ssie_523")
    mapping_file = project_root / "data" / "derived" / "country_code_mapping.csv"
    iso3_to_numeric = {}
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                numeric_code = row.get("country_code", "")
                iso3_code = row.get("Country Code", "")
                if numeric_code and iso3_code:
                    iso3_to_numeric[iso3_code] = numeric_code
    
    # Convert ISO3 codes to numeric for distance lookup
    origin_numeric = iso3_to_numeric.get(tourist.home_country_code, tourist.home_country_code)
    
    # Filter destinations based on trip type preference
    # This ensures agents actually choose from their preferred category
    filtered_accessible = []
    for dest in accessible:
        dest_numeric = iso3_to_numeric.get(dest.country_code, dest.country_code)
        distance = distance_matrix.get((origin_numeric, dest_numeric), 0.0)
        is_regional = distance < 4000
        
        # Keep destination if it matches preference, OR if it's a top global destination
        # (allows some long-haul to major attractions even for regional-preferring agents)
        if prefer_regional:
            if is_regional or dest.base_capacity > 5000:  # Keep mega-destinations
                filtered_accessible.append((dest, distance))
        else:
            if not is_regional or dest.base_capacity > 10000:  # Keep only far or mega
                filtered_accessible.append((dest, distance))
    
    # If filtering left us with nothing, use all accessible
    if not filtered_accessible:
        filtered_accessible = [(dest, distance_matrix.get((origin_numeric, iso3_to_numeric.get(dest.country_code, dest.country_code)), 0.0)) 
                               for dest in accessible]
    
    # 3. Calculate utilities for filtered destinations
    utilities = []
    destination_data = []
    for dest, distance in filtered_accessible:
        dest_numeric = iso3_to_numeric.get(dest.country_code, dest.country_code)
        origin_code = tourist.home_country_code  # Keep ISO3 for visa lookup

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
    
    # Replace accessible with filtered list for choice
    accessible = [dest for dest, _ in filtered_accessible]
    


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
