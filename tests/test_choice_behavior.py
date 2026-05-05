"""
Test script to evaluate destination choice behavior with tuned parameters.
Runs silent simulation and analyzes destination selection patterns.
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation.data.loaders import load_country_data
from simulation.simulation import Simulation


def run_test(agent_count=40000, days=60, seed=42):
    """Run simulation and collect destination choice statistics."""
    
    print(f"\n{'='*60}")
    print(f"DESTINATION CHOICE ANALYSIS")
    print(f"{'='*60}")
    print(f"Agents: {agent_count:,}")
    print(f"Duration: {days} days")
    print(f"Seed: {seed}")
    print(f"{'='*60}\n")
    
    # Load data
    countries = load_country_data()
    
    # Configure simulation
    config = {
        "agent_count": agent_count,
        "segment_shares": {
            "budget": 0.30,
            "luxury": 0.20,
            "adventure": 0.25,
            "family": 0.25,
        },
        "choice_set_size": 50,
        "start_date": "2026-01-01",
        "duration_days": 365,
        "seed": seed,
        "sampled_agents": 100,
    }
    
    # Initialize simulation
    sim = Simulation(config=config, countries_data=countries)
    sim.initialize()
    
    # Load centroids for continent analysis
    from simulation.data.loaders import load_centroids
    centroids = load_centroids(project_root / "data" / "derived")
    
    # Build continent mapping (ISO3 format)
    continent_map = {}
    for code, data in centroids.items():
        continent_map[code] = data.get('region', 'Unknown')
    
    # Build numeric to ISO3 mapping for distance lookup
    import csv
    numeric_to_iso3 = {}
    iso3_to_numeric = {}
    mapping_file = project_root / "data" / "derived" / "country_code_mapping.csv"
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                numeric_code = row.get("country_code", "")
                iso3_code = row.get("Country Code", "")
                if numeric_code and iso3_code:
                    numeric_to_iso3[numeric_code] = iso3_code
                    iso3_to_numeric[iso3_code] = numeric_code
    
    # Track statistics
    trip_origins = []
    trip_destinations = []
    trip_distances = []
    trip_segments = []
    destination_choices = defaultdict(int)
    regional_vs_far = defaultdict(lambda: {'regional': 0, 'far': 0})  # {segment: {'regional': X, 'far': Y}}
    
    print(f"Running simulation...")
    
    # Run simulation
    for day in range(days):
        if day % 10 == 0:
            print(f"  Day {day+1}/{days}...")
        
        # Step simulation
        sim.step()
    
    # Collect trip data from data collector (more reliable than agent state)
    print(f"Collecting trip data from data collector...")
    
    # Debug: Check distance matrix keys
    print(f"Distance matrix size: {len(sim.distance_matrix)} entries")
    sample_keys = list(sim.distance_matrix.keys())[:5]
    print(f"Sample distance matrix keys: {sample_keys}")
    
    # Debug: Check trip record format
    if sim.data_collector.trip_records:
        sample_trip = sim.data_collector.trip_records[0]
        print(f"Sample trip record: {sample_trip}")
    
    zero_distances = 0
    
    for trip in sim.data_collector.trip_records:
        origin_iso3 = trip['origin']
        dest_iso3 = trip['destination']
        segment = trip['segment']
        
        # Convert ISO3 to numeric for distance matrix lookup
        origin_numeric = iso3_to_numeric.get(origin_iso3, origin_iso3)
        dest_numeric = iso3_to_numeric.get(dest_iso3, dest_iso3)
        
        # Lookup distance using numeric codes
        distance = sim.distance_matrix.get((origin_numeric, dest_numeric), None)
        if distance is None:
            # Try reverse direction
            distance = sim.distance_matrix.get((dest_numeric, origin_numeric), None)
        if distance is None:
            zero_distances += 1
            distance = 0
        
        trip_origins.append(origin_iso3)
        trip_destinations.append(dest_iso3)
        trip_distances.append(distance)
        trip_segments.append(segment)
        destination_choices[dest_iso3] += 1
        
        # Regional vs far (using continent)
        origin_continent = continent_map.get(origin_iso3, 'Unknown')
        dest_continent = continent_map.get(dest_iso3, 'Unknown')
        
        if origin_continent == dest_continent:
            regional_vs_far[segment]['regional'] += 1
        else:
            regional_vs_far[segment]['far'] += 1
    
    if zero_distances > 0:
        print(f"WARNING: {zero_distances} trips had zero distance (matrix lookup failed)")
    
    # Analyze results
    total_trips = len(trip_destinations)
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total trips recorded: {total_trips:,}")
    print(f"Unique destinations visited: {len(destination_choices)}")
    print()
    
    # Regional vs Far by segment
    print("REGIONAL vs LONG-DISTANCE TRAVEL by Segment:")
    print(f"{'Segment':<12} {'Regional':>10} {'Far':>10} {'% Regional':>12}")
    print(f"{'-'*44}")
    
    for segment in ['budget', 'luxury', 'adventure', 'family']:
        regional = regional_vs_far[segment]['regional']
        far = regional_vs_far[segment]['far']
        total = regional + far
        pct_regional = (regional / total * 100) if total > 0 else 0
        print(f"{segment.capitalize():<12} {regional:>10,} {far:>10,} {pct_regional:>11.1f}%")
    
    total_regional = sum(regional_vs_far[s]['regional'] for s in regional_vs_far)
    total_far = sum(regional_vs_far[s]['far'] for s in regional_vs_far)
    total_all = total_regional + total_far
    overall_pct = (total_regional / total_all * 100) if total_all > 0 else 0
    
    print(f"{'-'*44}")
    print(f"{'OVERALL':<12} {total_regional:>10,} {total_far:>10,} {overall_pct:>11.1f}%")
    print()
    
    # Top destinations
    print("TOP 20 DESTINATIONS by Arrivals:")
    sorted_dests = sorted(destination_choices.items(), key=lambda x: x[1], reverse=True)[:20]
    
    print(f"{'Rank':>4} {'Code':<6} {'Arrivals':>10} {'% of Total':>12}")
    print(f"{'-'*34}")
    
    for rank, (code, count) in enumerate(sorted_dests, 1):
        pct = (count / total_trips * 100) if total_trips > 0 else 0
        dest_name = sim.destinations.get(code)
        name_str = f"{dest_name.country_name if dest_name else code}"
        print(f"{rank:>4} {code:<6} {count:>10,} {pct:>11.2f}%  ({name_str})")
    
    print()
    
    # Distance statistics
    if trip_distances:
        import statistics
        avg_distance = statistics.mean(trip_distances)
        median_distance = statistics.median(trip_distances)
        min_distance = min(trip_distances)
        max_distance = max(trip_distances)
        
        print("DISTANCE STATISTICS:")
        print(f"  Average distance: {avg_distance:,.0f} km")
        print(f"  Median distance:  {median_distance:,.0f} km")
        print(f"  Min distance:     {min_distance:,.0f} km")
        print(f"  Max distance:     {max_distance:,.0f} km")
        print()
        
        # Distance distribution
        short_haul = sum(1 for d in trip_distances if d < 2000)  # <2000km
        medium_haul = sum(1 for d in trip_distances if 2000 <= d < 6000)  # 2000-6000km
        long_haul = sum(1 for d in trip_distances if d >= 6000)  # >6000km
        
        print("DISTANCE DISTRIBUTION:")
        print(f"  Short-haul (<2000km):    {short_haul:>10,} ({short_haul/total_trips*100:.1f}%)")
        print(f"  Medium-haul (2-6k km):   {medium_haul:>10,} ({medium_haul/total_trips*100:.1f}%)")
        print(f"  Long-haul (>6000km):     {long_haul:>10,} ({long_haul/total_trips*100:.1f}%)")
        print()
    
    # Power law analysis (top 10 vs rest)
    top_10_arrivals = sum(count for _, count in sorted_dests[:10])
    rest_arrivals = sum(count for _, count in sorted_dests[10:])
    
    print("CONCENTRATION METRICS:")
    print(f"  Top 10 destinations: {top_10_arrivals:>10,} trips ({top_10_arrivals/total_trips*100:.1f}%)")
    print(f"  Rest of destinations: {rest_arrivals:>10,} trips ({rest_arrivals/total_trips*100:.1f}%)")
    print()
    
    # Save detailed data
    output_file = project_root / "test_output" / f"choice_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['origin', 'destination', 'distance_km', 'segment', 'origin_continent', 'dest_continent'])
        
        for i in range(len(trip_origins)):
            origin_cont = continent_map.get(trip_origins[i], 'Unknown')
            dest_cont = continent_map.get(trip_destinations[i], 'Unknown')
            writer.writerow([
                trip_origins[i],
                trip_destinations[i],
                trip_distances[i],
                trip_segments[i],
                origin_cont,
                dest_cont
            ])
    
    print(f"Detailed trip data saved to: {output_file}")
    print(f"{'='*60}\n")
    
    # Return key metrics for comparison
    return {
        'total_trips': total_trips,
        'pct_regional': overall_pct,
        'avg_distance': avg_distance if trip_distances else 0,
        'top_10_share': top_10_arrivals / total_trips if total_trips > 0 else 0,
        'unique_destinations': len(destination_choices),
    }


if __name__ == "__main__":
    # Run test with default parameters
    metrics = run_test(agent_count=40000, days=60, seed=42)
    
    # Expected benchmarks for realistic tourism:
    # - Regional travel: 60-75% (within continent)
    # - Top 10 share: 40-60% (power law concentration)
    # - Average distance: 3000-5000 km (mix of short and long haul)
    
    print("\nBENCHMARK COMPARISON:")
    print(f"{'Metric':<25} {'Actual':>12} {'Target Range':>20} {'Status':>10}")
    print(f"{'-'*70}")
    
    # Regional travel
    regional_status = "✓" if 60 <= metrics['pct_regional'] <= 75 else "✗"
    print(f"Regional Travel %:        {metrics['pct_regional']:>11.1f}%  60-75%              {regional_status}")
    
    # Top 10 share
    top10_status = "✓" if 40 <= metrics['top_10_share'] * 100 <= 60 else "✗"
    print(f"Top 10 Share %:           {metrics['top_10_share']*100:>11.1f}%  40-60%              {top10_status}")
    
    # Average distance
    dist_status = "✓" if 3000 <= metrics['avg_distance'] <= 5000 else "✗"
    print(f"Average Distance (km):    {metrics['avg_distance']:>12,.0f}  3,000-5,000         {dist_status}")
    
    print()
