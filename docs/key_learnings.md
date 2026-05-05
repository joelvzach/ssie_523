# Key Learnings for Simulation Development

**Version**: 1.0  
**Date**: 2026-04-17  
**Purpose**: Summary of insights from Stage 1 to guide Stage 2 implementation

---

## 1. Tourist Behavior: Decision Model

**Core Finding**: Tourists choose destinations based on **8 factors** that combine into a utility function.

### The Utility Function

```python
U(destination) = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk 
                 - η·Distance + θ·Popularity + ε·SocialMedia + ζ·Memory
```

### The 8 Factors

| Factor | Symbol | Data Source | Weight Range |
|--------|--------|-------------|--------------|
| **Attractiveness** | α | WEF TTDI (119 countries) | 0.20-0.50 |
| **Cost** | β | Numbeo Cost Index (156 countries) | 0.15-0.50 |
| **Crowding** | γ | Calculated (arrivals/capacity) | 0.10-0.25 |
| **Risk** | δ | ACLED conflict events | 0.10-0.30 |
| **Distance** | η | Haversine (great-circle) | 0.15-0.45 |
| **Popularity** | θ | Log-scale arrivals (endogenous) | 0.10-0.40 |
| **Social Media** | ε | UGC quality/quantity | 0.20-0.40 |
| **Memory** | ζ | Return visitor probability | 0.55-0.65 |

### Segment-Specific Preferences

| Segment | Primary Driver | High Weight | Low Weight | Population Share |
|---------|---------------|-------------|------------|------------------|
| **Budget** | Affordability | Cost (β=0.50) | Distance (η=0.30) | 30% (configurable) |
| **Luxury** | Quality | Attractiveness (α=0.50) | Cost (β=0.15) | 20% (configurable) |
| **Adventure** | Attractions + Risk Tolerance | Attractiveness (α=0.40) | Crowding (γ=0.10) | 25% (configurable) |
| **Family** | Safety + Balance | Risk (δ=0.25) | Popularity (θ=0.25) | 25% (configurable) |

**Note**: Segment weights are user-configurable parameters for scenario exploration.

---

## 2. Geographic Structure: Origin-Destination Flows

**Core Finding**: Where tourists come from determines where they go through distance friction and regional clustering.

### Home Country Assignment

Each tourist agent has a home country sampled from regional distribution:

| Region | Share of Global Tourists | Intra-regional Flow |
|--------|-------------------------|---------------------|
| **Europe** | 45% | 65% stay within Europe |
| **Americas** | 25% | 55% stay within Americas |
| **Asia-Pacific** | 20% | 55% stay within Asia-Pacific |
| **Africa** | 5% | 45% stay within Africa |
| **Middle East** | 5% | 40% stay within Middle East |

### Distance Friction

**Calculation**: Haversine formula (great-circle distance)

```python
distance_km = haversine(origin_lat, origin_lon, dest_lat, dest_lon)
distance_penalty = η × (distance_km / 20000)  # Normalized 0-1
```

**Example Distances**:
- London → Paris: 344 km → negligible penalty
- New York → London: 5,585 km → moderate penalty
- Sydney → London: 17,016 km → strong penalty

### Regional Flow Patterns (Validated from UN Tourism)

| Home Region | Primary Destinations | Secondary Destinations |
|-------------|---------------------|------------------------|
| Europe | Europe (65%) | Americas (20%), Asia-Pacific (10%) |
| Americas | Americas (55%) | Europe (30%), Asia-Pacific (10%) |
| Asia-Pacific | Asia-Pacific (55%) | Europe (25%), Americas (15%) |

---

## 3. Carrying Capacity: Multi-Subsystem Model

**Core Finding**: Destinations have multiple capacity constraints that create bottlenecks.

### 4 Capacity Subsystems

