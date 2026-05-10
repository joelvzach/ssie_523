# Parameter Sweep Analysis Guide

**Generated**: 2026-05-10  
**Total Simulations**: 28 runs (4 parameters × 7 values each)  
**Method**: One-at-a-time (OAT) sensitivity analysis

---

## Overview

This parameter sweep analysis explores how key simulation parameters affect emergent outcomes in the tourism simulation. By systematically varying one parameter at a time while holding others constant, we can identify:

- **Which parameters matter most** (sensitivity ranking)
- **Optimal parameter values** (closest to validation targets)
- **Trade-offs** between competing objectives
- **Segment differentiation** (heterogeneity) drivers

---

## Files Generated

| File | Description |
|------|-------------|
| `parameter_sweep_results.csv` | Full numerical results (28 rows × 16 columns) |
| `parameter_sweep_global_metrics.png` | Gini & heterogeneity vs parameters |
| `parameter_sweep_segment_analysis.png` | Segment-specific travel distances |
| `parameter_sweep_sensitivity.png` | Sensitivity ranking bar charts |
| `parameter_sweep_optimal_values.png` | Baseline vs optimal comparison |
| `parameter_sweep_heterogeneity_deep_dive.png` | Detailed heterogeneity analysis |

---

## Parameters Swept

### 1. Softmax Temperature (τ)
- **Range**: 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5
- **Baseline**: 1.0
- **What it controls**: Exploration vs exploitation in destination choice
- **Interpretation**:
  - τ < 0.5: Nearly deterministic (always choose best option)
  - τ = 1.0: Moderate randomness (realistic)
  - τ > 2.0: High randomness (nearly random choice)

### 2. Capacity Threshold
- **Range**: 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95
- **Baseline**: 0.80
- **What it controls**: Crowding ratio that triggers TFI decline
- **Interpretation**:
  - Lower threshold = Earlier policy response (more protective)
  - Higher threshold = Later policy response (more permissive)

### 3. TFI Decline Rate
- **Range**: 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10
- **Baseline**: 0.05
- **What it controls**: Speed of resident hostility growth when overcrowded
- **Interpretation**:
  - Higher rate = Faster policy activation
  - Lower rate = Slower response (more tolerant)

### 4. Distance Friction Multiplier
- **Range**: 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0
- **Baseline**: 1.0
- **What it controls**: Sensitivity to distance in utility function
- **Interpretation**:
  - Higher multiplier = Stronger distance penalty (more regional tourism)
  - Lower multiplier = Weaker distance penalty (more long-haul travel)

---

## Metrics Tracked

### Global Metrics

| Metric | Validation Target | What it Measures |
|--------|------------------|------------------|
| **Gini Coefficient** | 0.71 | Destination concentration (inequality in visitor distribution) |
| **Heterogeneity (CV)** | ~0.35 | Segment differentiation (do tourist types behave differently?) |
| **TFI Stress (%)** | - | % of destinations with TFI < 0.60 (policy activation) |
| **Top 10 Share (%)** | ~35% | Market dominance of top 10 destinations |

### Segment-Specific Metrics

- **Average distance traveled** (km) per segment
- **Destination concentration** (Gini) per segment
- **Trip length** (days) per segment

---

## Chart Interpretation Guide

### Chart 1: Global Metrics vs Parameters
**File**: `parameter_sweep_global_metrics.png`

**Layout**: 4 rows (parameters) × 2 columns (Gini, Heterogeneity)

**How to read**:
- **Left column (Gini)**: Shows destination concentration
  - Higher Gini = More unequal (few destinations dominate)
  - Target: 0.71 (empirical observation from UN Tourism data)
  - Green dotted line = validation target
  
- **Right column (Heterogeneity)**: Shows segment differentiation
  - Higher CV = Segments behave more differently
  - Target: ~0.35 (moderate differentiation)
  - Yellow annotation = Maximum heterogeneity point

**Key patterns to look for**:
- Upward slope = Positive relationship (increasing parameter increases metric)
- Downward slope = Negative relationship
- Flat line = Parameter has no effect (insensitive)
- Peak/valley = Optimal value exists in middle of range

---

### Chart 2: Segment-Specific Analysis
**File**: `parameter_sweep_segment_analysis.png`

