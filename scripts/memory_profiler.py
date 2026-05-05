#!/usr/bin/env python3
"""
Memory Profiling Script for Global Tourism Simulation

Measures RAM consumption at different simulation stages to identify memory leaks.
Run this to establish baseline before applying fixes.
"""

import sys
import time
import tracemalloc
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.simulation import Simulation
from simulation.data.loaders import load_country_data


def get_memory_mb():
    """Get current memory usage in MB."""
    import psutil
    import os
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_tracemalloc_top(n=10):
    """Get top memory allocations from tracemalloc."""
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print(f"\n{'='*80}")
    print(f"TOP {n} MEMORY ALLOCATIONS:")
    print(f"{'='*80}")
    
    for index, stat in enumerate(top_stats[:n], 1):
        print(f"{index}. {stat}")
    
    return top_stats


def profile_data_collector(collector, tick):
    """Profile memory usage of data collector."""
    print(f"\n{'='*80}")
    print(f"DATA COLLECTOR METRICS AT TICK {tick}:")
    print(f"{'='*80}")
    
    # Count data points
    total_visitor_points = sum(len(v) for v in collector.dest_visitors.values())
    total_capacity_points = sum(len(c) for c in collector.dest_capacity_util.values())
    total_tfi_points = sum(len(t) for t in collector.dest_tfi.values())
    total_trajectory_points = sum(len(t) for t in collector.agent_trajectories.values())
    
    print(f"Destination metrics (177 countries × {tick} days):")
    print(f"  - Visitors:      {total_visitor_points:>10,} data points")
    print(f"  - Capacity Util: {total_capacity_points:>10,} data points")
    print(f"  - TFI:           {total_tfi_points:>10,} data points")
    print(f"Agent trajectories (100 sampled agents):")
    print(f"  - Trajectories:  {total_trajectory_points:>10,} data points")
    print(f"Trip records:")
    print(f"  - Total trips:   {len(collector.trip_records):>10,} records")
    
    # Estimate memory
    # Python int/float ≈ 28 bytes, dict overhead ≈ 240 bytes per dict
    # List overhead ≈ 56 bytes per list
    estimated_bytes = (
        (total_visitor_points + total_capacity_points + total_tfi_points) * 28 +  # Data
        total_trajectory_points * 56 +  # Tuples are larger
        len(collector.trip_records) * 240 +  # Dict records
        177 * 3 * 56  # List overhead for 177 countries × 3 metrics
    )
    
    estimated_mb = estimated_bytes / 1024 / 1024
    print(f"\nEstimated collector memory: ~{estimated_mb:.2f} MB")
    
    return {
        'tick': tick,
        'visitor_points': total_visitor_points,
        'capacity_points': total_capacity_points,
        'tfi_points': total_tfi_points,
        'trajectory_points': total_trajectory_points,
        'trip_records': len(collector.trip_records),
        'estimated_mb': estimated_mb
    }