| Subsystem | Calculation | Data Quality |
|-----------|-------------|--------------|
| **Accommodation** | Hotel beds + alternative accommodation × 80% occupancy | HIGH (OECD, UN Tourism) |
| **Transport** | Airport seats × 75% load factor | MEDIUM (UN Tourism transport) |
| **Infrastructure** | Population × 15% hosting capacity | LOW (assumption) |
| **Attractions** | Sum of heritage site capacities | LOW (UNESCO proxy) |

### Bottleneck Approach

```python
overall_capacity = min(
    accommodation_capacity,
    transport_capacity,
    infrastructure_capacity,
    attraction_capacity
)
```

### Linear Degradation Above Threshold

```python
utilization = arrivals / capacity

if utilization > 0.80:  # 80% threshold (user-configurable)
    attractiveness_degradation = γ × (utilization - 0.80)
```

**Why Linear**: Bertocchi et al. (2020) Venice carrying capacity study shows linear constraints, not quadratic collapse.

---

## 4. Shocks & Recovery: Type-Specific Dynamics

**Core Finding**: Different disaster types have distinct magnitudes and recovery patterns.

### Shock Parameters (Empirically Grounded)

| Shock Type | Magnitude | Duration | Recovery Pattern | Source |
|------------|-----------|----------|------------------|--------|
| **Pandemic** | -70% arrivals | 12 months | Hybrid (double-dip + S-curve) | UN Tourism + Škare et al. |
| **Volcanic eruption** | -4% per $1B cost | 6-12 months | S-curve | Rosselló et al. |
| **Wildfire** | -0.035% per $1B cost | 3-6 months | Linear | Rosselló et al. |
| **Flood** | -0.007% per 1K deaths | 6 months | Linear | Rosselló et al. |
| **Storm** | -0.003% per $1B cost | 6 months | Linear | Rosselló et al. |
| **Earthquake** | -1.7% per M affected | 12 months | S-curve | Rosselló et al. |
| **Conflict** | -30% to -50% | Variable | S-curve (2-8 years) | ACLED + assumption |

### Hybrid Recovery Function (Pandemic)

```python
def recovery_fraction(years_since_shock, shock_type):
    if shock_type == 'pandemic':
        if years_since_shock < 2.0:
            # Double-dip pattern (Škare et al. early phase)
            return double_dip_recovery(years_since_shock)
        else:
            # S-curve fits 2020-2024 UN Tourism data
            return 100 / (1 + exp(-0.8 × (years_since_shock - 2.5)))
    elif shock_type in ['flood', 'storm', 'wildfire']:
        # Linear recovery (Rosselló et al.: 6-12 months)
        return min(1.0, years_since_shock / 0.5)
    else:
        # Default S-curve
        return 100 / (1 + exp(-0.8 × (years_since_shock - 2.5)))
```

---

## 5. Network Effects: Endogenous Popularity

**Core Finding**: Destination popularity creates self-reinforcing dynamics with diminishing returns.

### Popularity Feedback Mechanism

```python
# Log-scale popularity (prevents winner-take-all)
popularity_index = log(previous_period_arrivals + 1) / log(max_arrivals + 1)

# Applied to utility
utility += θ × popularity_index
```

### Why Log-Scale?

| Destination | Annual Arrivals | Popularity Index | Utility Bonus (θ=0.25) |
|-------------|-----------------|------------------|------------------------|
| France | 82M | 0.94 | +0.235 |
| Spain | 84M | 0.94 | +0.235 |
| Thailand | 40M | 0.89 | +0.223 |
| Maldives | 1.7M | 0.38 | +0.095 |
| Bhutan | 0.3M | 0.28 | +0.070 |

**Benefits**:
- Prevents monopoly (linear would create winner-take-all)
- Captures social proof without overwhelming other factors
- Consistent with Weber-Fechner law (perception is logarithmic)
- Allows secondary destinations to compete on other factors

### Segment-Specific Popularity Sensitivity

