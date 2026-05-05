"""
Main simulation class orchestrating agents, destinations, and dynamics.
"""

import logging
import random
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

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

        # Use relative path from this file (works on local and Streamlit Cloud)
        project_root = Path(__file__).parent.parent
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

        # Load population data
        from simulation.data.loaders import load_population_data
        population_data = load_population_data(project_root / "data" / "derived")

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

            # Get population data
            population = population_data.get(iso3_code, 0)

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
                population=population,
            )
            self.destinations[iso3_code] = dest

    def _create_agents(self):
        """Create tourist agents with segment distribution."""
        agent_count = self.config["agent_count"]
        shares = self.config["segment_shares"]

        # Load country code mapping (numeric M49 → ISO3)
        import csv
        from pathlib import Path
        numeric_to_iso3 = {}
        # Project root is 2 levels up from simulation.py
        project_root = Path(__file__).parent.parent
        mapping_file = project_root / "data" / "derived" / "country_code_mapping.csv"
        if mapping_file.exists():
            with open(mapping_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    numeric_to_iso3[row["country_code"]] = row["Country Code"]
        
        # Create mappings for country code/name conversion
        code_to_name = {c["code"]: c["name"] for c in self.countries_data}
        name_to_code = {c["name"]: c["code"] for c in self.countries_data}
        
        # Sample home countries from country data
        country_codes = [c["code"] for c in self.countries_data]

        agent_id = 0
        for segment, share in shares.items():
            count = int(agent_count * share)
            for _ in range(count):
                home_numeric = random.choice(country_codes)
                home_name = code_to_name[home_numeric]
                home_iso3 = numeric_to_iso3.get(home_numeric, home_numeric)  # Convert to ISO3 for lookups
                
                self.agents.append(
                    Tourist(
                        agent_id=f"T-{agent_id:05d}", 
                        segment=segment, 
                        home_country=home_name,  # Store country name for display
                        home_country_code=home_iso3  # Store ISO3 code for distance/visa lookups (matches destinations keys)
                    )
                )
                agent_id += 1
        
        # Store name-to-code mapping for use in other modules
        self.name_to_code = name_to_code

    def _select_sampled_agents(self):
        """Select sampled agents for trajectory tracking (stratified by segment)."""
        from collections import defaultdict

        # Get sample size from config (default 100)
        sample_size = getattr(self, 'config', {}).get('sampled_agents', 100)
        
        # Stratified sampling: equal representation from each segment
        by_segment = defaultdict(list)

        for agent in self.agents:
            by_segment[agent.segment].append(agent.agent_id)

        sampled = []
        per_segment = sample_size // len(by_segment)  # Divide equally among 4 segments
        
        for segment, ids in by_segment.items():
            sampled.extend(random.sample(ids, min(per_segment, len(ids))))

        self.sampled_agent_ids = set(sampled)

    def _get_top_destinations(self, n: int = 50, origin_code: str = None) -> List[Destination]:
        """
        Get top N destinations with origin-aware consideration set.
        
        Mix of global popular destinations + nearby regional options.

        Args:
            n: Number of destinations
            origin_code: Origin country code (optional, for regional bias)

        Returns:
            List of top Destination objects
        """
        if not origin_code:
            # Fallback to global top N
            sorted_dests = sorted(
                self.destinations.values(), key=lambda d: d.base_capacity, reverse=True
            )
            return sorted_dests[:n]
        
        # Build origin-aware choice set:
        # - 30% from global top destinations (15 destinations)
        # - 70% from regional/nearby destinations (35 destinations)
        
        # Global top destinations (smaller set)
        global_top = sorted(
            self.destinations.values(), key=lambda d: d.base_capacity, reverse=True
        )[:int(n * 0.3)]
        global_top_codes = {d.country_code for d in global_top}
        
        # Regional/nearby destinations (sorted by distance from origin)
        origin_dest = self.destinations.get(origin_code)
        if not origin_dest:
            return global_top
        
        # Calculate distances and sort
        regional_candidates = []
        for code, dest in self.destinations.items():
            if code in global_top_codes or code == origin_code:
                continue  # Skip already included
            
            distance = self.distance_matrix.get((origin_code, code), float('inf'))
            regional_candidates.append((distance, dest))
        
        # Sort by distance (nearest first) and take top regional
        regional_candidates.sort(key=lambda x: x[0])
        regional_top = [dest for _, dest in regional_candidates[:int(n * 0.7)]]
        
        # Combine and return
        choice_set = global_top + regional_top
        return choice_set

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

        # Diagnostic logging every 100 ticks
        if self.tick % 100 == 0 and self.tick > 0:
            logger.info(f"=== Tick {self.tick} Diagnostic ===")

            # Top 5 destinations by visitors
            top_5 = sorted(
                self.destinations.items(),
                key=lambda x: x[1].get_current_visitors(),
                reverse=True,
            )[:5]

            for code, dest in top_5:
                logger.info(
                    f"{code}: {dest.get_current_visitors()} visitors, "
                    f"{dest.get_crowding_ratio() * 100:.1f}% util, "
                    f"TFI={dest.tfi:.2f}"
                )

            # Check for anomalies
            for code, dest in self.destinations.items():
                if dest.get_crowding_ratio() > 2.0:
                    logger.warning(
                        f"{code}: CRITICAL - {dest.get_crowding_ratio() * 100:.0f}% capacity!"
                    )

                if dest.tfi < 0.50:
                    logger.warning(
                        f"{code}: LOW TFI - {dest.tfi:.2f} (policy response active)"
                    )

        # 2. Process agents (each gets origin-aware choice set)
        for agent in self.agents:
            if agent.state == "HOME":
                # Check if agent should start trip
                seasonal_mod = (
                    1.0  # Will use destination-specific in full implementation
                )
                event_mod = 1.0

                if agent.should_start_trip(current_month, seasonal_mod, event_mod):
                    # Get origin-aware choice set (60% global top + 40% regional)
                    agent_choice_set = self._get_top_destinations(
                        self.config["choice_set_size"],
                        agent.home_country_code
                    )
                    
                    # Choose destination (enters CHOOSING state for 10-day planning)
                    dest_code = agent.choose_destination(
                        agent_choice_set,
                        self.distance_matrix,
                        visa_lookup_func=self._get_visa_friction,
                        event_bonus_func=self._get_event_bonus,
                        tick=self.tick,
                        capture_decision_data=True,
                    )

            elif agent.state == "CHOOSING":
                # Count down planning days
                agent.step()
                
                # Check if planning complete and ready to travel
                if agent.ready_to_travel():
                    dest_code = agent.get_chosen_destination()
                    
                    if dest_code and dest_code in self.destinations:
                        # Get distance (use country code for lookup)
                        distance = get_distance(
                            agent.home_country_code, dest_code, self.distance_matrix
                        )

                        # Check shock impact (Phase 2)
                        risk_mult = self.unplanned_events.get_risk_multiplier(
                            dest_code, agent.segment, self.current_date
                        )

                        # Shock reduces probability of travel
                        # risk_mult=1.0 → 100% travel, risk_mult=2.0 → 50% travel, risk_mult=3.0 → 33% travel
                        travel_probability = 1.0 / risk_mult
                        
                        if random.random() < travel_probability:
                            # Begin trip
                            agent.travel_to(dest_code, self.tick, distance)

                            # Record arrival at destination (may be rejected if over capacity)
                            accommodated = self.destinations[dest_code].add_arrival(1)
                            
                            # Only record trip if tourist was actually accommodated
                            if accommodated > 0:
                                # Capture decision data before clearing (for sampled agents)
                                decision_data = None
                                if agent.agent_id in self.sampled_agent_ids and hasattr(agent, 'last_decision'):
                                    decision_data = agent.last_decision
                                
                                # Record trip for data collection (use country name for origin)
                                self.data_collector.record_trip(
                                    agent,
                                    agent.home_country_code,  # Use code for data consistency
                                    dest_code,
                                    self.tick,
                                    self.tick,  # Will be updated on departure
                                    decision_data=decision_data,  # Store decision breakdown
                                )
                            else:
                                # Tourist couldn't find accommodation - return home
                                agent.return_home()
                        else:
                            # Tourist cancels trip due to elevated risk - return home
                            agent.return_home()

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
