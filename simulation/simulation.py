"""
Main simulation class orchestrating agents, destinations, and dynamics.
"""

import random
from typing import Dict, List, Optional, Set
from datetime import datetime

from simulation.agents.tourist import Tourist
from simulation.destinations.destination import Destination
from simulation.mechanics.distance import precompute_distance_matrix, get_distance
from simulation.data_collection.collector import DataCollector
from simulation.events.planned_events import PlannedEventManager
from simulation.events.unplanned_events import UnplannedEventManager
from simulation.dynamics.recovery import ShockRecoveryManager
from simulation.data.tourism_gdp import TourismGDPManager


# Default configuration
DEFAULT_CONFIG = {
    "agent_count": 4000,
    "segment_shares": {
        "budget": 0.30,
        "luxury": 0.20,
        "adventure": 0.25,
        "family": 0.25,
    },
    "choice_set_size": 50,  # Top 50 countries by arrivals
    "start_date": "2026-01-01",
    "duration_days": 365,
    "seed": 42,
}


class Simulation:
    """
    Main simulation orchestrator.
    """

    def __init__(
        self,
        config: dict = None,
        countries_data: List[dict] = None,
        visa_lookup_func=None,
    ):
        """
        Initialize simulation.

        Args:
            config: Configuration dictionary (uses defaults if None)
            countries_data: List of country dicts with required fields
            visa_lookup_func: Visa restriction lookup function
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.visa_lookup_func = visa_lookup_func

        # Set random seed for reproducibility
        random.seed(self.config["seed"])

        # Initialize components
        self.countries_data = countries_data or []
        self.agents: List[Tourist] = []
        self.destinations: Dict[str, Destination] = {}
        self.distance_matrix = {}
        self.data_collector: Optional[DataCollector] = None

        # Simulation state
        self.tick = 0
        self.paused = False
        self.current_date: Optional[datetime] = None

        # Sampled agents for trajectory tracking (100 agents)
        self.sampled_agent_ids: Set[str] = set()

        # Events systems (Phase 2)
        self.planned_events = PlannedEventManager()
        self.unplanned_events = UnplannedEventManager()
        self.shock_recovery = ShockRecoveryManager()

        # Tourism GDP manager (for TFI dynamics modification)
        self.tourism_gdp_manager: Optional[TourismGDPManager] = None

    def initialize(self):
        """
        Initialize simulation components.
        Call this after construction to set up agents and destinations.
        """
        # Initialize tourism GDP manager (pre-computes tourism GDP % for all countries)
        self._initialize_tourism_gdp()

        # Create destinations
        self._create_destinations()

        # Pre-compute distance matrix
        if self.countries_data:
            self.distance_matrix = precompute_distance_matrix(self.countries_data)

        # Create agents
        self._create_agents()

        # Select sampled agents (100 for trajectory tracking)
        self._select_sampled_agents()

        # Initialize data collector
        self.data_collector = DataCollector(self.sampled_agent_ids)

        # Set start date
        self.current_date = datetime.strptime(self.config["start_date"], "%Y-%m-%d")

    def _initialize_tourism_gdp(self):
        """Initialize tourism GDP manager with pre-computed data."""
        self.tourism_gdp_manager = TourismGDPManager(target_year=2019)
        print(
            f"[Simulation] Tourism GDP manager initialized: {len(self.tourism_gdp_manager.tourism_gdp_data)} countries"
        )

    def _create_destinations(self):
        """Create destination objects from country data."""
        # Load numeric to ISO3 mapping
        from pathlib import Path
        import csv

        # Use hardcoded project root (ssie_523 directory)
        project_root = Path("/Users/joelvzach/Code/ssie_523")
        mapping_file = project_root / "data" / "derived" / "country_code_mapping.csv"
        numeric_to_iso3 = {}

        if mapping_file.exists():
            with open(mapping_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    numeric_code = row.get("country_code", "")
                    iso3_code = row.get("Country Code", "")
                    if numeric_code and iso3_code:
                        numeric_to_iso3[numeric_code] = iso3_code

        for country in self.countries_data:
            numeric_code = str(country["code"])
            iso3_code = numeric_to_iso3.get(numeric_code, numeric_code)

            # Get tourism GDP data if available (stored with ISO3 code)
            tourism_gdp_pct = 0.0
            dependency_category = "minimal_dependency"
            tfi_modifier = 1.0

            if (
                self.tourism_gdp_manager
                and iso3_code in self.tourism_gdp_manager.tourism_gdp_data
            ):
                gdp_info = self.tourism_gdp_manager.tourism_gdp_data[iso3_code]
                tourism_gdp_pct = gdp_info["tourism_gdp_pct"]
                dependency_category = gdp_info["dependency_category"]
                tfi_modifier = gdp_info["tfi_decline_modifier"]

            dest = Destination(
                country_code=iso3_code,  # Use ISO3 code for consistency
                country_name=country["name"],
                hotel_beds=country.get("hotel_beds", 10000),
                attractiveness=country.get("attractiveness", 3.5),
                cost_index=country.get("cost_index", 50.0),
                risk_score=country.get("risk_score", 0.2),
                latitude=country.get("lat", 0.0),
                longitude=country.get("lon", 0.0),
                tourism_gdp_pct=tourism_gdp_pct,
                dependency_category=dependency_category,
            )
            self.destinations[iso3_code] = dest

    def _create_agents(self):
        """Create tourist agents with segment distribution."""
        agent_count = self.config["agent_count"]
        shares = self.config["segment_shares"]

        # Sample home countries from country data
        country_codes = [c["code"] for c in self.countries_data]

        agent_id = 0
        for segment, share in shares.items():
            count = int(agent_count * share)
            for _ in range(count):
                home = random.choice(country_codes)
                self.agents.append(
                    Tourist(
                        agent_id=f"T-{agent_id:05d}", segment=segment, home_country=home
                    )
                )
                agent_id += 1

    def _select_sampled_agents(self):
        """Select 100 agents for trajectory tracking."""
        # Stratified sampling: 25 from each segment
        from collections import defaultdict

        by_segment = defaultdict(list)

        for agent in self.agents:
            by_segment[agent.segment].append(agent.agent_id)

        sampled = []
        for segment, ids in by_segment.items():
            sampled.extend(random.sample(ids, min(25, len(ids))))

        self.sampled_agent_ids = set(sampled)

    def _get_top_destinations(self, n: int = 50) -> List[Destination]:
        """
        Get top N destinations by capacity (proxy for popularity).

        Args:
            n: Number of destinations

        Returns:
            List of top Destination objects
        """
        # Sort by base_capacity (proxy for 2019 arrivals)
        sorted_dests = sorted(
            self.destinations.values(), key=lambda d: d.base_capacity, reverse=True
        )
        return sorted_dests[:n]

    def _get_event_bonus(self, destination, tourist, tick: int) -> float:
        """
        Get utility bonus from planned events.

        Args:
            destination: Destination object
            tourist: Tourist agent
            tick: Current tick

        Returns:
            Event bonus (0.0 if no active events)
        """
        return self.planned_events.get_utility_bonus(
            destination.country_code, tourist.segment, self.current_date
        )

    def _get_visa_friction(self, dest_code: str, origin_code: str) -> float:
        """
        Get visa friction between origin and destination.

        Args:
            dest_code: Destination country code
            origin_code: Origin country code

        Returns:
            Visa friction (0.0-1.0)
        """
        if self.visa_lookup_func:
            return self.visa_lookup_func(dest_code, origin_code)
        return 0.0

    def step(self):
        """
        Advance simulation by one tick (1 day).
        """
        if self.paused:
            return

        # Update current date
        from datetime import timedelta

        self.current_date += timedelta(days=1)
        current_month = self.current_date.month

        # 1. Update destinations (TFI, capacity)
        for dest in self.destinations.values():
            dest.update(self.tick)

        # 2. Get choice set (top 50 destinations)
        choice_set = self._get_top_destinations(self.config["choice_set_size"])

        # 3. Process agents
        for agent in self.agents:
            if agent.state == "HOME":
                # Check if agent should start trip
                seasonal_mod = (
                    1.0  # Will use destination-specific in full implementation
                )
                event_mod = 1.0

                if agent.should_start_trip(current_month, seasonal_mod, event_mod):
                    # Choose destination
                    dest_code = agent.choose_destination(
                        choice_set,
                        self.distance_matrix,
                        visa_lookup_func=self._get_visa_friction,
                        event_bonus_func=self._get_event_bonus,
                        tick=self.tick,
                    )

                    if dest_code and dest_code in self.destinations:
                        # Get distance
                        distance = get_distance(
                            agent.home_country, dest_code, self.distance_matrix
                        )

                        # Check shock impact (Phase 2)
                        risk_mult = self.unplanned_events.get_risk_multiplier(
                            dest_code, agent.segment, self.current_date
                        )

                        # Shock reduces probability of travel
                        if random.random() < (1.0 / risk_mult):
                            # Begin trip
                            agent.travel_to(dest_code, self.tick, distance)

                            # Record arrival at destination
                            self.destinations[dest_code].add_arrival(1)

                            # Record trip for data collection
                            self.data_collector.record_trip(
                                agent,
                                agent.home_country,
                                dest_code,
                                self.tick,
                                self.tick,  # Will be updated on departure
                            )

            elif agent.state == "TRAVELING":
                # Advance trip
                agent.step()

        # 4. Collect data
        self.data_collector.record(self.tick, self.agents, self.destinations)

        # 5. Increment tick
        self.tick += 1

    def run(self, steps: int = None):
        """
        Run simulation for specified number of steps.

        Args:
            steps: Number of ticks to run (uses config duration if None)
        """
        if steps is None:
            steps = self.config["duration_days"]

        for _ in range(steps):
            self.step()

    def get_state(self) -> dict:
        """
        Get current simulation state.

        Returns:
            Dictionary with simulation state
        """
        return {
            "tick": self.tick,
            "current_date": self.current_date.isoformat()
            if self.current_date
            else None,
            "paused": self.paused,
            "agent_count": len(self.agents),
            "destination_count": len(self.destinations),
            "data_summary": self.data_collector.get_summary()
            if self.data_collector
            else {},
        }

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused

    def set_speed(self, speed_multiplier: float):
        """
        Set simulation speed multiplier.

        Args:
            speed_multiplier: 0.5, 1.0, 2.0, or 4.0
        """
        # Placeholder: speed control will be implemented in dashboard
        pass
