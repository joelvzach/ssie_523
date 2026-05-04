#!/usr/bin/env python3
"""
Debug script to reproduce the India missing from Top 10 bug.
"""

import sys
sys.path.insert(0, '/Users/joelvzach/Code/ssie_523')

from simulation.data.loaders import load_country_data, load_centroids
from simulation.simulation import Simulation
from pathlib import Path

print("=" * 80)
print("DEBUG: Testing choice mechanism for India selection bug")
print("=" * 80)

# Load data
countries = load_country_data()
centroids = load_centroids(Path('data/derived'))

print(f"✓ Loaded {len(countries)} countries")
print(f"✓ Loaded {len(centroids)} centroids")

# Check if India is in the data
india_in_countries = any(c['code'] == '356' or c['code'] == 'IND' for c in countries)
print(f"✓ India in countries data: {india_in_countries}")

# Create simulation
config = {
    "agent_count": 40000,
    "segment_shares": {
        "budget": 0.30,
        "luxury": 0.20,
        "adventure": 0.25,
        "family": 0.25,
    },
    "choice_set_size": 50,
    "start_date": "2026-01-01",
    "duration_days": 365,
    "seed": 42,
}

print(f"\n🔧 Creating simulation with {config['agent_count']:,} agents...")
sim = Simulation(config=config, countries_data=countries)
sim.initialize()

print(f"✓ Simulation initialized")
print(f"  - {len(sim.agents):,} agents")
print(f"  - {len(sim.destinations)} destinations")

# Check if India is in destinations
india_in_destinations = 'IND' in sim.destinations or '356' in sim.destinations
print(f"✓ India in destinations: {india_in_destinations}")

if 'IND' in sim.destinations:
    india_dest = sim.destinations['IND']
    print(f"  - Country: {india_dest.country_name}")
    print(f"  - Attractiveness: {india_dest.attractiveness}")
    print(f"  - Cost Index: {india_dest.cost_index}")
    print(f"  - Capacity: {india_dest.base_capacity}")

# Find agents that chose India
print("\n" + "=" * 80)
print("Running simulation to find agents that choose India...")
print("=" * 80)

agents_chose_india = []

for day in range(1, 31):  # Run 30 days
    sim.step()
    
    # Check agents in CHOOSING state
    for agent in sim.agents:
        if agent.state == "CHOOSING" and hasattr(agent, 'last_decision') and agent.last_decision:
            decision = agent.last_decision
            chosen = decision['chosen']
            
            if chosen == 'IND':
                agents_chose_india.append((agent.agent_id, day, decision))
                
                # Check if India is in top 10
                top_10_codes = [d['country_code'] for d in decision['destinations'][:10]]
                all_codes = [d['country_code'] for d in decision['destinations']]
                
                print(f"\n🎯 FOUND Agent {agent.agent_id} on Day {day}:")
                print(f"   Chosen: {chosen}")
                print(f"   India in Top 10: {'IND' in top_10_codes}")
                print(f"   India in All: {'IND' in all_codes}")
                print(f"   Total destinations: {len(decision['destinations'])}")
                print(f"   Top 10: {top_10_codes}")
                print(f"   All: {all_codes[:15]}{'...' if len(all_codes) > 15 else ''}")
                
                # Find India's position
                if 'IND' in all_codes:
                    india_pos = all_codes.index('IND')
                    india_prob = decision['destinations'][india_pos]['probability']
                    print(f"   India position: {india_pos + 1} (probability: {india_prob:.2%})")
                
                # Show top 10 table
                print(f"\n   Top 10 Table:")
                for i, dest in enumerate(decision['destinations'][:10]):
                    marker = "✅" if dest['country_code'] == chosen else "  "
                    print(f"   {marker} {i+1}. {dest['country_name']} ({dest['country_code']}): {dest['probability']:.2%}")
                
                if len(agents_chose_india) >= 3:
                    print("\n" + "=" * 80)
                    print("Found 3 agents - stopping test")
                    print("=" * 80)
                    sys.exit(0)

print(f"\nTotal agents that chose India: {len(agents_chose_india)}")
if len(agents_chose_india) == 0:
    print("No agents chose India in first 30 days - this might be expected with seed=42")
