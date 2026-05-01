#!/usr/bin/env python3
"""
Sensitivity Analysis Framework

Tests how emergent patterns change with key parameter variations.
Uses config-based parameter passing for proper isolation.

Usage:
    python scripts/sensitivity_analysis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import csv
from datetime import datetime
from typing import Dict, List
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulation.data.loaders import load_country_data


def run_simulation_with_params(
    param_name: str,
    param_value: float,
    countries_data: List[Dict],
    duration_days: int = 365,
    agent_count: int = 4000,
    seed: int = 42,
) -> Dict:
    """
    Run simulation with modified parameter.

    Properly isolates parameter changes by importing fresh modules each run.
    """
    # Force fresh imports by removing from cache
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith("simulation")]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Apply parameter modification before importing simulation modules
    if param_name == "tfi_decline_rate":
        # Patch the destination module before import
        import simulation.destinations.destination as dest_module

        dest_module.TFI_DECLINE_RATE = 0.05 * param_value

    elif param_name == "capacity_threshold":
        import simulation.destinations.destination as dest_module

        dest_module.CROWDING_THRESHOLD = param_value

    elif param_name == "softmax_temperature":
        import simulation.mechanics.choice as choice_module

        choice_module.SOFTMAX_TEMPERATURE = param_value

    elif param_name == "distance_friction":
        import simulation.mechanics.distance as dist_module

        # Multiply all distance weights by param_value
        if hasattr(dist_module, "DISTANCE_WEIGHTS"):
            for segment in dist_module.DISTANCE_WEIGHTS:
                dist_module.DISTANCE_WEIGHTS[segment] *= param_value

    # Import and run simulation
    from simulation.simulation import Simulation

    sim = Simulation(
        countries_data=countries_data,
        config={
            "duration_days": duration_days,
            "agent_count": agent_count,
            "seed": seed,
        },
    )
    sim.initialize()
    sim.run(duration_days)

    # Calculate metrics
    return calculate_metrics(sim, param_name, param_value, seed)


def calculate_metrics(sim, param_name: str, param_value: float, seed: int) -> Dict:
    """Calculate validation metrics from simulation."""
    dc = sim.data_collector

    # 1. Gini coefficient (final 30-day average)
    gini_values = []
    for tick in range(max(0, len(dc.global_active) - 30), len(dc.global_active)):
        values = []
        for code, history in dc.dest_visitors.items():
            if tick < len(history):
                values.append(history[tick])
        if len(values) > 1 and sum(values) > 0:
            sorted_values = sorted(values)
            n = len(sorted_values)
            gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (
                n * np.sum(sorted_values)
            ) - (n + 1) / n
            gini_values.append(gini)
    gini_avg = np.mean(gini_values) if gini_values else 0.0

    # 2. Total arrivals (365-day sum)
    total_arrivals = sum(dc.global_active)

    # 3. TFI decline (% destinations with TFI < 0.80)
    tfi_declined = sum(1 for d in sim.destinations.values() if d.tfi < 0.80)
    tfi_decline_pct = (tfi_declined / len(sim.destinations)) * 100

    # 4. Top 10 destination share
    final_visitors = {}
    for code, history in dc.dest_visitors.items():
        if history:
            final_visitors[code] = history[-1]
    total_final = sum(final_visitors.values())
    if total_final > 0:
        top10 = sorted(final_visitors.values(), reverse=True)[:10]
        top10_share = (sum(top10) / total_final) * 100
    else:
        top10_share = 0.0

    # 5. Segment distribution (final day)
    segment_dist = {}
    total_active = dc.global_active[-1] if dc.global_active else 0
    for segment in ["budget", "luxury", "adventure", "family"]:
        if segment in dc.segment_arrivals and dc.segment_arrivals[segment]:
            seg_active = dc.segment_arrivals[segment][-1]
            segment_dist[segment] = (
                (seg_active / total_active * 100) if total_active > 0 else 0
            )
        else:
            segment_dist[segment] = 0.0

    return {
        "param_name": param_name,
        "param_value": param_value,
        "seed": seed,
        "gini_coefficient": gini_avg,
        "total_arrivals": total_arrivals,
        "tfi_decline_pct": tfi_decline_pct,
        "top10_share": top10_share,
        "segment_budget": segment_dist["budget"],
        "segment_luxury": segment_dist["luxury"],
        "segment_adventure": segment_dist["adventure"],
        "segment_family": segment_dist["family"],
    }


def plot_sensitivity_results(results: List[Dict], output_dir: Path):
    """Generate sensitivity analysis plots."""
    print("\nGenerating sensitivity analysis plots...")

    # Group results by parameter
    by_param = {}
    for r in results:
        param = r["param_name"]
        if param not in by_param:
            by_param[param] = []
        by_param[param].append(r)

    # Create plots for each metric
    metrics = [
        ("gini_coefficient", "Gini Coefficient", "gini"),
        ("total_arrivals", "Total Arrivals", "arrivals"),
        ("tfi_decline_pct", "TFI Decline (%)", "tfi"),
        ("top10_share", "Top 10 Share (%)", "top10"),
    ]

    param_labels = {
        "tfi_decline_rate": "TFI Decline Rate Multiplier",
        "capacity_threshold": "Capacity Threshold",
        "softmax_temperature": "Softmax Temperature",
        "distance_friction": "Distance Friction Multiplier",
        "trip_frequency": "Trip Frequency Multiplier",
    }

    for metric_key, metric_name, plot_suffix in metrics:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()

        for i, param_name in enumerate(
            [
                "tfi_decline_rate",
                "capacity_threshold",
                "softmax_temperature",
                "distance_friction",
                "trip_frequency",
            ]
        ):
            param_results = by_param.get(param_name, [])
            if not param_results:
                axes[i].text(0.5, 0.5, "No data", ha="center", va="center")
                axes[i].axis("off")
                continue

            # Sort by parameter value
            param_results = sorted(param_results, key=lambda x: x["param_value"])

            x_values = [r["param_value"] for r in param_results]
            y_values = [r[metric_key] for r in param_results]

            ax = axes[i]
            ax.plot(x_values, y_values, "o-", linewidth=2, markersize=8)
            ax.set_xlabel(param_labels.get(param_name, param_name))
            ax.set_ylabel(metric_name)
            ax.set_title(
                f"{metric_name}\nvs {param_labels.get(param_name, param_name)}"
            )
            ax.grid(True, alpha=0.3)

            # Mark baseline
            baseline = 1.0 if param_name != "capacity_threshold" else 0.80
            ax.axvline(
                x=baseline, color="red", linestyle="--", alpha=0.5, label="Baseline"
            )

        # Hide unused subplot
        axes[5].axis("off")

        plt.tight_layout()
        output_file = output_dir / f"sensitivity_{plot_suffix}.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {output_file}")


def export_results_csv(results: List[Dict], output_file: Path):
    """Export sensitivity results to CSV."""
    fieldnames = [
        "param_name",
        "param_value",
        "seed",
        "gini_coefficient",
        "total_arrivals",
        "tfi_decline_pct",
        "top10_share",
        "segment_budget",
        "segment_luxury",
        "segment_adventure",
        "segment_family",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved: {output_file}")


def main():
    print("=" * 80)
    print("SENSITIVITY ANALYSIS FRAMEWORK")
    print("=" * 80)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Parameters to sweep (simplified to 3 that we can actually modify)
    param_sweeps = {
        "tfi_decline_rate": {
            "baseline": 1.0,
            "range": [0.75, 0.875, 1.0, 1.125, 1.25],
            "name": "TFI Decline Rate Multiplier",
        },
        "capacity_threshold": {
            "baseline": 0.80,
            "range": [0.70, 0.75, 0.80, 0.85, 0.90],
            "name": "Capacity Threshold",
        },
        "softmax_temperature": {
            "baseline": 1.0,
            "range": [0.5, 0.75, 1.0, 1.5, 2.0],
            "name": "Softmax Temperature",
        },
    }

    total_runs = len(param_sweeps) * 5
    print(f"Total simulations: {total_runs}")

    # Load country data (once)
    print("\n[1/3] Loading country data...")
    countries = load_country_data()
    print(f"  Loaded {len(countries)} countries")

    # Run parameter sweeps
    print("\n[2/3] Running parameter sweeps...")
    results = []

    run_count = 0
    for param_name, sweep_config in param_sweeps.items():
        print(f"\n  Sweeping: {param_name}")
        for param_value in sweep_config["range"]:
            run_count += 1
            print(
                f"    [{run_count}/{total_runs}] {param_name} = {param_value}...",
                end=" ",
            )

            try:
                metrics = run_simulation_with_params(
                    param_name=param_name,
                    param_value=param_value,
                    countries_data=countries,
                    duration_days=365,
                    agent_count=4000,
                    seed=42,
                )
                results.append(metrics)
                print(
                    f"Gini={metrics['gini_coefficient']:.3f}, Top10={metrics['top10_share']:.1f}%"
                )

            except Exception as e:
                print(f"ERROR: {e}")
                import traceback

                traceback.print_exc()

    # Save results
    print("\n[3/3] Saving results...")
    output_dir = Path(__file__).parent.parent / "docs" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    export_results_csv(results, output_dir / "sensitivity_results.csv")
    plot_sensitivity_results(results, output_dir)

    # Summary
    print("\n" + "=" * 80)
    print("SENSITIVITY ANALYSIS SUMMARY")
    print("=" * 80)

    print("\nParameter Sensitivity Rankings (by impact on Gini):")
    param_gini_ranges = {}
    for param_name in param_sweeps.keys():
        param_results = [
            r
            for r in results
            if r["param_name"] == param_name and r["gini_coefficient"] >= 0
        ]
        if param_results:
            gini_values = [r["gini_coefficient"] for r in param_results]
            param_gini_ranges[param_name] = max(gini_values) - min(gini_values)

    for i, (param, range_val) in enumerate(
        sorted(param_gini_ranges.items(), key=lambda x: x[1], reverse=True), 1
    ):
        print(f"  {i}. {param}: Gini range = {range_val:.3f}")

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOutput files:")
    print(f"  - {output_dir / 'sensitivity_results.csv'}")
    print(f"  - {output_dir / 'sensitivity_gini.png'}")
    print(f"  - {output_dir / 'sensitivity_arrivals.png'}")
    print(f"  - {output_dir / 'sensitivity_tfi.png'}")
    print(f"  - {output_dir / 'sensitivity_top10.png'}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
