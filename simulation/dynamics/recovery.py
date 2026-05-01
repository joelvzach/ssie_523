"""
Shock and recovery dynamics.
Implements hybrid recovery model (double-dip + S-curve).
"""

import math
from typing import Dict, Optional


class ShockRecoveryManager:
    """
    Manages shock injection and recovery dynamics.
    """

    # Recovery patterns by shock type
    RECOVERY_PATTERNS = {
        "pandemic": {
            "pattern": "hybrid",
            "double_dip_duration": 24,  # months
            "s_curve_midpoint": 30,  # months
            "s_curve_steepness": 0.15,
        },
        "natural_disaster": {
            "pattern": "linear",
            "duration_months": 6,
        },
        "terrorism": {
            "pattern": "exponential",
            "decay_rate": 0.1,
        },
        "economic_crisis": {
            "pattern": "s_curve",
            "midpoint_months": 18,
            "steepness": 0.1,
        },
    }

    def __init__(self):
        """Initialize shock recovery manager."""
        self.active_shocks: Dict[str, dict] = {}

    def inject_shock(
        self,
        shock_type: str,
        magnitude: float,
        start_tick: int,
        country_code: Optional[str] = None,
    ):
        """
        Inject a shock into the simulation.

        Args:
            shock_type: Type of shock ('pandemic', 'natural_disaster', etc.)
            magnitude: Shock strength (0.0-1.0)
            start_tick: Simulation tick when shock starts
            country_code: Optional country filter (None = global)
        """
        shock_id = f"{shock_type}_{start_tick}_{country_code or 'GLOBAL'}"

        self.active_shocks[shock_id] = {
            "type": shock_type,
            "magnitude": magnitude,
            "start_tick": start_tick,
            "country_code": country_code,
            "recovery_info": self.RECOVERY_PATTERNS.get(
                shock_type, {"pattern": "s_curve"}
            ),
        }

    def get_recovery_fraction(self, shock_id: str, current_tick: int) -> float:
        """
        Get recovery fraction for a shock.

        0.0 = full shock impact, 1.0 = fully recovered.

        Args:
            shock_id: Shock identifier
            current_tick: Current simulation tick

        Returns:
            Recovery fraction (0.0-1.0)
        """
        if shock_id not in self.active_shocks:
            return 1.0

        shock = self.active_shocks[shock_id]
        ticks_elapsed = current_tick - shock["start_tick"]
        months_elapsed = ticks_elapsed / 30.0

        pattern = shock["recovery_info"]["pattern"]

        if pattern == "hybrid":
            return self._hybrid_recovery(months_elapsed, shock)
        elif pattern == "linear":
            return self._linear_recovery(months_elapsed, shock)
        elif pattern == "exponential":
            return self._exponential_recovery(months_elapsed, shock)
        else:  # s_curve
            return self._s_curve_recovery(months_elapsed, shock)

    def _hybrid_recovery(self, months: float, shock: dict) -> float:
        """
        Hybrid recovery: double-dip (0-2 years) + S-curve (2+ years).

        Matches Škare et al. (2021) pandemic recovery pattern.
        """
        if months < 24:
            # Double-dip phase: initial recovery, then second decline
            if months < 6:
                # Initial sharp decline
                return 0.2 * (months / 6)
            elif months < 12:
                # Brief recovery
                return 0.2 + 0.15 * ((months - 6) / 6)
            else:
                # Second dip
                progress = (months - 12) / 12
                return max(0.15, 0.35 - 0.2 * progress)
        else:
            # S-curve recovery phase
            progress = (months - 24) / 24
            return 0.35 + 0.65 * self._sigmoid(progress)

    def _linear_recovery(self, months: float, shock: dict) -> float:
        """
        Linear recovery (natural disasters).

        Matches Rosselló et al. (2020) findings.
        """
        duration = shock["recovery_info"].get("duration_months", 6)
        return min(1.0, months / duration)

    def _exponential_recovery(self, months: float, shock: dict) -> float:
        """
        Exponential decay recovery (terrorism).
        """
        decay_rate = shock["recovery_info"].get("decay_rate", 0.1)
        return 1.0 - math.exp(-decay_rate * months)

    def _s_curve_recovery(self, months: float, shock: dict) -> float:
        """
        Standard S-curve recovery.
        """
        midpoint = shock["recovery_info"].get("midpoint_months", 18)
        steepness = shock["recovery_info"].get("steepness", 0.1)

        return 1.0 / (1 + math.exp(-steepness * (months - midpoint)))

    def _sigmoid(self, x: float) -> float:
        """Standard sigmoid function."""
        return 1.0 / (1 + math.exp(-10 * (x - 0.5)))

    def get_impact_multiplier(
        self, current_tick: int, country_code: Optional[str] = None
    ) -> float:
        """
        Get total impact multiplier for a country.

        Args:
            current_tick: Current simulation tick
            country_code: Country code (or None for global)

        Returns:
            Impact multiplier (0.0-1.0, lower = more impacted)
        """
        multiplier = 1.0

        for shock_id, shock in self.active_shocks.items():
            # Check if shock applies to this country
            if shock["country_code"] and shock["country_code"] != country_code:
                if shock["country_code"] != "GLOBAL":
                    continue

            # Get recovery fraction
            recovery = self.get_recovery_fraction(shock_id, current_tick)

            # Calculate remaining impact
            remaining_impact = shock["magnitude"] * (1.0 - recovery)

            # Apply multiplicatively
            multiplier *= 1.0 - remaining_impact

        return max(0.1, multiplier)  # Floor at 10%

    def is_recovery_complete(self, shock_id: str, current_tick: int) -> bool:
        """
        Check if shock recovery is complete.

        Args:
            shock_id: Shock identifier
            current_tick: Current simulation tick

        Returns:
            True if recovery is complete (>95%)
        """
        recovery = self.get_recovery_fraction(shock_id, current_tick)
        return recovery > 0.95

    def cleanup_completed_shocks(self, current_tick: int):
        """
        Remove completed shocks from active list.

        Args:
            current_tick: Current simulation tick
        """
        completed = [
            shock_id
            for shock_id in self.active_shocks
            if self.is_recovery_complete(shock_id, current_tick)
        ]

        for shock_id in completed:
            del self.active_shocks[shock_id]
