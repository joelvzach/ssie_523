"""
Planned events system for predictable tourism boosters.
Examples: FIFA World Cup, Olympics, cultural festivals.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math


class PlannedEvent:
    """
    A planned event that boosts destination attractiveness.
    """

    def __init__(
        self,
        name: str,
        country_code: str,
        start_date: datetime,
        end_date: datetime,
        magnitude: float = 0.5,
        segment_appeal: Dict[str, float] = None,
        expected_footfall: int = 100000,
        pre_event_days: int = 30,
    ):
        """
        Initialize planned event.

        Args:
            name: Event name (e.g., "FIFA World Cup 2026")
            country_code: Host country code
            start_date: Event start date
            end_date: Event end date
            magnitude: Base impact strength (0.0-1.0)
            segment_appeal: Appeal by segment (0.0-1.0)
            expected_footfall: Expected additional visitors
            pre_event_days: Days before event for ramp-up (linear increase from 0% to 30% of full effect)
        """
        self.name = name
        self.country_code = country_code
        self.start_date = start_date
        self.end_date = end_date
        self.magnitude = magnitude
        self.expected_footfall = expected_footfall
        self.pre_event_days = pre_event_days
        self.pre_event_start = start_date - timedelta(days=pre_event_days)

        # Default segment appeal (can be customized)
        self.segment_appeal = segment_appeal or {
            "budget": 0.6,
            "luxury": 0.7,
            "adventure": 0.5,
            "family": 0.8,
        }

        # Calculate event duration
        self.duration_days = (end_date - start_date).days + 1
        self.peak_date = start_date + timedelta(days=self.duration_days // 2)

    def is_active(self, tick_date: datetime) -> bool:
        """
        Check if event is active on given date (during event period only).

        Args:
            tick_date: Current simulation date

        Returns:
            True if event is within start_date and end_date
        """
        return self.start_date <= tick_date <= self.end_date

    def has_utility_bonus(self, tick_date: datetime) -> bool:
        """
        Check if event provides utility bonus on given date.

        Includes pre-event ramp-up and post-event decline periods.

        Args:
            tick_date: Current simulation date

        Returns:
            True if event provides any utility bonus
        """
        # Pre-event period
        if self.pre_event_start <= tick_date < self.start_date:
            return True
        
        # Event period
        if self.is_active(tick_date):
            return True
        
        # Post-event period (15 days)
        days_since_end = (tick_date - self.end_date).days
        if 0 < days_since_end <= 15:
            return True
        
        return False

    def get_utility_bonus(self, tourist_segment: str, tick_date: datetime) -> float:
        """
        Calculate utility bonus for a tourist.

        Uses linear ramp-up before event, bell curve during event, and linear decline after.

        Args:
            tourist_segment: Tourist segment
            tick_date: Current simulation date

        Returns:
            Utility bonus (0.0 if not in pre-event, event, or post-event period)
        """
        # Get segment-specific appeal
        appeal = self.segment_appeal.get(tourist_segment, 0.5)

        # Pre-event linear ramp-up (0% → 30% of full magnitude)
        if self.pre_event_start <= tick_date < self.start_date:
            days_into_pre = (tick_date - self.pre_event_start).days
            ramp_factor = days_into_pre / self.pre_event_days  # Linear: 0.0 → 1.0
            return self.magnitude * 0.3 * appeal * ramp_factor

        # During event: bell curve distribution
        if self.is_active(tick_date):
            days_from_peak = (tick_date - self.peak_date).days
            sigma = self.duration_days / 4  # Spread parameter

            # Bell curve: exp(-0.5 * (x/σ)²)
            curve_factor = math.exp(-0.5 * (days_from_peak / sigma) ** 2)

            # Final bonus
            bonus = self.magnitude * appeal * curve_factor
            return bonus

        # Post-event linear decline (20% → 0% over 15 days)
        days_since_end = (tick_date - self.end_date).days
        if 0 < days_since_end <= 15:
            decline_factor = 1.0 - (days_since_end / 15)  # Linear decline
            return self.magnitude * 0.2 * appeal * decline_factor

        return 0.0

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "name": self.name,
            "country_code": self.country_code,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "magnitude": self.magnitude,
            "segment_appeal": self.segment_appeal,
            "expected_footfall": self.expected_footfall,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlannedEvent":
        """Deserialize event from dictionary."""
        return cls(
            name=data["name"],
            country_code=data["country_code"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            magnitude=data.get("magnitude", 0.5),
            segment_appeal=data.get("segment_appeal"),
            expected_footfall=data.get("expected_footfall", 100000),
        )


class PlannedEventManager:
    """
    Manages collection of planned events.
    """

    def __init__(self):
        """Initialize event manager."""
        self.events: List[PlannedEvent] = []

    def add_event(self, event: PlannedEvent):
        """
        Add event to manager.

        Args:
            event: PlannedEvent object
        """
        self.events.append(event)

    def get_active_events(
        self, tick_date: datetime, country_code: Optional[str] = None
    ) -> List[PlannedEvent]:
        """
        Get events active on given date (during event period only).

        Args:
            tick_date: Current simulation date
            country_code: Optional filter by country

        Returns:
            List of active PlannedEvent objects (event period only)
        """
        active = [e for e in self.events if e.is_active(tick_date)]

        if country_code:
            active = [e for e in active if e.country_code == country_code]

        return active

    def get_events_with_utility_bonus(
        self, tick_date: datetime, country_code: Optional[str] = None
    ) -> List[PlannedEvent]:
        """
        Get events providing utility bonus on given date.

        Includes pre-event ramp-up and post-event decline periods.

        Args:
            tick_date: Current simulation date
            country_code: Optional filter by country

        Returns:
            List of PlannedEvent objects with non-zero utility bonus
        """
        active = [e for e in self.events if e.has_utility_bonus(tick_date)]

        if country_code:
            active = [e for e in active if e.country_code == country_code]

        return active

    def get_utility_bonus(
        self, country_code: str, tourist_segment: str, tick_date: datetime
    ) -> float:
        """
        Get total utility bonus for a destination.

        Includes pre-event ramp-up and post-event decline periods.

        Args:
            country_code: Destination country code
            tourist_segment: Tourist segment
            tick_date: Current simulation date

        Returns:
            Total utility bonus from all events with non-zero bonus
        """
        # Use get_events_with_utility_bonus to include pre/post-event periods
        active_events = self.get_events_with_utility_bonus(tick_date, country_code)

        total_bonus = sum(
            e.get_utility_bonus(tourist_segment, tick_date) for e in active_events
        )

        return min(1.0, total_bonus)  # Cap at 1.0

    def get_expected_footfall(self, tick_date: datetime) -> Dict[str, int]:
        """
        Get expected additional footfall by country.

        Args:
            tick_date: Current simulation date

        Returns:
            Dict of country_code → expected additional visitors
        """
        footfall = {}

        for event in self.events:
            if event.is_active(tick_date):
                # Distribute footfall over event duration
                daily_footfall = event.expected_footfall / event.duration_days
                footfall[event.country_code] = (
                    footfall.get(event.country_code, 0) + daily_footfall
                )

        return footfall

    def to_list(self) -> List[dict]:
        """Serialize all events to list."""
        return [e.to_dict() for e in self.events]

    @classmethod
    def from_list(cls, events_data: List[dict]) -> "PlannedEventManager":
        """Deserialize events from list."""
        manager = cls()
        for data in events_data:
            manager.add_event(PlannedEvent.from_dict(data))
        return manager


# Example: FIFA World Cup 2026
def create_fifa_world_cup_2026() -> PlannedEvent:
    """Create FIFA World Cup 2026 event (USA)."""
    return PlannedEvent(
        name="FIFA World Cup 2026",
        country_code="USA",  # Use ISO3 code to match destination data
        start_date=datetime(2026, 6, 1),
        end_date=datetime(2026, 7, 15),
        magnitude=0.8,
        segment_appeal={
            "budget": 0.6,
            "luxury": 0.8,
            "adventure": 0.5,
            "family": 0.9,
        },
        expected_footfall=1000000,
        pre_event_days=45,  # Start ramp-up from April 17
    )


# Example: Olympics 2028
def create_olympics_2028() -> PlannedEvent:
    """Create LA Olympics 2028 event."""
    return PlannedEvent(
        name="LA Olympics 2028",
        country_code="US",
        start_date=datetime(2028, 7, 14),
        end_date=datetime(2028, 7, 30),
        magnitude=0.9,
        segment_appeal={
            "budget": 0.5,
            "luxury": 0.9,
            "adventure": 0.6,
            "family": 0.8,
        },
        expected_footfall=1500000,
    )
