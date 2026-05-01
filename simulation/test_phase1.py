#!/usr/bin/env python3
"""
Test runner for Phase 1 simulation.
Verifies core mechanics work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import from simulation package
from simulation.simulation import Simulation
from simulation.data.loaders import load_country_data
from simulation.validation.baseline import run_validation_tests


def test_basic_simulation():
    """
    Run basic simulation test with placeholder countries.
    """
    print("=" * 60)
    print("Phase 1 Simulation Test")
    print("=" * 60)

    # Load country data
    print("\n1. Loading country data...")
    countries = load_country_data()
    print(f"   Loaded {len(countries)} countries")

    # Create simulation
    print("\n2. Creating simulation...")
    config = {
        "agent_count": 4000,
        "segment_shares": {
            "budget": 0.30,
            "luxury": 0.20,
            "adventure": 0.25,
            "family": 0.25,
        },
        "choice_set_size": min(50, len(countries)),
        "start_date": "2026-01-01",
        "duration_days": 30,  # Short test run
        "seed": 42,
    }

    sim = Simulation(config=config, countries_data=countries)
    sim.initialize()

    print(f"   Created {len(sim.agents)} agents")
    print(f"   Created {len(sim.destinations)} destinations")
    print(f"   Selected {len(sim.sampled_agent_ids)} sampled agents")

    # Run simulation
    print("\n3. Running simulation (30 days)...")
    sim.run(30)

    # Get results
    print("\n4. Results:")
    state = sim.get_state()
    print(f"   Final tick: {state['tick']}")
    print(f"   Current date: {state['current_date']}")
    print(f"   Total trips recorded: {state['data_summary']['total_trips_recorded']}")
    print(f"   Active travelers (final): {state['data_summary']['active_travelers']}")

    # Show some destination stats
    print("\n5. Top 5 destinations by average visitors:")
    dest_stats = []
    for code, dest in sim.destinations.items():
        visitors = sim.data_collector.dest_visitors[code]
        if visitors:
            avg_visitors = sum(visitors) / len(visitors)
            dest_stats.append((code, dest.country_name, avg_visitors))

    dest_stats.sort(key=lambda x: x[2], reverse=True)
    for code, name, avg in dest_stats[:5]:
        print(f"   {name} ({code}): {avg:.1f} avg visitors")

    # Run validation tests
    print("\n6. Running validation tests...")
    # Reset and run full validation
    sim2 = Simulation(
        config={**config, "duration_days": 365 * 10}, countries_data=countries
    )
    sim2.initialize()
    run_validation_tests(sim2)

    print("\n✅ Phase 1 test complete!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_basic_simulation()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