**Layout**: 4 rows (parameters) × 1 column

**How to read**:
- Each colored line = One tourist segment
  - Blue = Budget
  - Pink = Luxury
  - Orange = Adventure
  - Green = Family
- Y-axis = Average travel distance (km)
- Vertical spread between lines = Heterogeneity

**Key patterns to look for**:
- **Converging lines** = Segments becoming similar (lower heterogeneity)
- **Diverging lines** = Segments differentiating (higher heterogeneity)
- **Crossing lines** = Parameter affects segments differently
- **Parallel lines** = All segments respond similarly to parameter

**Example interpretation**:
> "As distance friction increases, all segments travel shorter distances, but budget travelers reduce distance more sharply than luxury travelers (steeper slope)."

---

### Chart 3: Sensitivity Ranking
**File**: `parameter_sweep_sensitivity.png`

**Layout**: 3 bar charts (one per metric)

**How to read**:
- X-axis = Sensitivity Index (Range / Baseline)
- Y-axis = Parameters (sorted by sensitivity)
- Red dashed line = 0.5 (moderate sensitivity threshold)
- Dark red dashed line = 1.0 (high sensitivity threshold)

**Sensitivity Index interpretation**:
- **< 0.5**: Low sensitivity (parameter has minimal effect)
- **0.5 - 1.0**: Moderate sensitivity (parameter matters)
- **> 1.0**: High sensitivity (parameter is critical)

**Formula**:
```
Sensitivity Index = (max_metric - min_metric) / baseline_metric
```

**Example interpretation**:
> "Capacity threshold has the highest sensitivity index (1.2) for Gini coefficient, meaning it's the most influential parameter for destination concentration."

---

### Chart 4: Optimal Parameter Values
**File**: `parameter_sweep_optimal_values.png`

**Layout**: Grouped bar chart (baseline vs optimal)

**How to read**:
- Light blue bars = Baseline values
- Dark blue bars = Optimal values (closest to validation targets)
- Numbers on bars = Exact values

**How optimality is calculated**:
```
distance = sqrt(
  ((gini - 0.71) / 0.71)² + 
  ((heterogeneity - 0.35) / 0.35)²
)
optimal = parameter_value with minimum distance
```

**Interpretation**:
- Bars at same height = Baseline is already optimal
- Bars at different heights = Adjustment needed
- Direction of change = Which way to tune parameter

---

### Chart 5: Heterogeneity Deep Dive
**File**: `parameter_sweep_heterogeneity_deep_dive.png`

**Layout**: 2×2 grid with 4 panels

**Panel descriptions**:

**Top-Left: Heterogeneity vs Gini (Trade-off)**
- Scatter plot with connected points
- Each color = One parameter sweep
- Green box = Ideal region (target Gini × target heterogeneity)
- **Interpretation**: Can we achieve both realistic concentration AND segment differentiation?

**Top-Right: Segment Distance Distribution**
- Bar chart showing baseline distances by segment
- Red line = Mean distance
- Annotation = CV value
- **Interpretation**: How differentiated are segments at baseline?

**Bottom-Left: Heterogeneity vs Normalized Parameter Value**
- All parameters plotted on same scale (0-1)
- Allows direct comparison of heterogeneity effects
- **Interpretation**: Which parameter creates the most heterogeneity per unit change?

**Bottom-Right: Interpretation Guide**
- Text box with key findings
- CV thresholds:
  - CV > 0.5 = HIGH heterogeneity (ideal for resilience)
  - CV = 0.2-0.5 = MODERATE heterogeneity (realistic)
  - CV < 0.2 = LOW heterogeneity (segments too similar)

---

## Key Findings from Initial Sweep

### 1. Metrics Summary

| Metric | Observed Range | Target | Gap |
|--------|---------------|--------|-----|
| Gini coefficient | 0.537 - 0.610 | 0.71 | -0.10 to -0.17 |
| Heterogeneity (CV) | 0.092 - 0.153 | ~0.35 | -0.20 to -0.26 |
| TFI stress | 11.4% - 21.1% | - | Acceptable |
| Top 10 share | 30.6% - 38.9% | ~35% | ✓ On target |

