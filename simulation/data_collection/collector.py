"""
Data collection for simulation metrics.
Tracks aggregate, segment, destination, and sampled agent data.
"""

from typing import Dict, List, Set
from collections import defaultdict


class DataCollector:
    """
    Collects and stores simulation metrics at various aggregation levels.
    """

    def __init__(self, sampled_agent_ids: Set[str] = None):
        """
        Initialize data collector.

        Args:
            sampled_agent_ids: Set of 100 agent IDs to track individually
        """
        self.sampled_agent_ids = sampled_agent_ids or set()

        # Aggregate metrics (every tick)
        self.global_arrivals: List[int] = []
        self.global_active: List[int] = []

        # Segment-level metrics (every tick)
        self.segment_arrivals: Dict[str, List[int]] = {
            "budget": [],
            "luxury": [],
            "adventure": [],
            "family": [],
        }
        self.segment_avg_stay: Dict[str, List[float]] = {
            "budget": [],
            "luxury": [],
            "adventure": [],
            "family": [],
        }

        # Destination-level metrics (every tick)
        self.dest_visitors: Dict[str, List[int]] = defaultdict(list)
        self.dest_capacity_util: Dict[str, List[float]] = defaultdict(list)
        self.dest_tfi: Dict[str, List[float]] = defaultdict(list)

        # Sampled agent trajectories
        self.agent_trajectories: Dict[str, List[tuple]] = defaultdict(list)

        # Trip records (all trips)
        self.trip_records: List[dict] = []

        # Current tick
        self.current_tick = 0

    def record(self, tick: int, agents: list, destinations: dict):
        """
        Record metrics for current tick.

        Args:
            tick: Current simulation tick
            agents: List of Tourist agents
            destinations: Dict of country_code → Destination
        """
        self.current_tick = tick

        # Count arrivals this tick (agents in CHOOSING state)
        arrivals_by_segment = defaultdict(int)
        active_travelers = 0

        for agent in agents:
            if agent.state == "TRAVELING":
                active_travelers += 1
                arrivals_by_segment[agent.segment] += 1

                # Track sampled agents
                if agent.agent_id in self.sampled_agent_ids:
                    self.agent_trajectories[agent.agent_id].append(
                        (tick, agent.current_destination)
                    )

        # Record aggregate metrics
        total_arrivals = sum(arrivals_by_segment.values())
        self.global_arrivals.append(total_arrivals)
        self.global_active.append(active_travelers)

        # Record segment metrics
        for segment in ["budget", "luxury", "adventure", "family"]:
            self.segment_arrivals[segment].append(arrivals_by_segment[segment])

        # Record destination metrics
        for code, dest in destinations.items():
            self.dest_visitors[code].append(dest.get_current_visitors())
            self.dest_capacity_util[code].append(dest.get_crowding_ratio())
            self.dest_tfi[code].append(dest.tfi)

    def record_trip(
        self,
        agent,
        origin: str,
        destination: str,
        arrival_tick: int,
        departure_tick: int = None,
    ):
        """
        Record trip (can be updated later with departure tick).

        Args:
            agent: Tourist agent
            origin: Origin country code
            destination: Destination country code
            arrival_tick: Arrival tick
            departure_tick: Departure tick (None if still traveling)
        """
        trip_record = {
            "agent_id": agent.agent_id,
            "segment": agent.segment,
            "origin": origin,
            "destination": destination,
            "arrival_tick": arrival_tick,
            "departure_tick": departure_tick,
            "duration": (departure_tick - arrival_tick) if departure_tick else None,
        }
        self.trip_records.append(trip_record)

        # Store reference for updating later
        agent._current_trip_record = trip_record

    def get_summary(self) -> dict:
        """
        Get summary statistics for current state.

        Returns:
            Dictionary with key metrics
        """
        return {
            "tick": self.current_tick,
            "total_arrivals_this_tick": self.global_arrivals[-1]
            if self.global_arrivals
            else 0,
            "active_travelers": self.global_active[-1] if self.global_active else 0,
            "total_trips_recorded": len(self.trip_records),
            "sampled_agents": len(self.sampled_agent_ids),
        }

    def get_destination_summary(self, country_code: str) -> dict:
        """
        Get summary for specific destination.

        Args:
            country_code: Destination country code

        Returns:
            Dictionary with destination metrics
        """
        if country_code not in self.dest_visitors:
            return {}

        visitors = self.dest_visitors[country_code]
        capacity_util = self.dest_capacity_util[country_code]
        tfi = self.dest_tfi[country_code]

        return {
            "country_code": country_code,
            "avg_visitors": sum(visitors) / len(visitors) if visitors else 0,
            "max_visitors": max(visitors) if visitors else 0,
            "avg_capacity_util": sum(capacity_util) / len(capacity_util)
            if capacity_util
            else 0,
            "current_tfi": tfi[-1] if tfi else 0,
            "tfi_trend": tfi[-1] - tfi[0] if len(tfi) > 1 else 0,
        }

    def export_to_dict(self) -> dict:
        """
        Export all collected data to dictionary.

        Returns:
            Dictionary with all metrics
        """
        return {
            "aggregate": {
                "global_arrivals": self.global_arrivals,
                "global_active": self.global_active,
            },
            "segment": {
                "arrivals": dict(self.segment_arrivals),
                "avg_stay": dict(self.segment_avg_stay),
            },
            "destinations": {
                "visitors": dict(self.dest_visitors),
                "capacity_util": dict(self.dest_capacity_util),
                "tfi": dict(self.dest_tfi),
            },
            "sampled_agents": dict(self.agent_trajectories),
            "trip_records": self.trip_records,
        }
