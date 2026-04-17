# Key Learnings for Simulation Development

**Version**: 1.0  
**Date**: 2026-04-17  
**Purpose**: Summary of insights from Stage 1 to guide Stage 2 implementation

---

## 1. Tourist Behavior: What We Learned

**Key Finding**: Tourists choose destinations based on **8 factors**, NOT just 4 like we originally thought.

### The Decision Process

```
Tourist thinks: "Where should I go?"

1. Attractiveness - How good is the destination? (TTDI score)
2. Cost - Can I afford it?
3. Crowding - Will it be too packed?
4. Risk - Is it safe? (conflict, crime)
5. Distance - How far do I have to travel? ← NEW
6. Popularity - Are other people going there? ← NEW
7. Social Media - What do reviews say?
8. Memory - Have I been there before? Would I go back?
```

### Segment Differences

| Segment | Primary Driver | Secondary Driver | Low Priority |
|---------|---------------|------------------|--------------|
| **Budget** | Cost (50%) | Attractiveness (20%) | Distance (30%) |
| **Luxury** | Attractiveness (50%) | Risk (20%) | Cost (15%) |
| **Adventure** | Attractiveness (40%) | Risk tolerance (30%) | Cost (20%) |
| **Family** | Safety/Risk (25%) | Cost (30%) | Crowding (25%) |

**⚠️ Important Caveat**: These segment weights (50%, 30%, etc.) are **educated guesses, NOT from data**. Users can adjust them in the simulation.

---

## 2. Geographic Reality: What We Learned

**Key Finding**: Where tourists **COME FROM** matters as much as where they're going.

### Old Model (Wrong)
- All tourists choose from all 177 countries equally
- A tourist could just as easily choose Antarctica as France

### New Model (Realistic)
- Every tourist has a **home country**
- Regional clustering patterns:

| Home Region | % Stay Intra-regional | Primary Extra-regional | Secondary Extra-regional |
|-------------|----------------------|------------------------|-------------------------|
| **Europe** | 65% | Americas (20%) | Asia-Pacific (10%) |
| **Americas** | 55% | Europe (30%) | Asia-Pacific (10%) |
| **Asia-Pacific** | 55% | Europe (25%) | Americas (15%) |
| **Africa** | 45% | Europe (35%) | Middle East (15%) |
| **Middle East** | 40% | Europe (35%) | Asia-Pacific (20%) |

- **Distance matters**: farther = less likely (but not impossible)

### Why This Matters
- Creates realistic regional clusters
- Explains why nearby countries get similar visitor numbers
- Makes the simulation look like real tourism flows

---

## 3. Capacity & Overtourism: What We Learned

**Key Finding**: Destinations have limits, but degradation is **GRADUAL**, not sudden.

### Old Model (Wrong)
- Single capacity number (e.g., 1M tourists max)
- Nothing happens until 80%, then sudden crash

### New Model (Realistic)

**4 Separate Capacity Limits**:
1. **Hotels** - How many beds available?
2. **Transport** - How many flight seats?
3. **Infrastructure** - Can roads/water/waste handle it?
4. **Attractions** - How much can sites handle?

**Bottleneck Rule**: Overall capacity = the WORST of the 4 subsystems

**Linear Degradation**: Above 80% full, attractiveness slowly declines (not suddenly)

```python
if arrivals > 0.8 × capacity:
    degradation = γ × (arrivals/capacity - 0.8)  # Linear, not quadratic
```

**⚠️ Important Caveat**: We only have good data for hotels. Transport/infrastructure/attractions are rough estimates.

---

## 4. Shocks & Recovery: What We Learned

**Key Finding**: Different disasters have **different impacts** and **recovery patterns**.

### Shock Types

| Disaster Type | Impact | Recovery Time | Pattern |
|--------------|--------|---------------|---------|
| **Pandemic** | -70% arrivals | 4-5 years | Double-dip first, then S-curve |
| **Volcano** | -4% per $1B damage | 1 year | S-curve |
| **Wildfire** | -0.03% per $1B damage | 6 months | Linear |
| **Flood** | -0.007% per 1K deaths | 6 months | Linear |
| **Conflict** | -30% to -50% | 2-8 years | S-curve |

### Why Hybrid Recovery?

**Years 0-2**: Double-dip pattern
- People afraid to travel
- Tentative return, setbacks

**Years 2+**: S-curve
- Confidence builds
- Rapid recovery, then plateaus

**Formula**:
```python
if years_since_shock < 2.0:
    recovery = double_dip_pattern()
else:
    recovery = 100 / (1 + exp(-0.8 × (years - 2.5)))  # S-curve
```

---

## 5. Network Effects: What We Learned

**Key Finding**: Popular destinations become **MORE popular** (rich-get-richer), but with **diminishing returns**.

### The Mechanism

```
Destination gets popular 
  → More people talk about it 
    → More people visit 
      → Even more popular
```

### But: We Use LOG-Scale

**Prevents winner-take-all**:

| Destination | Annual Arrivals | Popularity Bonus (θ=0.25) |
|-------------|-----------------|---------------------------|
| France | 82M | +0.235 |
| Thailand | 40M | +0.223 |
| Maldives | 1.7M | +0.095 |
| Bhutan | 0.3M | +0.070 |

**Why Log-Scale?**:
- Prevents one destination from dominating everything
- Allows smaller destinations to compete on other factors (cost, attractions)
- Matches real-world observation: new destinations emerge even while established ones grow

**Formula**:
```python
popularity_index = log(previous_period_arrivals + 1) / log(max_arrivals + 1)
utility += θ × popularity_index
```

---

## 6. What We DON'T Know (Honest Gaps)