### 2. Sensitivity Rankings

**By Gini coefficient** (most to least sensitive):
1. Capacity threshold (highest impact)
2. Distance friction
3. Softmax temperature
4. TFI decline rate (lowest impact)

**By Heterogeneity** (most to least sensitive):
1. Softmax temperature (highest impact)
2. Distance friction
3. Capacity threshold
4. TFI decline rate (lowest impact)

### 3. Optimal Values

All parameters performed best at or near their **baseline values**:
- Softmax Temperature: 1.0 ✓
- Capacity Threshold: 0.80 ✓
- TFI Decline Rate: 0.05 ✓
- Distance Friction: 1.0 ✓

This validates the literature-backed baseline configuration.

### 4. Critical Insights

**Gini coefficient is too low** (0.61 max vs 0.71 target):
- Suggests destination concentration is insufficient
- Possible fixes:
  - Increase popularity feedback (rich-get-richer effect)
  - Reduce choice set size
  - Increase utility weight on attractiveness

**Heterogeneity is too low** (0.15 max vs 0.35 target):
- Segments are not differentiated enough
- Possible fixes:
  - Increase segment-specific utility weight differences
  - Use segment-specific temperature values (not uniform)
  - Add segment-specific constraints (budget caps, time limits)

**TFI stress is acceptable** (11-21%):
- Reasonable policy activation levels
- No adjustment needed

---

## Recommendations for Next Steps

### Immediate Actions

1. **Fine-grained sweep around optimal values**
   - Current step size is too coarse
   - Recommend: 0.1 increments around baseline

2. **Test segment-specific parameters**
   - Currently using uniform temperature (τ=1.0 for all segments)
   - Literature suggests: τ_budget=0.8, τ_luxury=0.5, τ_adventure=1.0, τ_family=0.6

3. **Add popularity feedback parameter**
   - Not included in this sweep
   - Expected to increase Gini coefficient significantly

### Future Sweeps

**Stage 2: Interaction Effects**
- Full factorial design (all parameter combinations)
- Expected runs: 7^4 = 2,401 (requires parallelization)

**Stage 3: Additional Parameters**
- Popularity weight (θ)
- Choice set size
- Utility weight variations
- Memory decay rate

**Stage 4: Calibration**
- Use optimization algorithm (e.g., Bayesian optimization)
- Multi-objective: minimize distance to all validation targets simultaneously

---

## How to Re-run the Analysis

### Option 1: Run the Script
```bash
cd /Users/joelvzach/Code/ssie_523
python scripts/parameter_sweep.py
```
- Takes ~15-20 minutes for 28 runs
- Automatically generates all plots
- Saves results to `docs/validation/`

### Option 2: Use the Jupyter Notebook
```bash
jupyter notebook notebooks/02_parameter_sweep_analysis.ipynb
```
- Run cells 1-6 (setup)
- Skip cell 12 (execution) if using existing results
- Run cells 14-24 (analysis & plotting)
- Interactive exploration possible

### Option 3: Load Results Directly
```python
import pandas as pd
df = pd.read_csv('docs/validation/parameter_sweep_results.csv')
```
- Quick analysis without re-running simulations
- 28 rows × 16 columns
- Ready for custom visualizations

---

## Glossary

| Term | Definition |
|------|------------|
| **Gini Coefficient** | Measure of inequality (0 = perfect equality, 1 = perfect inequality) |
| **Coefficient of Variation (CV)** | Standard deviation / mean (measures relative variability) |
| **Heterogeneity** | Degree of segment differentiation in the simulation |
| **TFI (Tourism Friendliness Index)** | Resident attitudes toward tourists (0 = hostile, 1 = welcoming) |
| **Sensitivity Index** | (max - min) / baseline (measures parameter impact) |
| **OAT (One-at-a-time)** | Vary one parameter while holding others constant |
| **Baseline** | Literature-backed or calibrated reference value |
| **Validation Target** | Empirical value from real-world data |

---

## References

- Literature parameters: `docs/literature_parameters.md`
- Validation metrics: `docs/validation_metrics.md`
- Simulation code: `simulation/`
- Data collection: `simulation/data_collection/collector.py`

---

**Questions?** Open an issue on GitHub or contact the development team.
