"""
Destination class with capacity tracking and TFI dynamics.
Models crowding, resident attitudes, and policy responses.
"""

from typing import Dict, Optional, List
from collections import deque


# TFI dynamics parameters
TFI_BASELINE = 0.80
TFI_DECLINE_RATE = 0.05  # per tick when crowding > 80%
TFI_RECOVERY_RATE = 0.02  # per tick (hysteresis: slower than decline)
CROWDING_THRESHOLD = 0.80

# Tourism dependency modifier (applied to TFI_DECLINE_RATE)
# Higher tourism-GDP % = slower TFI decline (economic necessity)
TFI_DEPENDENCY_MODIFIER = {
    "highly_dependent": 0.5,  # 50% slower decline
    "moderately_dependent": 0.75,  # 25% slower decline
    "low_dependency": 1.0,  # Normal decline
    "minimal_dependency": 1.0,  # Normal decline
}

# Policy thresholds
TFI_SEVERE_THRESHOLD = 0.40  # Capacity × 0.70
TFI_MODERATE_THRESHOLD = 0.60  # Capacity × 0.85

# Capacity modifiers by policy level
CAPACITY_SEVERE = 0.70
CAPACITY_MODERATE = 0.85


class Destination:
    """
    Destination country with capacity, TFI, and dynamic attributes.
    """

    def __init__(
        self,
        country_code: str,
        country_name: str,
        hotel_beds: int,
        attractiveness: float,
        cost_index: float,
        risk_score: float,
        latitude: float,
        longitude: float,
        climate_zone: Optional[str] = None,
        tourism_gdp_pct: Optional[float] = None,
        dependency_category: Optional[str] = None,
    ):
        """
        Initialize destination.

        Args:
            country_code: ISO 3166-1 alpha-2 code
            country_name: Full country name
            hotel_beds: Total hotel beds (from UN Tourism)
            attractiveness: TTDI score (2.78-5.24)
            cost_index: Numbeo cost index (26.6-135.8)
            risk_score: ACLED-derived risk (0.0-1.0)
            latitude: Country centroid latitude
            longitude: Country centroid longitude
            climate_zone: 'Northern', 'Southern', or 'Tropical' (auto-assigned if None)
            tourism_gdp_pct: Tourism GDP percentage (0-100+)
            dependency_category: 'highly_dependent', 'moderately_dependent', 'low_dependency', or 'minimal_dependency'
        """
        self.country_code = country_code
        self.country_name = country_name

        # Capacity: hotel beds × 0.80 × 0.15 (reduced for realistic crowding dynamics)
        # Original: 0.80 × 1.10 = 0.88 (88% of hotel beds)
        # Adjusted: 0.80 × 0.15 = 0.12 (12% of hotel beds) to trigger TFI dynamics
        # Rationale: Real destinations experience crowding at lower occupancy due to:
        #            - Geographic concentration (tourists cluster in specific areas)
        #            - Seasonal peaks (10x average during high season)
        #            - Infrastructure limits (roads, attractions, restaurants)
        #            - Day trippers not counted in hotel stays
        #            - Overtourism occurs at specific sites, not country-wide
        self.base_capacity = int(hotel_beds * 0.80 * 0.15)

        # Tourism dependency (for TFI dynamics)
        self.tourism_gdp_pct = tourism_gdp_pct if tourism_gdp_pct is not None else 0.0
        self.dependency_category = (
            dependency_category
            if dependency_category is not None
            else "minimal_dependency"
        )
        self.tfi_decline_modifier = TFI_DEPENDENCY_MODIFIER.get(
            self.dependency_category, 1.0
        )

        # Core attributes
        self.attractiveness = attractiveness
        self.cost_index = cost_index
        self.risk_score = risk_score
        self.latitude = latitude
        self.longitude = longitude

        # Climate zone (auto-assign if not provided)
        if climate_zone is None:
            from simulation.dynamics.seasonality import assign_climate_zone

            self.climate_zone = assign_climate_zone(latitude)
        else:
            self.climate_zone = climate_zone

        # TFI dynamics
        self.tfi = TFI_BASELINE

        # Rolling visitor count (30-day window)
        self.daily_arrivals = deque(maxlen=30)

        # Memory of past visitors (for memory utility factor)
        self.visitor_memories: Dict[str, float] = {}

        # History tracking
        self.arrivals_history: List[int] = []
        self.tfi_history: List[float] = []

        # Current tick
        self.current_tick = 0

    def get_crowding_ratio(self) -> float:
        """
        Calculate current crowding ratio.

        Returns:
            visitors / capacity (can exceed 1.0 when overcrowded)
        """
        current_visitors = sum(self.daily_arrivals)
        return current_visitors / self.base_capacity if self.base_capacity > 0 else 0.0

    def get_effective_capacity(self) -> int:
        """
        Get capacity modified by TFI policy responses.

        Returns:
            Effective capacity (reduced when TFI is low)
        """
        if self.tfi < TFI_SEVERE_THRESHOLD:
            return int(self.base_capacity * CAPACITY_SEVERE)
        elif self.tfi < TFI_MODERATE_THRESHOLD:
            return int(self.base_capacity * CAPACITY_MODERATE)
        else:
            return self.base_capacity

    def get_current_visitors(self) -> int:
        """
        Get current number of visitors (30-day rolling sum).

        Returns:
            Current visitor count
        """
        return sum(self.daily_arrivals)

    def add_arrival(self, count: int = 1):
        """
        Record new arrival(s).

        Args:
            count: Number of arriving tourists
        """
        if len(self.daily_arrivals) == 0:
            # First arrival: initialize with count
            self.daily_arrivals.append(count)
        else:
            # Add to most recent day
            self.daily_arrivals[-1] += count

    def update(self, tick: int):
        """
        Update destination state for new tick.

        Args:
            tick: Current simulation tick
        """
        self.current_tick = tick

        # Update TFI based on crowding
        crowding = self.get_crowding_ratio()

        if crowding > CROWDING_THRESHOLD:
            # Resident hostility grows (fast decline)
            # Modified by tourism dependency: highly dependent economies decline slower
            modified_decline = TFI_DECLINE_RATE * self.tfi_decline_modifier
            self.tfi = max(0.0, self.tfi - modified_decline)
        else:
            # Recovery toward baseline (slow, with hysteresis)
            self.tfi = min(TFI_BASELINE, self.tfi + TFI_RECOVERY_RATE)

        # Record history
        self.arrivals_history.append(self.get_current_visitors())
        self.tfi_history.append(self.tfi)

    def get_memory_score(self, tourist) -> float:
        """
        Get memory score for a specific tourist.

        Args:
            tourist: Tourist agent

        Returns:
            Memory score (-1.0 to +1.0)
            +1.0 = very positive past experience
            0.0 = no history
            -1.0 = very negative past experience
        """
        if tourist.agent_id in self.visitor_memories:
            return self.visitor_memories[tourist.agent_id]
        else:
            return 0.0  # No history

    def record_satisfaction(self, tourist, satisfaction: float):
        """
        Record satisfaction score from departing tourist.

        Args:
            tourist: Departing tourist agent
            satisfaction: Score (-1.0 to +1.0)
        """
        self.visitor_memories[tourist.agent_id] = satisfaction

    def get_seasonal_multiplier(self, month: int) -> float:
        """
        Get seasonal multiplier for current month.

        Args:
            month: Month number (1-12)

        Returns:
            Multiplier (0.8-1.2)
        """
        from simulation.dynamics.seasonality import get_seasonal_multiplier

        return get_seasonal_multiplier(self.climate_zone, month)

    def get_crowding_level(self) -> tuple:
        """
        Get crowding level and color indicator.

        Returns:
            Tuple of (level_name, color_hex)
            LOW/GREEN, MEDIUM/YELLOW, HIGH/ORANGE, CRITICAL/RED
        """
        ratio = self.get_crowding_ratio()

        if ratio < 0.55:
            return "LOW", "#4CAF50"  # Green
        elif ratio < 0.80:
            return "MEDIUM", "#FFC107"  # Yellow
        elif ratio < 1.0:
            return "HIGH", "#FF9800"  # Orange
        else:
            return "CRITICAL", "#F44336"  # Red

    def get_rectification_suggestions(self) -> List[str]:
        """
        Get policy suggestions when overcrowded.

        Returns:
            List of policy suggestions
        """
        ratio = self.get_crowding_ratio()

        if ratio < 0.80:
            return []

        suggestions = []

        if ratio >= 1.0:
            suggestions.extend(
                [
                    "Implement tourist tax increase",
                    "Cap daily arrivals",
                    "Promote alternative destinations",
                    "Suspend marketing campaigns",
                ]
            )
        elif ratio >= 0.80:
            suggestions.extend(
                [
                    "Monitor visitor growth",
                    "Consider seasonal pricing",
                    "Develop infrastructure capacity",
                ]
            )

        return suggestions

    def to_dict(self) -> dict:
        """
        Convert destination state to dictionary.

        Returns:
            Dictionary with destination state
        """
        crowding_level, color = self.get_crowding_level()

        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "base_capacity": self.base_capacity,
            "effective_capacity": self.get_effective_capacity(),
            "current_visitors": self.get_current_visitors(),
            "crowding_ratio": self.get_crowding_ratio(),
            "crowding_level": crowding_level,
            "crowding_color": color,
            "tfi": self.tfi,
            "tfi_trend": "declining" if self.tfi < TFI_BASELINE else "stable",
            "attractiveness": self.attractiveness,
            "cost_index": self.cost_index,
            "risk_score": self.risk_score,
            "climate_zone": self.climate_zone,
            "tourism_gdp_pct": self.tourism_gdp_pct,
            "dependency_category": self.dependency_category,
            "tfi_decline_modifier": self.tfi_decline_modifier,
        }