### Critical Admission

Our main attractiveness measure (TTDI) only explains **13% of real tourism patterns**.

```
TTDI correlation: r = 0.364
R-squared: 0.13
Interpretation: 87% of variation comes from factors NOT in our model
```

### Missing Factors

- ❌ Cultural/linguistic affinity
- ❌ Flight network connectivity
- ❌ Visa policy/accessibility
- ❌ Colonial/historical ties
- ❌ Marketing/advertising spend

### Our Response

1. Frame simulation as **exploration tool**, NOT prediction
2. Let users adjust uncertain parameters
3. Focus on "does this look realistic?" not "does this predict exact numbers?"

---

## 7. User Configuration: What We're Doing

### Key Design Decision

**Turn unknowns into experimentation features.**

### Users Can Adjust

| Parameter | Default Range | What It Controls |
|-----------|--------------|------------------|
| Segment shares | 5-50% each | What % of tourists are Budget/Luxury/etc. |
| Distance sensitivity (η) | 0.15-0.45 | How much does distance matter? |
| Popularity weight (θ) | 0.10-0.40 | How much do trends matter? |
| Capacity threshold | 60-95% | When does overtourism start? |
| Recovery speed | 0.5-2.0 years | How fast do destinations recover? |
| Softmax temperature (τ) | 0.1-5.0 | How deterministic are choices? |

### Why This Approach?

- We don't know the "right" values
- Different scenarios need different assumptions
- Users can test "what if luxury travel doubles?" or "what if people become more risk-averse?"

---

## 8. Validation: How We'll Know It Works

### 4-Tier Validation Plan

#### Tier 1 (Must Pass) - Aggregate Metrics

| Metric | Target | Acceptable Range | Real Value |
|--------|--------|------------------|------------|
| CAGR (2010-2019) | 3.69% | 3.0-4.5% | 3.69% |
| Pandemic shock (2020) | -70.6% | -65% to -75% | -70.6% |
| Recovery (2024) | 94.5% | 90-100% | 94.5% |

#### Tier 2 (Should Pass) - Distributional Metrics

| Metric | Target | Acceptable Range | Real Value |
|--------|--------|------------------|------------|
| Gini coefficient | 0.71 | 0.60-0.80 | 0.71 |
| Top 10 share | 48% | 40-60% | 48% |
| Intra-regional (Europe) | 65% | 55-75% | 65% |

#### Tier 3 (Nice to Have) - Emergent Patterns

- ✅ Hub formation (popular destinations stay popular)
- ✅ Regional clustering (nearby countries have similar patterns)
- ✅ Congestion spillover (when hubs get crowded, tourists go elsewhere)
- ✅ Rich-get-richer dynamics (log-scale popularity)

#### Tier 4 (Sensitivity Tests) - Robustness

- Change parameters ±50%, check if model stays stable
- No crashes, no extreme outputs
- Reasonable behavior across parameter ranges

---

## 9. What's Still Uncertain (Before We Start)

### Unresolved Questions

1. **Utility weights**: Are our segment defaults (Budget=30%, Luxury=20%, etc.) reasonable, or should we just show ranges?

2. **Carrying capacity**: We have good hotel data but rough guesses for infrastructure/attractions. Should we simplify to just 2 subsystems?

3. **Correlations**: Our current correlations pool all countries/years together. Should we compute within-country correlations instead?

4. **Seasonality**: We have hemisphere-based patterns, but should we add 4 climate zones (Mediterranean, Tropical, Temperate, etc.)?

5. **Primary purpose**: Are we building this to **validate against history** or to **explore future scenarios**? (Both? But which is priority?)

---

## Summary: What We're Building

### A Simulation Where...

- ✅ Tourist agents with home countries choose destinations
- ✅ Based on 8 factors (attractiveness, cost, distance, popularity, etc.)
- ✅ With segment-specific preferences (Budget cares about cost, Luxury cares about quality)
- ✅ Destinations have capacity limits (4 subsystems, bottleneck approach)
- ✅ Shocks reduce arrivals (type-specific magnitudes)
- ✅ Recovery follows patterns (hybrid: double-dip + S-curve)
- ✅ Popular destinations get more popular (log-scale, not winner-take-all)
- ✅ Users can adjust uncertain parameters to test scenarios

### What It's Good For

- ✅ "What if" experiments (e.g., "What if budget travel doubles?")
- ✅ Understanding emergent patterns (hub formation, overtourism)
- ✅ Exploring plausible dynamics
- ✅ Scenario exploration with plausibility validation

### What It's NOT Good For

- ❌ Predicting exact tourist numbers
- ❌ Forecasting future trends
- ❌ Policy recommendations without further calibration
- ❌ Replacing econometric forecasting models

---

## Next Steps: Stage 2 Implementation

### Phase 1 (Week 1-2): Minimal Viable Simulation

- Country-level granularity (177 destinations)
- Business/Personal segments (data-backed)
- 8-factor utility function
- Origin-destination structure
- Multi-subsystem capacity
- Shock/recovery dynamics

### Phase 2 (Week 3-4): Enhanced Features

- 4 user-configurable segments
- Popularity feedback (rich-get-richer)
- Seasonality (4 climate zones)
- Interactive dashboard (Streamlit)
- Validation tests (4-tier framework)

### Phase 3 (Stage 3): Advanced Features

- City-level granularity (top 50 destinations)
- Full network effects (not just popularity proxy)
- Supply-side dynamics (marketing, investment)
- Policy interventions (visa, tourism taxes)

---

**Document Status**: Ready for Stage 2 implementation  
**Last Updated**: 2026-04-17  
**Owner**: Simulation Development Team
