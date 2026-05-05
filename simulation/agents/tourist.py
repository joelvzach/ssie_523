"""
Tourist agent class with state machine and trip frequency model.
States: HOME → CHOOSING → TRAVELING → RETURNING → HOME
"""

import random
from typing import Dict, Optional, List
from datetime import datetime

from simulation.mechanics.utility import (
    SEGMENT_WEIGHTS,
    SEGMENT_TEMPERATURE,
    BUSINESS_PROBABILITY,
)
from simulation.dynamics.seasonality import get_seasonal_multiplier


# Base stay duration by segment (days)
BASE_STAY = {
    "budget": 7,
    "luxury": 14,
    "adventure": 21,
    "family": 10,
}

# Trips per year by segment
# Calibrated to achieve target segment distribution in active tourists
# Target: budget 30%, luxury 20%, adventure 25%, family 25%
# Adjusted: Reduced luxury/adventure frequency, increased budget/family
TRIPS_PER_YEAR = {
    "budget": 2.0,  # Increased from 0.75 (more frequent short trips)
    "luxury": 1.0,  # Reduced from 3.0 (fewer but longer trips)
    "adventure": 0.75,  # Reduced from 1.5 (fewer trips)
    "family": 1.5,  # Increased from 0.75 (school holidays, regular trips)
}

# Planning duration ranges by segment (days spent in CHOOSING state)
# Reflects realistic trip planning behavior differences
PLANNING_RANGE = {
    "budget": (3, 7),     # Spontaneous, less planning needed
    "luxury": (7, 14),    # More research, bookings, itineraries
    "adventure": (3, 10), # Moderate planning, some spontaneity
    "family": (5, 12),    # Coordinate schedules, school holidays
}


