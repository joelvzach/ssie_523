#!/usr/bin/env python3
"""
Parameter Sweep Analysis Script

Systematically explores how key parameters affect simulation outcomes:
- Destination concentration (Gini coefficient)
- Segment heterogeneity (coefficient of variation)
- TFI dynamics (policy stress)
- Segment-specific behaviors

Usage:
    python scripts/parameter_sweep.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from datetime import datetime
import csv

# Plotting configuration
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


# ============================================================================
# BASELINE CONFIGURATION
# ============================================================================

BASELINE_CONFIG = {
    # Simulation setup
    'agent_count': 4000,
    'duration_days': 365,
    'seed': 42,
    'segment_shares': {
        'budget': 0.30,
        'luxury': 0.20,
        'adventure': 0.25,
        'family': 0.25,
    },
    
    # Utility weights (from utility.py)
    'softmax_temperature': 1.0,
    'distance_friction': 1.0,
    
    # Destination dynamics (from destination.py)
    'capacity_threshold': 0.80,
    'tfi_decline_rate': 0.05,
    'tfi_recovery_rate': 0.02,
    
    # Crowding feedback
    'crowding_exponent': 2.0,
}


# ============================================================================
# PARAMETER SWEEP DEFINITIONS
# ============================================================================

PARAM_SWEEPS = {
    'softmax_temperature': {
        'range': [0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5],
        'baseline': 1.0,
        'label': 'Softmax Temperature (τ)',
        'description': 'Controls exploration vs exploitation in destination choice',
    },
    'capacity_threshold': {
        'range': [0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
        'baseline': 0.80,
        'label': 'Capacity Threshold',
        'description': 'Crowding ratio that triggers TFI decline',
    },
    'tfi_decline_rate': {
        'range': [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10],
        'baseline': 0.05,
        'label': 'TFI Decline Rate',
        'description': 'Rate of TFI decline when crowding exceeds threshold',
    },
    'distance_friction': {
        'range': [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
        'baseline': 1.0,
        'label': 'Distance Friction Multiplier',
        'description': 'Scaling factor on distance penalty in utility function',
    },
}


# ============================================================================
# METRICS CALCULATION
# ============================================================================

def calculate_gini(values: List[float]) -> float:
    """Calculate Gini coefficient for destination concentration."""
    if len(values) < 2 or sum(values) == 0:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * np.sum(sorted_values)) - (n + 1) / n
    return gini


def calculate_heterogeneity_cv(segment_metrics: Dict[str, float]) -> float:
    """Calculate coefficient of variation across segments."""
    values = list(segment_metrics.values())
    if len(values) < 2:
        return 0.0
    
    mean = np.mean(values)
    if mean == 0:
        return 0.0
    
    std = np.std(values)
    return std / mean


def calculate_metrics(sim, param_name: str, param_value: float) -> Dict:
    """Calculate comprehensive metrics from simulation run."""
    dc = sim.data_collector
    
    # 1. Gini coefficient (final 30-day average)
    gini_values = []
    for tick in range(max(0, len(dc.global_active) - 30), len(dc.global_active)):
        values = []
        for code, history in dc.dest_visitors.items():
            if tick < len(history):
                values.append(history[tick])
        if len(values) > 1 and sum(values) > 0:
            gini_values.append(calculate_gini(values))
    gini_avg = np.mean(gini_values) if gini_values else 0.0
    
    # 2. Total arrivals
    total_arrivals = sum(dc.global_active)
    
    # 3. TFI stress (% destinations with TFI < 0.60)
    tfi_stressed = sum(1 for d in sim.destinations.values() if d.tfi < 0.60)
    tfi_stress_pct = (tfi_stressed / len(sim.destinations)) * 100 if sim.destinations else 0.0
    
    # 4. Top 10 destination share
    final_visitors = {}
    for code, history in dc.dest_visitors.items():
        if history:
            final_visitors[code] = history[-1]
    total_final = sum(final_visitors.values())
    top10_share = 0.0
    if total_final > 0:
        top10 = sorted(final_visitors.values(), reverse=True)[:10]
        top10_share = (sum(top10) / total_final) * 100
    
    # 5. Segment-specific metrics (from data collector)
    segment_distances = {}
    segment_concentration = {}
    segment_trip_lengths = {}
    
    for segment in ['budget', 'luxury', 'adventure', 'family']:
        # Get from collected data if available
        if hasattr(dc, 'segment_distances') and segment in dc.segment_distances:
            segment_distances[segment] = np.mean(dc.segment_distances[segment]) if dc.segment_distances[segment] else 0.0
        else:
            segment_distances[segment] = 0.0
        
        segment_concentration[segment] = 0.0
        segment_trip_lengths[segment] = 0.0
    
    # 6. Heterogeneity (CV across segments)
    heterogeneity_distance = calculate_heterogeneity_cv(segment_distances)
    heterogeneity_concentration = calculate_heterogeneity_cv(segment_concentration)
    
    return {
        'param_name': param_name,
        'param_value': param_value,
        'seed': BASELINE_CONFIG['seed'],
        'gini_coefficient': gini_avg,
        'total_arrivals': total_arrivals,
        'tfi_stress_pct': tfi_stress_pct,
        'top10_share': top10_share,
        'segment_distances': segment_distances,
        'segment_concentration': segment_concentration,
        'heterogeneity_distance': heterogeneity_distance,
        'heterogeneity_concentration': heterogeneity_concentration,
        'segment_trip_lengths': segment_trip_lengths,
    }


# ============================================================================
# PARAMETER PATCHING
# ============================================================================

def apply_parameter_patch(param_name: str, param_value: float):
    """Apply parameter modification to simulation modules."""
    # Force fresh imports
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('simulation')]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    if param_name == 'tfi_decline_rate':
        import simulation.destinations.destination as dest_module
        dest_module.TFI_DECLINE_RATE = param_value
        
    elif param_name == 'capacity_threshold':
        import simulation.destinations.destination as dest_module
        dest_module.CROWDING_THRESHOLD = param_value
        
    elif param_name == 'softmax_temperature':
        import simulation.mechanics.utility as utility_module
        for segment in utility_module.SEGMENT_TEMPERATURE:
            utility_module.SEGMENT_TEMPERATURE[segment] = param_value
        
    elif param_name == 'distance_friction':
        import simulation.mechanics.utility as utility_module
        # Store original weights if not already patched
        if not hasattr(utility_module, '_original_distance_weights'):
            utility_module._original_distance_weights = {}
            for segment in ['budget', 'luxury', 'adventure', 'family']:
                utility_module._original_distance_weights[segment] = \
                    utility_module.SEGMENT_WEIGHTS[segment]['η']
        # Apply multiplier to original weights
        for segment in ['budget', 'luxury', 'adventure', 'family']:
            utility_module.SEGMENT_WEIGHTS[segment]['η'] = \
                utility_module._original_distance_weights[segment] * param_value


def run_simulation_with_params(param_name: str, param_value: float, countries_data: List[Dict]) -> Dict:
    """Run single simulation with modified parameter."""
    # Apply parameter patch
    apply_parameter_patch(param_name, param_value)
    
    # Import and run simulation
    from simulation.simulation import Simulation
    
    sim_config = {
        'duration_days': BASELINE_CONFIG['duration_days'],
        'agent_count': BASELINE_CONFIG['agent_count'],
        'seed': BASELINE_CONFIG['seed'],
        'segment_shares': BASELINE_CONFIG['segment_shares'],
    }
    
    sim = Simulation(countries_data=countries_data, config=sim_config)
    sim.initialize()
    sim.run(BASELINE_CONFIG['duration_days'])
    
    return calculate_metrics(sim, param_name, param_value)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 80)
    print("PARAMETER SWEEP ANALYSIS")
    print("=" * 80)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nBaseline configuration:")
    print(f"  Agents: {BASELINE_CONFIG['agent_count']}")
    print(f"  Duration: {BASELINE_CONFIG['duration_days']} days")
    print(f"  Seed: {BASELINE_CONFIG['seed']}")
    print(f"\nParameters to sweep: {len(PARAM_SWEEPS)}")
    for param_name, config in PARAM_SWEEPS.items():
        print(f"  - {config['label']}: {len(config['range'])} values")
    
    # Load country data
    print("\n[1/2] Loading country data...")
    from simulation.data.loaders import load_country_data
    countries = load_country_data()
    print(f"  Loaded {len(countries)} countries")
    
    # Run parameter sweeps
    print("\n[2/2] Running parameter sweeps...")
    all_results = []
    
    total_runs = sum(len(config['range']) for config in PARAM_SWEEPS.values())
    run_count = 0
    
    for param_name, sweep_config in PARAM_SWEEPS.items():
        print(f"\n  Sweeping: {sweep_config['label']}")
        
        for param_value in sweep_config['range']:
            run_count += 1
            print(f"    [{run_count}/{total_runs}] {param_name} = {param_value}...", end=" ", flush=True)
            
            try:
                metrics = run_simulation_with_params(
                    param_name=param_name,
                    param_value=param_value,
                    countries_data=countries,
                )
                all_results.append(metrics)
                print(f"Gini={metrics['gini_coefficient']:.3f}, Heterogeneity={metrics['heterogeneity_distance']:.3f}")
                
            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n\nCompleted {len(all_results)} runs")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Convert to DataFrame
    results_flat = []
    for r in all_results:
        row = {
            'param_name': r['param_name'],
            'param_value': r['param_value'],
            'gini': r['gini_coefficient'],
            'total_arrivals': r['total_arrivals'],
            'tfi_stress_pct': r['tfi_stress_pct'],
            'top10_share': r['top10_share'],
            'heterogeneity_distance': r['heterogeneity_distance'],
            'heterogeneity_concentration': r['heterogeneity_concentration'],
        }
        for segment in ['budget', 'luxury', 'adventure', 'family']:
            row[f'{segment}_distance'] = r['segment_distances'].get(segment, 0)
            row[f'{segment}_concentration'] = r['segment_concentration'].get(segment, 0)
        results_flat.append(row)
    
    df_results = pd.DataFrame(results_flat)
    
    # Save results
    output_dir = Path(__file__).parent.parent / 'docs' / 'validation'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_dir / 'parameter_sweep_results.csv', index=False)
    print(f"\nExported results to: {output_dir / 'parameter_sweep_results.csv'}")
    
    # Generate plots
    generate_plots(df_results, output_dir)
    
    # Print summary
    print_summary(df_results)


def generate_plots(df_results: pd.DataFrame, output_dir: Path):
    """Generate visualization plots."""
    print("\nGenerating plots...")
    
    segments = ['budget', 'luxury', 'adventure', 'family']
    segment_colors = {'budget': '#2E86AB', 'luxury': '#A23B72', 'adventure': '#F18F01', 'family': '#4CAF50'}
    
    # Plot 1: Global metrics vs parameters
    fig, axes = plt.subplots(len(PARAM_SWEEPS), 2, figsize=(14, 4 * len(PARAM_SWEEPS)))
    
    for i, (param_name, sweep_config) in enumerate(PARAM_SWEEPS.items()):
        param_data = df_results[df_results['param_name'] == param_name].sort_values('param_value')
        baseline_val = sweep_config['baseline']
        
        # Left: Gini coefficient
        ax1 = axes[i, 0] if len(PARAM_SWEEPS) > 1 else axes[0]
        ax1.plot(param_data['param_value'], param_data['gini'], 'o-', linewidth=2, markersize=8, color='navy')
        ax1.axvline(x=baseline_val, color='red', linestyle='--', alpha=0.7, label=f'Baseline ({baseline_val})')
        ax1.axhline(y=0.71, color='green', linestyle=':', alpha=0.7, label='Target (0.71)')
        ax1.set_xlabel(sweep_config['label'])
        ax1.set_ylabel('Gini Coefficient')
        ax1.set_title(f'Destination Concentration\nvs {sweep_config["label"]}')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Right: Heterogeneity
        ax2 = axes[i, 1] if len(PARAM_SWEEPS) > 1 else axes[1]
        ax2.plot(param_data['param_value'], param_data['heterogeneity_distance'], 
                's-', linewidth=2.5, markersize=10, color='darkblue')
        ax2.axvline(x=baseline_val, color='red', linestyle='--', alpha=0.7, label='Baseline')
        ax2.set_xlabel(sweep_config['label'])
        ax2.set_ylabel('Heterogeneity (CV)')
        ax2.set_title(f'Segment Heterogeneity\nvs {sweep_config["label"]}')
        ax2.grid(True, alpha=0.3)
        
        # Annotate max heterogeneity
        max_het_idx = param_data['heterogeneity_distance'].idxmax()
        max_het_row = param_data.loc[max_het_idx]
        ax2.annotate(f'Max: {max_het_row["heterogeneity_distance"]:.3f}',
                    xy=(max_het_row['param_value'], max_het_row['heterogeneity_distance']),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7),
                    fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parameter_sweep_global_metrics.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'parameter_sweep_global_metrics.png'}")
    
    # Plot 2: Segment-specific analysis
    fig, axes = plt.subplots(len(PARAM_SWEEPS), 1, figsize=(14, 4 * len(PARAM_SWEEPS)))
    
    for i, (param_name, sweep_config) in enumerate(PARAM_SWEEPS.items()):
        param_data = df_results[df_results['param_name'] == param_name].sort_values('param_value')
        baseline_val = sweep_config['baseline']
        
        ax = axes[i] if len(PARAM_SWEEPS) > 1 else axes[0]
        
        for segment in segments:
            col = f'{segment}_distance'
            ax.plot(param_data['param_value'], param_data[col], 'o-', 
                    linewidth=2, markersize=6, color=segment_colors[segment], 
                    label=segment.capitalize())
        
        ax.axvline(x=baseline_val, color='gray', linestyle='--', alpha=0.5, label='Baseline')
        ax.set_xlabel(sweep_config['label'])
        ax.set_ylabel('Average Distance (km)')
        ax.set_title(f'Segment Distance\nvs {sweep_config["label"]}')
        ax.legend(ncol=4, fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parameter_sweep_segment_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'parameter_sweep_segment_analysis.png'}")
    
    # Plot 3: Sensitivity ranking
    sensitivity_data = []
    for param_name in PARAM_SWEEPS.keys():
        param_data = df_results[df_results['param_name'] == param_name]
        
        for metric in ['gini', 'heterogeneity_distance', 'tfi_stress_pct']:
            values = param_data[metric].values
            baseline_val = param_data[param_data['param_value'] == PARAM_SWEEPS[param_name]['baseline']][metric].values
            
            if len(baseline_val) > 0 and baseline_val[0] > 0:
                range_val = max(values) - min(values)
                sensitivity_idx = range_val / baseline_val[0]
                
                sensitivity_data.append({
                    'parameter': param_name,
                    'metric': metric,
                    'sensitivity_index': sensitivity_idx,
                })
    
    df_sensitivity = pd.DataFrame(sensitivity_data)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for i, metric in enumerate(['gini', 'heterogeneity_distance', 'tfi_stress_pct']):
        metric_data = df_sensitivity[df_sensitivity['metric'] == metric].sort_values('sensitivity_index', ascending=True)
        
        ax = axes[i]
        bars = ax.barh(metric_data['parameter'], metric_data['sensitivity_index'], color='steelblue')
        ax.set_xlabel('Sensitivity Index (Range / Baseline)')
        ax.set_title(f'Sensitivity Ranking: {metric.replace("_", " ").title()}')
        ax.axvline(x=0.5, color='red', linestyle='--', alpha=0.5, label='Moderate sensitivity')
        ax.axvline(x=1.0, color='darkred', linestyle='--', alpha=0.5, label='High sensitivity')
        ax.legend(fontsize=8)
        
        # Add value labels
        for bar, val in zip(bars, metric_data['sensitivity_index']):
            ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2, f'{val:.2f}', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parameter_sweep_sensitivity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'parameter_sweep_sensitivity.png'}")


def print_summary(df_results: pd.DataFrame):
    """Print summary statistics and insights."""
    print("\n" + "=" * 80)
    print("PARAMETER SWEEP ANALYSIS - SUMMARY")
    print("=" * 80)
    
    print("\n1. METRICS RANGE:")
    print(f"   Gini coefficient: {df_results['gini'].min():.3f} - {df_results['gini'].max():.3f}")
    print(f"   Heterogeneity (CV): {df_results['heterogeneity_distance'].min():.3f} - {df_results['heterogeneity_distance'].max():.3f}")
    print(f"   TFI stress: {df_results['tfi_stress_pct'].min():.1f}% - {df_results['tfi_stress_pct'].max():.1f}%")
    print(f"   Top 10 share: {df_results['top10_share'].min():.1f}% - {df_results['top10_share'].max():.1f}%")
    
    print("\n2. OPTIMAL PARAMETER VALUES (closest to validation targets):")
    validation_targets = {'gini': 0.71, 'heterogeneity_distance': 0.35}
    
    for param_name, sweep_config in PARAM_SWEEPS.items():
        param_data = df_results[df_results['param_name'] == param_name]
        
        # Find value closest to targets
        distances = []
        for idx, row in param_data.iterrows():
            dist = 0
            for metric, target in validation_targets.items():
                if metric in row and target > 0:
                    dist += ((row[metric] - target) / target) ** 2
            distances.append(np.sqrt(dist))
        
        best_idx = np.argmin(distances)
        best_row = param_data.iloc[best_idx]
        
        print(f"\n   {sweep_config['label']}:")
        print(f"      Baseline: {sweep_config['baseline']}")
        print(f"      Optimal:  {best_row['param_value']}")
        print(f"      Expected Gini: {best_row['gini']:.3f}, Heterogeneity: {best_row['heterogeneity_distance']:.3f}")
    
    print("\n3. KEY INSIGHTS:")
    print(f"   • Parameters swept: {len(PARAM_SWEEPS)}")
    print(f"   • Total simulations: {len(df_results)}")
    print(f"   • Best Gini (closest to 0.71): {df_results.assign(dist=lambda x: abs(x['gini'] - 0.71)).sort_values('dist').iloc[0]['gini']:.3f}")
    print(f"   • Best heterogeneity (closest to 0.35): {df_results.assign(dist=lambda x: abs(x['heterogeneity_distance'] - 0.35)).sort_values('dist').iloc[0]['heterogeneity_distance']:.3f}")
    
    print(f"\n\nAnalysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOutput files saved to: docs/validation/")
    print(f"  - parameter_sweep_results.csv")
    print(f"  - parameter_sweep_global_metrics.png")
    print(f"  - parameter_sweep_segment_analysis.png")
    print(f"  - parameter_sweep_sensitivity.png")


if __name__ == "__main__":
    main()
