# Validation Metrics & Success Criteria

**Version**: 2.0  
**Date**: 2026-04-17  
**Purpose**: Define quantitative metrics for validating simulation output against real data

---

## Validation Philosophy

**This model is EXPLORATORY, not predictive.**

Validation goals:
- ✅ Demonstrate plausible dynamics (not exact predictions)
- ✅ Match aggregate patterns (not country-level precision)
- ✅ Reproduce emergent phenomena (not pre-programmed outcomes)
- ✅ Enable scenario exploration (not forecasting)

---

## Tier 1: Aggregate Metrics (Must Match)

These metrics **must** be within acceptable ranges for the model to be considered valid.

| Metric | Target Value | Acceptable Range | Source | Priority |
|--------|--------------|------------------|--------|----------|
| **Baseline CAGR (2010-2019)** | 3.69% | 3.0-4.5% | UN Tourism | **CRITICAL** |
| **Pandemic shock (2020)** | -70.6% | -65% to -75% | UN Tourism | **CRITICAL** |
| **Recovery (2024)** | 94.5% of 2019 | 90-100% | UN Tourism | **CRITICAL** |
| **Growth volatility (σ)** | 8.52% | 6-12% | UN Tourism | HIGH |
| **Business/Personal split** | 11%/89% | 8-14% / 86-92% | UN Tourism | HIGH |

**Validation Method**: Run simulation with 2010-2024 parameters, compare output to UN Tourism data

---

## Tier 2: Distributional Metrics (Should Match)

These metrics test whether the model reproduces realistic **distributions** (not just aggregates).

| Metric | Target | Acceptable Range | Source | Priority |
|--------|--------|------------------|--------|----------|
| **Arrivals distribution (Gini coefficient)** | 0.65-0.75 | 0.60-0.80 | UN Tourism | HIGH |
| **Top 10 destinations share** | 45-55% | 40-60% | UN Tourism | HIGH |
| **Regional flow patterns** (intra-regional %) | | | | |
| - Europe | 65% | 55-75% | UN Tourism | MEDIUM |
| - Americas | 55% | 45-65% | UN Tourism | MEDIUM |
| - Asia-Pacific | 55% | 45-65% | UN Tourism | MEDIUM |
| **Distance distribution** (median trip distance) | 2,000-4,000 km | 1,500-5,000 km | UN Tourism | MEDIUM |

**Validation Method**: Compare simulated arrival distributions to real data using statistical tests (Kolmogorov-Smirnov)

---

## Tier 3: Emergent Patterns (Nice to Match)

These patterns should **emerge** from the model without being explicitly programmed.

| Pattern | Expected Behavior | Validation Method | Priority |
|---------|-------------------|-------------------|----------|
| **Hub formation** | Top destinations attract disproportionate flows | Check if top 10 stable over time | MEDIUM |
| **Regional clustering** | Nearby countries have correlated flows | Correlation matrix of arrivals | MEDIUM |
| **Rich-get-richer** | Popular destinations grow faster (log-scale) | Regression: growth vs. popularity | LOW |
| **Congestion spillover** | Overcrowded hubs lose visitors to alternatives | Negative correlation: crowding → growth | LOW |
| **Shock propagation** | Crisis in one region affects others | Cross-regional correlation during shocks | LOW |
| **Recovery heterogeneity** | Different destinations recover at different speeds | Std dev of recovery rates = 36% | MEDIUM |

---

## Tier 4: Sensitivity Tests (Robustness Checks)

These tests ensure the model behaves reasonably under parameter variations.

| Test | Parameter Varied | Expected Response | Priority |
|------|-----------------|-------------------|----------|
| **Distance friction sensitivity** | η ±50% | Regional flows change, global total stable | HIGH |
| **Popularity weight sensitivity** | θ ±50% | Hub concentration changes (not total) | MEDIUM |
| **Shock magnitude sensitivity** | Shock size ±20% | Recovery time scales proportionally | HIGH |
| **Segment distribution sensitivity** | Segment shares ±10% | Aggregate patterns stable | MEDIUM |
| **Capacity threshold sensitivity** | 80% → 70% or 90% | Overtourism timing changes | LOW |

**Validation Method**: One-way sensitivity analysis, check if model remains stable

---

## Country-Level Validation (Exploratory)

**Note**: We do **not** expect country-level precision. However, these patterns should hold:

| Metric | Target | Acceptable Range | Notes |
|--------|--------|------------------|-------|
| **Rank stability** (top 10) | 7-10 countries stable | 5-10 | France, Spain, USA should remain top |
| **Regional leaders** | At least 1 per region | All 5 regions | No region should be empty |
| **Small island states** | High tourism/GDP ratio | >20% for 10+ countries | Maldives, Bahamas, etc. |
| **Conflict-affected** | Lower arrivals during crises | -30% to -70% | Syria, Afghanistan, etc. |

---

## Validation Dashboard (Proposed)

**Real-time validation metrics during simulation runs:**