| Segment | θ Weight | Rationale |
|---------|----------|-----------|
| **Budget** | 0.20 | Moderate trend-following |
| **Luxury** | 0.30 | Exclusive destinations become more desirable |
| **Adventure** | 0.10 | Seek undiscovered places |
| **Family** | 0.25 | Safety in numbers |

---

## 6. Empirical Foundation: What's Validated

### Data Sources (8 Integrated Datasets)

| Dataset | Coverage | Records | Key Variables |
|---------|----------|---------|---------------|
| **UN Tourism** | 215 countries, 1995-2024 | 163,656 | Arrivals, expenditure, purpose split |
| **WEF TTDI** | 119 countries, 2024 | 119 | Attractiveness scores (2.78-5.24) |
| **OECD** | 55 countries, 2008-2023 | ~30,000 | GDP share, nights spent |
| **ACLED** | Global, 1997-2026 | ~978,000 events | Conflict events, fatalities |
| **WHO Air Quality** | Global, 1990-2021 | 6,603 | PM2.5 concentrations |
| **Numbeo Cost** | 156 countries, 2024 | 156 | Cost indices (26.6-135.8) |
| **UNESCO** | 60 countries, 2024 | 60 | Heritage site counts |
| **World Bank** | 39 countries, 2010-2024 | ~80 | Political stability |

### Key Empirical Findings

| Finding | Value | Source | Confidence |
|---------|-------|--------|------------|
| Baseline CAGR (2010-2019) | 3.69% | UN Tourism analysis | **HIGH** |
| Pandemic shock (2020) | -70.6% | UN Tourism 2020 | **HIGH** |
| Recovery (2024) | 94.5% of 2019 | UN Tourism 2024 | **HIGH** |
| Business/Personal split | 11%/89% | UN Tourism purpose data | **HIGH** |
| TTDI correlation | r = 0.364 | Our correlation analysis | **MEDIUM** |
| Regional clustering (Europe) | 65% intra-regional | UN Tourism flow patterns | **HIGH** |
| Return visitor probability | 0.55-0.65 | Sönmez & Graefe (1998) | **HIGH** |
| Business price elasticity | -0.350 | Peng et al. (2014) | **HIGH** |
| Leisure price elasticity | -1.102 | Peng et al. (2014) | **HIGH** |

### Critical Limitation

**TTDI explains only 13% of variance** (r² = 0.13):
- 87% of tourism variation comes from factors NOT in our model
- Missing: cultural ties, flight networks, visa policies, marketing, colonial history
- **Implication**: Model is for **scenario exploration**, NOT prediction

---

## 7. User Configuration: Experimentation Framework

**Design Philosophy**: Turn data gaps into experimentation parameters.

### Configurable Parameters

| Parameter | Default | Range | What It Controls |
|-----------|---------|-------|------------------|
| **Segment shares** | 30/20/25/25 | 5-50% each | Population distribution |
| **Distance weight (η)** | 0.15-0.35 | 0.05-0.50 | Geographic friction strength |
| **Popularity weight (θ)** | 0.10-0.30 | 0.0-0.50 | Rich-get-richer strength |
| **Capacity threshold** | 80% | 60-95% | When overtourism begins |
| **Recovery speed** | 2.5 years | 1-5 years | How fast destinations recover |
| **Softmax temperature (τ)** | 1.0 | 0.1-5.0 | Choice determinism |

### Preset Configurations

Users can start with presets or create custom configurations:

1. **Literature-Based Defaults**: Our current parameter values
2. **Business/Leisure Only**: Simplified 2-segment model (data-backed)
3. **Equal Segments**: 25/25/25/25 for comparison
4. **Custom**: User-defined segments and weights

### Experimentation Examples

- "What if luxury travel doubles from 20% to 40%?"
- "What if tourists become 2x more distance-sensitive?"
- "What if popularity feedback is turned off?"
- "What if capacity threshold is 90% instead of 80%?"