def run_profiling(agent_count=40000, days=365):
    """Run simulation and profile memory at intervals."""
    
    print(f"\n{'='*80}")
    print(f"MEMORY PROFILING - GLOBAL TOURISM SIMULATION")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  - Agents: {agent_count:,}")
    print(f"  - Duration: {days} days")
    print(f"  - Start date: 2026-01-01")
    print(f"{'='*80}\n")
    
    # Start tracing
    tracemalloc.start()
    
    # Initial memory
    initial_mem = get_memory_mb()
    print(f"Initial memory (Python + data loading): {initial_mem:.2f} MB")
    
    # Load countries
    print("\nLoading country data...")
    countries = load_country_data()
    after_load_mem = get_memory_mb()
    print(f"After loading {len(countries)} countries: {after_load_mem:.2f} MB")
    print(f"  → Country data: {after_load_mem - initial_mem:.2f} MB")
    
    # Create simulation
    print("\nCreating simulation...")
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
        "duration_days": days,
        "seed": 42,
    }
    
    sim = Simulation(config=config, countries_data=countries)
    after_sim_mem = get_memory_mb()
    print(f"After simulation creation: {after_sim_mem:.2f} MB")
    print(f"  → Simulation objects: {after_sim_mem - after_load_mem:.2f} MB")
    
    # Initialize
    print("\nInitializing simulation...")
    sim.initialize()
    after_init_mem = get_memory_mb()
    print(f"After initialization: {after_init_mem:.2f} MB")
    print(f"  → Initialization: {after_init_mem - after_sim_mem:.2f} MB")
    
    # Profile data collector at start
    metrics_log = []
    metrics = profile_data_collector(sim.data_collector, 0)
    metrics['total_memory_mb'] = after_init_mem
    metrics_log.append(metrics)
    
    # Run simulation with profiling at intervals
    print(f"\n{'='*80}")
    print(f"RUNNING SIMULATION (profiling every {days//10} days)...")
    print(f"{'='*80}\n")
    
    interval = max(1, days // 10)  # Profile 10 times
    
    start_time = time.time()
    
    for day in range(1, days + 1):
        sim.step()
        
        # Profile at intervals
        if day % interval == 0 or day == days:
            current_mem = get_memory_mb()
            elapsed = time.time() - start_time
            ticks_per_sec = day / elapsed if elapsed > 0 else 0
            
            print(f"\n--- Day {day}/{days} ({day/interval*10:.0f}% complete) ---")
            print(f"Performance: {ticks_per_sec:.1f} ticks/sec")
            print(f"Total memory: {current_mem:.2f} MB")
            
            metrics = profile_data_collector(sim.data_collector, day)
            metrics['total_memory_mb'] = current_mem
            metrics['performance_ticks_per_sec'] = ticks_per_sec
            metrics_log.append(metrics)
    
    # Final tracemalloc report
    print(f"\n{'='*80}")
    print(f"FINAL MEMORY ANALYSIS")
    print(f"{'='*80}")
    
    get_tracemalloc_top(15)
    
    final_mem = get_memory_mb()
    total_elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total simulation time: {total_elapsed:.2f}s")
    print(f"Average speed: {days/total_elapsed:.1f} ticks/sec")
    print(f"Memory growth:")
    print(f"  - Initial: {initial_mem:.2f} MB")
    print(f"  - Final:   {final_mem:.2f} MB")
    print(f"  - Growth:  {final_mem - initial_mem:.2f} MB ({(final_mem/initial_mem - 1)*100:.1f}%)")
    print(f"  - Per day: {(final_mem - initial_mem)/days:.2f} MB/day")
    
    # Projection for longer runs
    if days == 365:
        projected_1year = final_mem
        projected_2year = initial_mem + (final_mem - initial_mem) * 2
        projected_5year = initial_mem + (final_mem - initial_mem) * 5
        print(f"\nProjection (if unbounded):")
        print(f"  - 1 year:  {projected_1year:.2f} MB")
        print(f"  - 2 years: {projected_2year:.2f} MB")
        print(f"  - 5 years: {projected_5year:.2f} MB ({projected_5year/1024:.2f} GB)")
    
    tracemalloc.stop()
    
    # Save metrics
    import json
    metrics_file = Path(__file__).parent / "memory_profile_results.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_log, f, indent=2)
    
    print(f"\nMetrics saved to: {metrics_file}")
    print(f"{'='*80}\n")
    
    return metrics_log


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Profile simulation memory usage")
    parser.add_argument("--agents", type=int, default=40000, 
                        help="Number of agents (default: 40,000)")
    parser.add_argument("--days", type=int, default=365,
                        help="Number of days to simulate (default: 365)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test: 10,000 agents for 30 days")
    
    args = parser.parse_args()
    
    if args.quick:
        args.agents = 10000
        args.days = 30
        print("Quick test mode: 10,000 agents × 30 days\n")
    
    run_profiling(args.agents, args.days)