```python
validation_metrics = {
    # Tier 1: Aggregate
    'cagr_2010_2019': calculate_cagr(simulated_arrivals, 2010, 2019),
    'shock_2020': simulated_arrivals[2020] / simulated_arrivals[2019] - 1,
    'recovery_2024': simulated_arrivals[2024] / simulated_arrivals[2019],
    
    # Tier 2: Distributional
    'gini_coefficient': calculate_gini(simulated_arrivals),
    'top10_share': sum(top10_arrivals) / total_arrivals,
    'intra_regional_europe': calculate_intra_regional_flow('Europe'),
    
    # Tier 3: Emergent
    'rank_stability': calculate_rank_correlation(top10_2010, top10_2024),
    'distance_median': median_distance(all_trips),
    
    # Tier 4: Sensitivity
    'parameter_sensitivity': run_sensitivity_analysis()
}

# Validation status
if (0.03 <= validation_metrics['cagr_2010_2019'] <= 0.045 and
    -0.75 <= validation_metrics['shock_2020'] <= -0.65 and
    0.90 <= validation_metrics['recovery_2024'] <= 1.00):
    validation_status = "✅ PASSED - Aggregate metrics valid"
else:
    validation_status = "❌ FAILED - Calibration needed"
```

---

## Known Limitations (Cannot Validate)

These aspects are **not validated** against real data:

| Limitation | Reason | Impact |
|------------|--------|--------|
| **Country-level precision** | Model is exploratory, not econometric | Cannot forecast exact volumes |
| **Monthly seasonality** | No monthly data collected | Patterns may not match real seasonality |
| **City-level dynamics** | Only country-level data | Cannot validate intra-country flows |
| **Segment-specific behavior** | No empirical segment data | User-configurable, not validated |
| **Network effects** | Simplified popularity proxy | Not full social network modeling |

---

## Validation Test Plan

### Phase 1: Baseline Validation (Week 2)

**Test**: Run simulation with default parameters, 2010-2024

**Metrics to check**:
- CAGR 2010-2019 (target: 3.69%)
- Shock 2020 (target: -70.6%)
- Recovery 2024 (target: 94.5%)

**Pass criteria**: All three within acceptable ranges

### Phase 2: Distributional Validation (Week 3)

**Test**: Compare arrival distributions

**Metrics to check**:
- Gini coefficient (target: 0.65-0.75)
- Top 10 share (target: 45-55%)
- Regional flow patterns (target: match UN Tourism)

**Pass criteria**: All within acceptable ranges

### Phase 3: Emergent Patterns (Week 4)

**Test**: Qualitative assessment of emergent behavior

**Patterns to observe**:
- Hub formation (yes/no)
- Regional clustering (yes/no)
- Congestion spillover (yes/no)
- Rich-get-richer dynamics (yes/no)

**Pass criteria**: At least 3 of 4 patterns observed

### Phase 4: Sensitivity Analysis (Week 4)

**Test**: Parameter robustness

**Parameters to vary**:
- Distance friction (η): ±50%
- Popularity weight (θ): ±50%
- Shock magnitude: ±20%
- Segment shares: ±10%

**Pass criteria**: Model remains stable, no crashes or extreme outputs

---

## Comparison to Real Data

### Real Data Benchmarks (UN Tourism)

| Statistic | Value | Year |
|-----------|-------|------|
| Total arrivals | 1.5B | 2019 |
| Top destination (France) | 90M | 2019 |
| Top 10 share | 48% | 2019 |
| Intra-regional (Europe) | 65% | 2019 |
| Median trip distance | ~3,500 km | Estimate |
| Gini coefficient | 0.71 | Calculated |

### Simulation Targets

| Statistic | Target | Tolerance |
|-----------|--------|-----------|
| Total arrivals | 1.5B (2019) | ±10% |
| Top destination | 80-100M | ±20% |
| Top 10 share | 48% | ±10% |
| Intra-regional (Europe) | 65% | ±15% |
| Median trip distance | 3,500 km | ±25% |
| Gini coefficient | 0.71 | ±0.10 |

---

## Red Flags (Model Failures)

**Stop and recalibrate if you observe:**

| Red Flag | Likely Cause | Fix |
|----------|--------------|-----|
| **Winner-take-all** (single destination gets >30%) | Popularity weight (θ) too high | Reduce θ, check log-scale |
| **No hubs form** (uniform distribution) | Distance friction (η) too high | Reduce η, check choice set |
| **No recovery after shock** | Recovery function broken | Check hybrid recovery implementation |
| **Regional flows wrong** (e.g., Europe → Asia > Europe → Europe) | Regional clustering broken | Check home country assignment |
| **Crashes or NaN values** | Division by zero in utility | Check capacity = 0 edge cases |
| **All tourists choose same destination** | Softmax temperature (τ) too low | Increase τ (more randomness) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-16 | Initial validation metrics (aggregate only) |
| 2.0 | 2026-04-17 | Comprehensive update with distributional, emergent, and sensitivity metrics |

---

**Notes**:
- This is a living document - update as validation reveals new insights
- Tier 1 metrics are non-negotiable; Tier 3-4 are aspirational
- Model is exploratory - focus on patterns, not point predictions