---

## 8. Validation Framework: 4-Tier Approach

### Tier 1: Aggregate Metrics (Must Pass)

| Metric | Target | Acceptable Range | Data Source |
|--------|--------|------------------|-------------|
| CAGR (2010-2019) | 3.69% | 3.0-4.5% | UN Tourism |
| Pandemic shock (2020) | -70.6% | -65% to -75% | UN Tourism |
| Recovery (2024) | 94.5% | 90-100% | UN Tourism |

### Tier 2: Distributional Metrics (Should Pass)

| Metric | Target | Acceptable Range | Source |
|--------|--------|------------------|--------|
| Gini coefficient | 0.71 | 0.60-0.80 | Calculated from UN Tourism |
| Top 10 share | 48% | 40-60% | UN Tourism |
| Intra-regional (Europe) | 65% | 55-75% | UN Tourism flow patterns |
| Median trip distance | 3,500 km | 1,500-5,000 km | Estimate |

### Tier 3: Emergent Patterns (Nice to Have)

- ✅ Hub formation (top destinations attract disproportionate flows)
- ✅ Regional clustering (nearby countries have correlated flows)
- ✅ Rich-get-richer (popularity feedback creates concentration)
- ✅ Congestion spillover (overcrowded hubs lose visitors to alternatives)

### Tier 4: Sensitivity Tests (Robustness)

| Test | Parameter Varied | Expected Response |
|------|-----------------|-------------------|
| Distance friction | η ±50% | Regional flows change, global total stable |
| Popularity weight | θ ±50% | Hub concentration changes (not total) |
| Shock magnitude | ±20% | Recovery time scales proportionally |
| Segment distribution | ±10% | Aggregate patterns stable |

---

## 9. Implementation Roadmap

### Phase 1 (Week 1-2): Minimal Viable Simulation

**Scope**:
- 177 countries with real data (TTDI, cost, risk)
- Origin-destination structure (home countries, distance friction)
- Business/Personal segments (11%/89% from UN Tourism)
- 8-factor utility function with softmax choice
- Multi-subsystem capacity (4 subsystems, bottleneck)
- Shock/recovery dynamics (hybrid model)

**Expected Emergent Patterns**:
- Regional clustering
- Hub formation
- Recovery curves post-shock

### Phase 2 (Week 3-4): Enhanced Features

**Additions**:
- 4 user-configurable segments (Budget/Luxury/Adventure/Family)
- Popularity feedback (rich-get-richer, log-scale)
- Seasonality (4 climate zones: Mediterranean, Tropical, Temperate, Polar)
- Social media effects (UGC quality/quantity)
- Interactive dashboard (Streamlit)
- 4-tier validation tests

**Expected Emergent Patterns**:
- Seasonal oscillation
- Trend destination dynamics
- Congestion spillover

### Phase 3 (Stage 3): Advanced Features

**Future Enhancements**:
- City-level granularity (top 50 destinations)
- Full network effects (social network propagation)
- Supply-side dynamics (marketing, infrastructure investment)
- Policy interventions (visa liberalization, tourism taxes)
- Cultural/linguistic affinity modifiers

---

## Summary: Simulation Architecture

### What We're Building

An agent-based simulation where:
- Tourist agents with home countries choose destinations
- Based on 8-factor utility function
- With segment-specific preferences
- Destinations have multi-subsystem capacity limits
- Shocks reduce arrivals with type-specific recovery
- Popularity creates endogenous rich-get-richer dynamics
- Users configure parameters for scenario exploration

### Primary Use Case

**Scenario exploration with plausibility validation**:
- NOT for predicting exact tourist numbers
- NOT for forecasting future trends
- YES for understanding emergent dynamics
- YES for testing "what-if" scenarios
- YES for exploring plausible futures under different assumptions

### Success Criteria

