#!/usr/bin/env python3
"""
Track agent T-36217 specifically to debug the India issue.
"""

import sys
sys.path.insert(0, '/Users/joelvzach/Code/ssie_523')

from simulation.data.loaders import load_country_data
from simulation.simulation import Simulation

print("=" * 80)
print("TRACKING AGENT T-36217")
print("=" * 80)

# Load data
countries = load_country_data()

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

print(f"Creating simulation with seed=42...")
sim = Simulation(config=config, countries_data=countries)
sim.initialize()

# Find agent T-36217
agent_36217 = next((a for a in sim.agents if a.agent_id == "T-36217"), None)

if not agent_36217:
    print("❌ Agent T-36217 NOT FOUND!")
    print(f"Available agents: {sim.agents[:5]}...")
    sys.exit(1)

print(f"✓ Found agent T-36217:")
print(f"  - Segment: {agent_36217.segment}")
print(f"  - Home: {agent_36217.home_country}")
print(f"  - Home code: {agent_36217.home_country_code}")

# Run simulation and track agent
print(f"\n{'='*80}")
print(f"RUNNING SIMULATION - Watching for T-36217 decisions")
print(f"{'='*80}\n")

for day in range(1, 31):  # Run 30 days
    sim.step()
    
    # Check if agent T-36217 made a decision
    if agent_36217.state == "CHOOSING" and hasattr(agent_36217, 'last_decision') and agent_36217.last_decision:
        decision = agent_36217.last_decision
        
        print(f"\n📊 DAY {day}: Agent T-36217 made a decision!")
        print(f"   State: {agent_36217.state}")
        print(f"   Chosen: {decision['chosen']}")
        
        # Check if chosen is in top 10
        top_10_codes = [d['country_code'] for d in decision['destinations'][:10]]
        all_codes = [d['country_code'] for d in decision['destinations']]
        
        chosen_pos = all_codes.index(decision['chosen']) if decision['chosen'] in all_codes else -1
        
        print(f"   Chosen position: #{chosen_pos + 1}")
        print(f"   Chosen in Top 10: {chosen_pos < 10}")
        
        print(f"\n   Top 10 Table:")
        for i, dest in enumerate(decision['destinations'][:10]):
            marker = "✅ CHOSEN" if dest['country_code'] == decision['chosen'] else ""
            print(f"   {i+1:2d}. {dest['country_name']:30s} ({dest['country_code']:3s}): {dest['probability']:5.2%} {marker}")
        
        if chosen_pos >= 10:
            print(f"\n   ⚠️  Chosen destination is at position {chosen_pos + 1} (outside top 10)")
            chosen_dest = decision['destinations'][chosen_pos]
            print(f"   Full details: {chosen_dest['country_name']} - {chosen_dest['probability']:.2%} probability")
        
        print(f"\n{'='*80}")
        
        # Stop after first decision
        break
    
    # Check agent state
    if day % 5 == 0:
        print(f"Day {day}: Agent state = {agent_36217.state}, days_until_next_trip = {agent_36217.days_until_next_trip}")

print(f"\nFinal state after 30 days: {agent_36217.state}")
if agent_36217.state == "TRAVELING":
    print(f"  Current destination: {agent_36217.current_destination}")