class Tourist:
    """
    Tourist agent that makes destination choices based on utility function.
    """

    def __init__(self, agent_id: str, segment: str, home_country: str, home_country_code: str = None):
        """
        Initialize tourist agent.

        Args:
            agent_id: Unique identifier
            segment: 'budget', 'luxury', 'adventure', or 'family'
            home_country: Home country name (e.g., 'United States of America', 'France')
            home_country_code: Home country code (e.g., '840', '250') for distance/visa lookups
        """
        self.agent_id = agent_id
        self.segment = segment
        self.home_country = home_country  # Country name for display
        self.home_country_code = home_country_code or home_country  # Code for lookups (fallback to name)

        # Determine purpose based on segment
        self.purpose = (
            "business"
            if random.random() < BUSINESS_PROBABILITY[segment]
            else "personal"
        )

        # State machine
        self.state = "HOME"  # HOME, CHOOSING, TRAVELING
        self.current_destination: Optional[str] = None
        self.arrival_tick: Optional[int] = None
        self.stay_duration: int = 0
        self.days_remaining: int = 0

        # Trip scheduling
        self.trips_per_year = TRIPS_PER_YEAR[segment]
        self.days_until_next_trip = self._sample_next_trip_interval()

        # Planning phase (CHOOSING state duration) - segment-specific
        self.planning_days = random.randint(*PLANNING_RANGE[segment])
        self.days_in_choosing = 0

        # Memory (visited destinations → satisfaction scores)
        self.visited_destinations: Dict[str, float] = {}

        # Utility weights (from segment)
        self.utility_weights = SEGMENT_WEIGHTS[segment]
        self.segment_temperature = SEGMENT_TEMPERATURE[segment]

    def _sample_next_trip_interval(self) -> int:
        """
        Sample time until next trip from exponential distribution.

        Returns:
            Days until next trip decision
        """
        # Exponential distribution with mean = 365 / trips_per_year
        mean_interval = 365.0 / self.trips_per_year
        return int(random.expovariate(1.0 / mean_interval)) + 1

    def _calculate_stay_duration(self, distance_km: float) -> int:
        """
        Calculate stay duration based on segment and distance.

        80% follow trend: farther = longer stays
        20% are exceptions (random variation)

        Args:
            distance_km: Distance from home to destination

        Returns:
            Stay duration in days
        """
        base = BASE_STAY[self.segment]

        if random.random() < 0.80:
            # 80% follow distance trend
            if distance_km < 1000:
                duration = base * 0.7
            elif distance_km < 5000:
                duration = base * 1.0
            else:
                duration = base * 1.4
        else:
            # 20% exceptions (random variation)
            duration = base * random.uniform(0.5, 2.0)

        return int(round(duration))

    def should_start_trip(
        self,
        current_month: int,
        seasonal_multiplier: float = 1.0,
        event_multiplier: float = 1.0,
    ) -> bool:
        """
        Determine if agent should start a trip this day.

        Uses Poisson process with seasonal and event modulation.
        The exponential distribution already models the timing, so when
        counter reaches 0, it's time to travel.

        Args:
            current_month: Month number (1-12)
            seasonal_multiplier: Seasonal adjustment (0.8-1.2)
            event_multiplier: Event-driven adjustment (1.0+)

        Returns:
            True if agent should start trip
        """
        if self.state != "HOME":
            return False

        # Decrement counter
        self.days_until_next_trip -= 1

        # When counter reaches 0, it's time to choose a destination
        # (the exponential distribution already incorporates the trip frequency rate)
        if self.days_until_next_trip <= 0:
            return True

        return False

    def choose_destination(
        self,
        destinations: List,
        distance_matrix: dict,
        visa_lookup_func=None,
        event_bonus_func=None,
        tick: int = 0,
        capture_decision_data: bool = False,
    ) -> Optional[str]:
        """
        Choose destination using utility-based softmax choice.

        Args:
            destinations: List of Destination objects
            distance_matrix: Pre-computed distance matrix
            visa_lookup_func: Visa friction lookup function
            event_bonus_func: Event bonus function
            tick: Current simulation tick
            capture_decision_data: If True, store detailed decision breakdown

        Returns:
            Selected destination country code
        """
        from simulation.mechanics.choice import choose_destination as choice_func

        self.state = "CHOOSING"
        # Sample new planning duration for this trip (segment-specific)
        self.planning_days = random.randint(*PLANNING_RANGE[self.segment])
        self.days_in_choosing = self.planning_days
        self._chosen_destination = None  # Store chosen destination for travel_to call

        chosen_code = choice_func(
            self,
            destinations,
            distance_matrix,
            visa_lookup_func=visa_lookup_func,
            event_bonus_func=event_bonus_func,
            tick=tick,
            capture_decision_data=capture_decision_data,
        )

        self._chosen_destination = chosen_code
        return chosen_code

    def ready_to_travel(self) -> bool:
        """
        Check if agent has completed planning and is ready to travel.

        Returns:
            True if planning period is complete
        """
        return self.state == "CHOOSING" and self.days_in_choosing <= 0

    def get_chosen_destination(self) -> Optional[str]:
        """
        Get the destination chosen during planning phase.

        Returns:
            Destination country code
        """
        return self._chosen_destination

    def travel_to(
        self, destination_code: str, arrival_tick: int, distance_km: float = 0.0
    ):
        """
        Begin trip to destination.

        Args:
            destination_code: Destination country code
            arrival_tick: Current simulation tick
            distance_km: Distance traveled (for stay duration calculation)
        """
        self.state = "TRAVELING"
        self.current_destination = destination_code
        self.arrival_tick = arrival_tick
        self.stay_duration = self._calculate_stay_duration(distance_km)
        self.days_remaining = self.stay_duration
        self._chosen_destination = None  # Clear after trip starts

    def step(self):
        """
        Advance agent state by one day.

        Call this daily for CHOOSING and TRAVELING agents.
        """
        if self.state == "CHOOSING":
            # Count down planning days
            self.days_in_choosing -= 1
            # State transition to TRAVELING handled by simulation
        elif self.state == "TRAVELING":
            self.days_remaining -= 1

            if self.days_remaining <= 0:
                self.return_home()

    def return_home(self):
        """
        Return home after trip completion.
        Records satisfaction and resets state.
        """
        if self.current_destination:
            # Calculate satisfaction based on experience
            # (simplified: based on crowding and random factor)
            satisfaction = random.uniform(0.3, 1.0)
            self.visited_destinations[self.current_destination] = satisfaction

            # Update trip record with departure tick
            if hasattr(self, "_current_trip_record") and self._current_trip_record:
                self._current_trip_record["departure_tick"] = (
                    self.arrival_tick + self.stay_duration
                )
                self._current_trip_record["duration"] = self.stay_duration

        self.state = "HOME"
        self.current_destination = None
        self.arrival_tick = None
        self.stay_duration = 0
        self.days_remaining = 0

        # Schedule next trip
        self.days_until_next_trip = self._sample_next_trip_interval()

    def get_traveling_days(self) -> int:
        """
        Get total days spent traveling (all trips).

        Returns:
            Total days in TRAVELING state
        """
        total = 0
        for dest, satisfaction in self.visited_destinations.items():
            # Approximate: use average stay duration
            total += BASE_STAY[self.segment]
        return total

    def to_dict(self) -> dict:
        """
        Convert agent state to dictionary for serialization.

        Returns:
            Dictionary with agent state
        """
        return {
            "agent_id": self.agent_id,
            "segment": self.segment,
            "home_country": self.home_country,
            "purpose": self.purpose,
            "state": self.state,
            "current_destination": self.current_destination,
            "days_remaining": self.days_remaining,
            "trips_taken": len(self.visited_destinations),
        }
