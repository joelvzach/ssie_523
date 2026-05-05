#!/usr/bin/env python3
"""
Phase 4 Validation Plots Generator

Generates 4 key validation plots:
1. Time series: Global arrivals over time
2. Gini coefficient: Arrival distribution inequality
3. Segment mix: Tourist segment distribution
4. TFI trajectories: TFI over time by dependency category

Usage:
    python scripts/generate_validation_plots.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
from datetime import datetime, timedelta

from simulation.simulation import Simulation
from simulation.data.loaders import load_country_data


def plot_time_series(data_collector, output_file: Path):
    """Plot 1: Global arrivals time series."""
    print("  [1/4] Generating time series plot...")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Get dates and arrivals
    start_date = datetime(2026, 1, 1)
    dates = [
        start_date + timedelta(days=i) for i in range(len(data_collector.global_active))
    ]

    # Plot active tourists
    ax.plot(
        dates,
        data_collector.global_active,
        "b-",
        linewidth=1.5,
        label="Active Tourists",
    )

    # Format
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x / 1000:.1f}K"))

    ax.set_xlabel("Date")
    ax.set_ylabel("Active Tourists")
    ax.set_title("Global Tourism Simulation: Active Tourists Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"    Saved: {output_file}")


def plot_gini_coefficient(data_collector, output_file: Path):
    """Plot 2: Gini coefficient evolution."""
    print("  [2/4] Generating Gini coefficient plot...")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Calculate Gini for each tick
    # dest_visitors is defaultdict(code -> list of visitor counts over time)
    gini_values = []
    num_ticks = len(data_collector.global_active)

    for tick in range(num_ticks):
        # Get visitor counts for all destinations at this tick
        values = []
        for code, history in data_collector.dest_visitors.items():
            if tick < len(history):
                values.append(history[tick])

        if len(values) > 1 and sum(values) > 0:
            # Calculate Gini coefficient
            sorted_values = sorted(values)
            n = len(sorted_values)
            gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (
                n * np.sum(sorted_values)
            ) - (n + 1) / n
            gini_values.append(gini)
        else:
            gini_values.append(0.0)

    # Plot
    ticks = range(len(gini_values))
    ax.plot(ticks, gini_values, "r-", linewidth=1.5)

    # Add target range
    ax.axhspan(0.60, 0.80, alpha=0.3, color="green", label="Target Range (0.60-0.80)")
    ax.axhline(
        y=np.mean(gini_values[-30:]),
        color="blue",
        linestyle="--",
        label=f"Final Avg: {np.mean(gini_values[-30:]):.3f}",
    )

    ax.set_xlabel("Simulation Day")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Arrival Distribution Inequality (Gini Coefficient)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"    Saved: {output_file}")


def plot_segment_mix(data_collector, output_file: Path):
    """Plot 3: Segment mix over time."""
    print("  [3/4] Generating segment mix plot...")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Get segment arrivals
    segments = ["budget", "luxury", "adventure", "family"]
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"]

    for i, segment in enumerate(segments):
        if segment in data_collector.segment_arrivals:
            arrivals = data_collector.segment_arrivals[segment]
            ax.plot(
                range(len(arrivals)),
                arrivals,
                color=colors[i],
                linewidth=1.5,
                label=segment.title(),
            )

    ax.set_xlabel("Simulation Day")
    ax.set_ylabel("Active Tourists")
    ax.set_title("Tourist Segment Distribution Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"    Saved: {output_file}")


def plot_tfi_trajectories(sim, output_file: Path):
    """Plot 4: TFI trajectories by dependency category."""
    print("  [4/4] Generating TFI trajectories plot...")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Group destinations by dependency category
    categories = {
        "highly_dependent": [],
        "moderately_dependent": [],
        "low_dependency": [],
        "minimal_dependency": [],
    }

    for dest in sim.destinations.values():
        if dest.tourism_gdp_pct > 0 and dest.tfi_history:
            cat = dest.dependency_category
            if cat in categories:
                categories[cat].append(dest.tfi_history)

    # Plot average TFI trajectory for each category
    colors = {
        "highly_dependent": "#C73E1D",
        "moderately_dependent": "#F18F01",
        "low_dependency": "#2E86AB",
        "minimal_dependency": "#6B9080",
    }

    for category, histories in categories.items():
        if histories:
            # Align histories to same length
            max_len = max(len(h) for h in histories)
            avg_tfi = []
            for i in range(max_len):
                values = [h[i] if i < len(h) else h[-1] for h in histories]
                avg_tfi.append(np.mean(values))

            ax.plot(
                range(len(avg_tfi)),
                avg_tfi,
                color=colors[category],
                linewidth=2,
                label=category.replace("_", " ").title(),
            )

    ax.axhline(y=0.80, color="gray", linestyle="--", alpha=0.5, label="Baseline TFI")
    ax.axhline(
        y=0.60, color="orange", linestyle=":", alpha=0.5, label="Moderate Threshold"
    )
    ax.axhline(y=0.40, color="red", linestyle=":", alpha=0.5, label="Severe Threshold")

    ax.set_xlabel("Simulation Day")
    ax.set_ylabel("Tourism Friendliness Index (TFI)")
    ax.set_title("TFI Trajectories by Tourism Dependency Category")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.0)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"    Saved: {output_file}")


def main():
    print("=" * 80)
    print("PHASE 4 VALIDATION PLOTS GENERATOR")
    print("=" * 80)

    # Initialize simulation
    print("\n[1/2] Initializing simulation (365 days)...")
    countries = load_country_data()
    sim = Simulation(
        countries_data=countries,
        config={
            "duration_days": 365,
            "agent_count": 4000,
            "seed": 42,
        },
    )
    sim.initialize()

    # Run simulation
    print("[2/2] Running simulation...")
    sim.run(365)
    print(f"    Completed {sim.tick} ticks")

    # Generate plots
    print("\nGenerating validation plots...")
    output_dir = Path(__file__).parent.parent / "docs" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_time_series(sim.data_collector, output_dir / "01_time_series.png")

    plot_gini_coefficient(sim.data_collector, output_dir / "02_gini_coefficient.png")

    plot_segment_mix(sim.data_collector, output_dir / "03_segment_mix.png")

    plot_tfi_trajectories(sim, output_dir / "04_tfi_trajectories.png")

    # Summary statistics
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    # Calculate final Gini
    # dest_visitors is defaultdict(code -> list), get last tick values
    final_arrivals = []
    for code, history in sim.data_collector.dest_visitors.items():
        if history:
            final_arrivals.append(history[-1])

    if final_arrivals and sum(final_arrivals) > 0:
        sorted_arrivals = sorted(final_arrivals)
        n = len(sorted_arrivals)
        gini = (2 * np.sum((np.arange(1, n + 1) * sorted_arrivals))) / (
            n * np.sum(sorted_arrivals)
        ) - (n + 1) / n
        print(f"\nFinal Gini Coefficient: {gini:.3f}")
        print(f"  Target Range: 0.60-0.80")
        print(
            f"  Status: {'✓ PASS' if 0.60 <= gini <= 0.80 else '⚠ NEEDS CALIBRATION'}"
        )

    # Segment distribution
    print(f"\nSegment Distribution (Final Day):")
    total_active = sum(sim.data_collector.global_active[-1:] or [0])
    for segment in ["budget", "luxury", "adventure", "family"]:
        if segment in sim.data_collector.segment_arrivals:
            seg_active = (
                sim.data_collector.segment_arrivals[segment][-1]
                if sim.data_collector.segment_arrivals[segment]
                else 0
            )
            pct = (seg_active / total_active * 100) if total_active > 0 else 0
            print(f"  {segment.title():12s}: {seg_active:5.0f} tourists ({pct:5.1f}%)")

    # TFI summary
    tfi_values = [dest.tfi for dest in sim.destinations.values()]
    print(f"\nTFI Statistics:")
    print(f"  Mean TFI: {np.mean(tfi_values):.3f}")
    print(f"  Min TFI: {np.min(tfi_values):.3f}")
    print(f"  Max TFI: {np.max(tfi_values):.3f}")
    print(f"  Destinations with TFI < 0.80: {sum(1 for t in tfi_values if t < 0.80)}")

    print("\n" + "=" * 80)
    print(f"Plots saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