- ✅ Tier 1 validation (aggregate metrics match historical data)
- ✅ Tier 2 validation (distributional patterns realistic)
- ✅ Tier 3 patterns emerge naturally (hubs, clustering, spillover)
- ✅ Tier 4 robustness (stable across parameter ranges)
- ✅ User can experiment with configurations and observe outcomes

---

## Phase 4 Learnings (May 1, 2026)

### GDP Integration

**Key Finding**: Tourism dependency (share of GDP from tourism) moderates resident attitudes toward overtourism.

**Implementation**:
- World Bank GDP parser with pickle cache (262 countries, ~0.3s initialization)
- Tourism-GDP % calculator: `tourism_expenditure / GDP * 100`
- TFI modifier: Highly dependent economies (>30%) decline 50% slower

**Validation**:
- 98 countries with tourism-GDP data
- Top 5: Aruba (98.9%), Andorra (94.6%), Antigua & Barbuda (90.1%), Seychelles (81.6%), Sint Maarten (78.8%)
- OECD correlation: r = 0.795 (valid for relative ranking)

### Data Quality Lessons

**Critical Discovery**: UN Tourism dataset contains 3 expenditure indicators per country-year:
1. Passenger transport services
2. Travel services (incl. goods)
3. **TOTAL** (= passenger + travel)

**Impact**: Loading all 3 without filtering created 3× duplication (8,911 → 3,794 rows after fix).

**Fix**: Filter to `expenditure_indicator == 'TOTAL'` in merge script.

### Calibration Insights

**Segment Distribution Problem**: Original trip frequencies caused over-representation:
- Luxury: 3.0 trips/year → 43.8% (target 20%)
- Adventure: 1.5 trips/year → 37.5% (target 25%)
- Budget: 0.75 trips/year → 7.4% (target 30%)
- Family: 0.75 trips/year → 11.4% (target 25%)

**Calibrated Frequencies** (RMSE reduced from 15.2% → 3.1%):
- Budget: 0.75 → 2.0 trips/year
- Luxury: 3.0 → 1.0 trips/year
- Adventure: 1.5 → 0.75 trips/year
- Family: 0.75 → 1.0 trips/year

### Validation Framework

**4-Tier Approach**:
1. **Tier 1 (Aggregate)**: CAGR, shock magnitude, recovery rate
2. **Tier 2 (Distributional)**: Gini coefficient, top 10 share, regional flows
3. **Tier 3 (Emergent)**: Hub formation, clustering, spillover (qualitative)
4. **Tier 4 (Robustness)**: Sensitivity to parameter variations

**Results**:
- Gini: 0.735 ✅ (target 0.60-0.80)
- OECD: r = 0.795 ✅ (target > 0.7)
- Segment RMSE: 3.1% ✅ (target < 10%)
- Code mapping: 100% ✅ (177/177 countries)

### Limitations Addressed

| Issue | Before | After | Status |
|-------|--------|-------|--------|
| Segment distribution | RMSE 15.2% | RMSE 3.1% | ✅ Fixed |
| Country code mapping | 77% (137/177) | 100% (177/177) | ✅ Fixed |
| TFI dynamics | 0 destinations declining | 50 destinations (28.6%) | ✅ Fixed |
| Data duplication | 3× rows (8,911) | Correct (3,794) | ✅ Fixed |

### Remaining Challenges

1. **Low crowding levels**: Average 1-2% utilization, TFI decline rarely triggers
   - Solution: Increase agent count (10K-20K) or add stress scenarios

2. **Risk score zero variance**: All countries have risk_score = 0.0 in 2019
   - Handled gracefully in visualizations (text annotation instead of trend line)

3. **TTDI low explanatory power**: r² = 0.13-0.20
   - Reframe as exploratory sandbox, not predictive model
   - Justifies agent-based approach (heterogeneity matters)

---

**Document Status**: ✅ Phase 4 Complete  
**Last Updated**: 2026-05-01  
**Owner**: Simulation Development Team
