"""
Unplanned events system for shocks and crises.
Examples: Natural disasters, terrorism, epidemics, conflicts.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import random


class UnplannedEvent:
    """
    An unplanned shock event that negatively impacts tourism.
    """

    # Event types with typical characteristics
    EVENT_TYPES = {
        "disaster": {
            "name": "Natural Disaster",
            "typical_duration": 6,  # months
            "recovery_pattern": "linear",
        },
        "epidemic": {
            "name": "Epidemic/Pandemic",
            "typical_duration": 12,
            "recovery_pattern": "hybrid",  # Double-dip + S-curve
        },
        "terrorism": {
            "name": "Terrorist Attack",
            "typical_duration": 3,
            "recovery_pattern": "exponential",
        },
        "conflict": {
            "name": "Armed Conflict",
            "typical_duration": "variable",
            "recovery_pattern": "s_curve",
        },
    }

    # Segment-specific impact multipliers
    SEGMENT_IMPACT = {
        "budget": 0.5,  # Less affected (cost-conscious, flexible)
        "luxury": 0.8,  # Highly affected (safety-conscious)
        "adventure": 0.3,  # Least affected (risk-tolerant)
        "family": 0.9,  # Most affected (child safety)
    }

    def __init__(
        self,
        name: str,
        country_code: str,
        start_date: datetime,
        event_type: str,
        severity: float = 0.5,
        duration_months: int = 6,
    ):
        """
        Initialize unplanned event.

        Args:
            name: Event name (e.g., "Japan Earthquake 2026")
            country_code: Affected country code
            start_date: Event start date
            event_type: 'disaster', 'epidemic', 'terrorism', or 'conflict'
            severity: Impact strength (0.0-1.0)
            duration_months: Expected duration in months
        """
        self.name = name
        self.country_code = country_code
        self.start_date = start_date
        self.event_type = event_type
        self.severity = severity
        self.duration_months = duration_months

        # Calculate end date
        self.end_date = start_date + timedelta(days=duration_months * 30)

        # Get event type characteristics
        type_info = self.EVENT_TYPES.get(event_type, {})
        self.recovery_pattern = type_info.get("recovery_pattern", "s_curve")

    def is_active(self, tick_date: datetime) -> bool:
        """
        Check if event is active on given date.

        Args:
            tick_date: Current simulation date

        Returns:
            True if event is active
        """
        # Events have lingering effects even after "end"
        # Use 2x duration for full recovery
        full_recovery = self.start_date + timedelta(days=self.duration_months * 30 * 2)
        return self.start_date <= tick_date <= full_recovery

    def get_risk_multiplier(self, tourist_segment: str, tick_date: datetime) -> float:
        """
        Calculate risk multiplier for a tourist.

        Higher multiplier = higher perceived risk = lower utility.

        Args:
            tourist_segment: Tourist segment
            tick_date: Current simulation date

        Returns:
            Risk multiplier (1.0 = no effect, 2.0 = double risk)
        """
        if tick_date < self.start_date:
            return 1.0

        # Calculate time since event
        days_since = (tick_date - self.start_date).days
        total_duration = self.duration_months * 30

        if days_since > total_duration * 2:
            return 1.0  # Fully recovered

        # Get segment-specific base impact
        base_impact = self.severity * self.SEGMENT_IMPACT.get(tourist_segment, 0.5)

        # Apply decay based on recovery pattern
        if self.recovery_pattern == "linear":
            # Linear recovery (natural disasters)
            decay = max(0, 1.0 - days_since / total_duration)

        elif self.recovery_pattern == "exponential":
            # Exponential decay (terrorism)
            decay = math.exp(-days_since / (total_duration / 3))

        elif self.recovery_pattern == "hybrid":
            # Hybrid: double-dip then S-curve (pandemics)
            if days_since < total_duration / 2:
                # Double-dip phase
                decay = 1.0 - (days_since / total_duration) * 0.3
            else:
                # S-curve phase
                progress = (days_since - total_duration / 2) / (total_duration / 2)
                decay = 0.7 / (1 + math.exp(-10 * (progress - 0.5)))

        else:  # s_curve
            # Standard S-curve recovery
            progress = days_since / total_duration
            decay = 1.0 / (1 + math.exp(-10 * (progress - 0.5)))

        # Final multiplier
        multiplier = 1.0 + (base_impact * decay)

        return multiplier

    def get_arrivals_reduction(self, tick_date: datetime) -> float:
        """
        Get expected arrivals reduction fraction.

        Args:
            tick_date: Current simulation date

        Returns:
            Reduction fraction (0.0 = no effect, 0.7 = 70% reduction)
        """
        if tick_date < self.start_date:
            return 0.0

        days_since = (tick_date - self.start_date).days

        # Peak impact in first month
        if days_since < 30:
            return self.severity

        # Gradual recovery
        total_duration = self.duration_months * 30
        if days_since > total_duration:
            return self.severity * 0.3  # Lingering 30% effect

        # Linear interpolation
        progress = days_since / total_duration
        return self.severity * (1.0 - progress * 0.7)

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "name": self.name,
            "country_code": self.country_code,
            "start_date": self.start_date.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "duration_months": self.duration_months,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UnplannedEvent":
        """Deserialize event from dictionary."""
        return cls(
            name=data["name"],
            country_code=data["country_code"],
            start_date=datetime.fromisoformat(data["start_date"]),
            event_type=data["event_type"],
            severity=data.get("severity", 0.5),
            duration_months=data.get("duration_months", 6),
        )


class UnplannedEventManager:
    """
    Manages collection of unplanned events.
    """

    def __init__(self):
        """Initialize event manager."""
        self.events: list[UnplannedEvent] = []

    def add_event(self, event: UnplannedEvent):
        """
        Add event to manager.

        Args:
            event: UnplannedEvent object
        """
        self.events.append(event)

    def trigger_event(
        self,
        country_code: str,
        event_type: str,
        severity: float,
        current_date: datetime,
        name: Optional[str] = None,
    ) -> UnplannedEvent:
        """
        Trigger a new unplanned event.

        Args:
            country_code: Affected country
            event_type: Type of event
            severity: Severity (0.0-1.0)
            current_date: Current simulation date
            name: Optional event name

        Returns:
            Created UnplannedEvent
        """
        if name is None:
            type_name = UnplannedEvent.EVENT_TYPES.get(event_type, {}).get(
                "name", "Event"
            )
            name = f"{type_name} in {country_code}"

        # Get typical duration
        typical_duration = UnplannedEvent.EVENT_TYPES.get(event_type, {}).get(
            "typical_duration", 6
        )

        if isinstance(typical_duration, str):
            typical_duration = 6  # Default for 'variable'

        event = UnplannedEvent(
            name=name,
            country_code=country_code,
            start_date=current_date,
            event_type=event_type,
            severity=severity,
            duration_months=typical_duration,
        )

        self.add_event(event)
        return event

    def get_active_events(
        self, tick_date: datetime, country_code: Optional[str] = None
    ) -> list[UnplannedEvent]:
        """
        Get events active on given date.

        Args:
            tick_date: Current simulation date
            country_code: Optional filter by country

        Returns:
            List of active UnplannedEvent objects
        """
        active = [e for e in self.events if e.is_active(tick_date)]

        if country_code:
            active = [e for e in active if e.country_code == country_code]

        return active

    def get_risk_multiplier(
        self, country_code: str, tourist_segment: str, tick_date: datetime
    ) -> float:
        """
        Get total risk multiplier for a destination.

        Args:
            country_code: Destination country code
            tourist_segment: Tourist segment
            tick_date: Current simulation date

        Returns:
            Total risk multiplier (1.0 = normal, >1.0 = elevated risk)
        """
        active_events = self.get_active_events(tick_date, country_code)

        if not active_events:
            return 1.0

        # Combine multiplicatively (compounding effect)
        total_multiplier = 1.0
        for event in active_events:
            mult = event.get_risk_multiplier(tourist_segment, tick_date)
            total_multiplier *= mult

        # Cap at reasonable maximum
        return min(3.0, total_multiplier)

    def to_list(self) -> list[dict]:
        """Serialize all events to list."""
        return [e.to_dict() for e in self.events]

    @classmethod
    def from_list(cls, events_data: list[dict]) -> "UnplannedEventManager":
        """Deserialize events from list."""
        manager = cls()
        for data in events_data:
            manager.add_event(UnplannedEvent.from_dict(data))
        return manager


# Example: Pandemic shock
def create_pandemic_2020() -> UnplannedEvent:
    """Create COVID-19 pandemic shock (global)."""
    return UnplannedEvent(
        name="COVID-19 Pandemic",
        country_code="GLOBAL",  # Special code for global events
        start_date=datetime(2020, 1, 1),
        event_type="epidemic",
        severity=0.70,
        duration_months=24,
    )


# Example: Natural disaster
def create_earthquake_example() -> UnplannedEvent:
    """Create example earthquake event."""
    return UnplannedEvent(
        name="Major Earthquake",
        country_code="JP",
        start_date=datetime(2026, 5, 15),
        event_type="disaster",
        severity=0.6,
        duration_months=12,
    )
