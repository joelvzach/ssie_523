# Progress Report: Global Tourism Complexity Simulation

**Project**: SSIE 523 - Agent-Based Modeling of Global Tourism Dynamics  
**Date**: April 21, 2026  
**Status**: Foundation Complete ✅ | Development Phase Ready to Begin  

---

## Executive Summary

We are building an **agent-based simulation** that captures the complexity of global tourism flows. The model enables scenario testing and "what-if" analysis for tourism dynamics—from pandemic recovery to overtourism policy responses.

**Value Proposition**: A sandbox for exploring tourism system behavior under different conditions, grounded in real-world data from 177 countries over 30 years.

**Development Status**: Stage 1 (data & literature) complete. Stage 2 (simulation development) design finalized, ready for implementation.

---

## What We've Accomplished

### 1. Comprehensive Data Foundation

We've assembled and merged **7 major datasets** into a single source of truth:

| Data Source | Coverage | Application |
|-------------|----------|-------------|
| UN Tourism Arrivals | 215 countries, 1995-2024 | Baseline calibration & validation |
| WEF Tourism Competitiveness (TTDI) | 119 countries | Destination attractiveness scoring |
| ACLED Conflict Events | Global, 1997-2026 | Risk perception modeling |
| Numbeo Cost of Living | 156 countries | Affordability factor |
| OECD Economic Indicators | 55 countries | Economic context |
| WHO Air Quality | Global | Environmental quality |
| UNESCO Heritage Sites | 60 countries | Cultural appeal |

**Result**: 8,911 country-year observations forming the empirical backbone of the simulation.

### 2. Key Empirical Insights

Our analysis of 30 years of tourism data reveals:

| Finding | Value | Implication |
|---------|-------|-------------|
| Pre-pandemic growth (CAGR 2010-2019) | **3.69%** | Baseline growth trajectory |
| Pandemic shock (2020) | **-70.6%** | Stress-test magnitude |
| Recovery status (2024) | **94.5%** of 2019 levels | Hybrid recovery pattern |
| Business vs. Leisure split | **11% / 89%** | Segment calibration anchor |
| Regional clustering (Europe) | **65%** intra-regional | Geographic friction matters |

### 3. Academic Literature Integration

We've reviewed and integrated findings from **6 peer-reviewed papers** (combined 2,500+ citations):

| Concept | Academic Source | Model Implementation |
|---------|-----------------|---------------------|
| Destination choice | Woodside & Lysonski (1989) | Utility-based decision model |
| Carrying capacity | Bertocchi et al. (2020) | Multi-subsystem capacity with linear degradation |
| Crisis recovery | Škare et al. (2021) | Hybrid recovery: double-dip + S-curve |
| Price elasticity | Peng et al. (2014) | Segment-specific cost sensitivity |
| Return visitors | Sönmez & Graefe (1998) | Memory-based loyalty mechanism |
| Overtourism thresholds | Muler González et al. (2018) | 80% capacity triggers policy response |

### 4. Additional Modules Complete

| Module | Status | Description |
|--------|--------|-------------|
| Visa Restrictions | ✅ Complete | 192 country pairs, 6 restriction levels (VISA_FREE → BANNED) |
| Country Centroids | ✅ Complete | 177 countries, lat/long for distance calculation |
| TFI Dynamics | ✅ Specified | Tourism Friendliness Index models resident attitudes → policy feedback |
| Documentation | ✅ Complete | 10+ files (PRD, literature review, parameters, validation, progress reports) |

---

## Model Design: Finalized Specifications

### Core Mechanism: 6-Factor Utility Function

Each tourist agent evaluates destinations using:

```
U = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk - η·Distance + ζ·Memory
    + EventBonus - VisaFriction
```

| Factor | What It Captures | Data Source | Empirical Support |
|--------|------------------|-------------|-------------------|
| **Attractiveness** | Infrastructure, natural/cultural resources | WEF TTDI | Woodside & Lysonski (1989) |
| **Cost** | Affordability for the traveler | Numbeo Index | Peng et al. (2014) elasticities |
| **Crowding** | Overtourism avoidance | Hotel capacity data | Bertocchi et al. (2020) |
| **Risk** | Safety/security concerns | ACLED conflict data | Rosselló et al. (2020) |
| **Distance** | Geographic friction (travel effort) | Haversine calculation | Gravity model literature |
| **Memory** | Return visitor loyalty | Agent history | Sönmez & Graefe (1998) |

### Tourist Segments

Four configurable segments with distinct preferences:

| Segment | Population Share | Trips/Year | Business % | Primary Focus |
|---------|------------------|------------|------------|---------------|
| **Budget** | 30% | 0.75 | 15% | Cost-sensitive, shorter stays |
| **Luxury** | 20% | 3.0 | 40% | Quality-focused, longer stays |
| **Adventure** | 25% | 1.5 | 5% | Risk-tolerant, remote destinations |
| **Family** | 25% | 0.75 | 0% | Safety-conscious, predictable outcomes |

**Business Travel**: Embedded within segments (not separate), producing ~11% business travel overall.

### Dynamic Feedback Loops

1. **Overtourism Response**: When destinations exceed 80% capacity, resident attitudes decline → policy restrictions activate → effective capacity reduces
2. **Memory Effect**: Past visitors 3-5× more likely to return (creates destination loyalty)
3. **Shock & Recovery**: Crises trigger segment-specific responses; recovery follows empirically-observed patterns (hybrid: double-dip + S-curve)
4. **Seasonal Modulation**: 3 climate zones (Northern/Southern/Tropical) with ±20% amplitude

### Trip Frequency Model

- **Poisson process**: Each agent has daily probability of starting a trip (based on segment trips/year)
- **Seasonal modulation**: Month-specific multipliers by climate zone
- **Event influence**: Planned events (e.g., FIFA World Cup) pull trips forward via utility bonus
- **Stay duration**: Segment base × distance modifier (80% follow trend: farther = longer stays)

---

## Development Roadmap

### Phase 1: Core Simulation
- Tourist agent class with state machine (HOME → CHOOSING → TRAVELING → RETURNING)
- Destination class with capacity tracking and TFI dynamics
- Utility function implementation (6 factors + softmax choice)
- Distance matrix pre-computation (31K pairs, O(1) lookup)
- Data collector (aggregate/segment/destination metrics + 100-agent sample)
- Historical validation (CAGR, pandemic shock, recovery targets)

### Phase 2: Events & Scenarios
- Seasonal patterns (3 climate zones, latitude-based assignment)
- Planned events interface (user input: FIFA World Cup example)
- Unplanned event triggers (disasters, terrorism, epidemics)
- Shock/recovery dynamics (hybrid model)
- Trip record tracking (arrival/departure dates)

### Phase 3: Interactive Dashboard
- Streamlit-based visualization (hybrid layout: map 60% + charts 40%)
- Plotly world map (choropleth + 100-agent animated sample)
- Real-time controls (pause/play, speed: 0.5×/1×/2×/4×)
- Side panel charts (time series, top 10 destinations, segment breakdown, origins pie)
- Click inspection (agent details: ID/segment/home; destination details: capacity%/visitors/TFI/origins)
- Scenario save/load (JSON config + seed for deterministic replay)

### Phase 4: Validation & Refinement
- 4-tier validation framework (aggregate, distributional, emergent, sensitivity)
- Performance optimization (target: 4,000 agents, <1s/timestep)
- Documentation (README, inline docstrings, user guide)

---

## Validation Approach

The model will be validated against three historical benchmarks:

| Metric | Target Range | Observed Value |
|--------|--------------|----------------|
| Growth Rate (2010-2019) | 3.0-4.5% CAGR | 3.69% |
| Pandemic Shock (2020) | -65% to -75% | -70.6% |
| Recovery Status (2024) | 90-100% of 2019 | 94.5% |

**Additional Validation Tiers** (Phase 4):
- Distributional: Gini coefficient, top 10 share, intra-regional flows
- Emergent: Hub formation, regional clustering, congestion spillover
- Sensitivity: Parameter robustness tests (±20% variations)

---

## Technical Architecture

### Data Collection Strategy

| Metric Category | Frequency | Details |
|-----------------|-----------|---------|
| **Aggregate** | Every tick | Global arrivals, active travelers |
| **Segment-level** | Every tick | Arrivals by segment, avg stay duration |
| **Destination-level** | Every tick | Visitors, capacity utilization, TFI trajectory |
| **Agent sample** | Every tick | 100-agent trajectories (animated on map) |
| **Trip records** | On event | All trips: agent_id, origin, dest, arrival, departure, segment |

### Simulation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Agent population | 4,000 | Balance between realism and performance |
| Destination choice set | Top 50 countries | Covers ~90% of global flows |
| Timestep granularity | 1 tick = 1 day | Fine-grained for animation |
| Distance matrix | Pre-computed (31K pairs) | O(1) lookup, ~0.1s startup |
| Capacity basis | Hotel beds × 0.80 × 1.10 | Bertocchi assumption + 10% non-hotel buffer |
| Climate zones | 3 (Northern/Southern/Tropical) | Latitude-based assignment |
| Save format | Config + seed | Deterministic replay with tweak capability |

### Visualization Approach

- **Map library**: Plotly (WebGL, interactive, Streamlit-compatible)
- **Agent display**: Aggregated circles (default) + 100-agent animation overlay
- **Layout**: Hybrid (map 60% + side panel 40% with charts + details)
- **Charts**: Time series (global arrivals), bar chart (top 10), stacked area (by segment), pie chart (visitor origins)

---

## Use Cases

Once complete, the simulation enables:

1. **Scenario Exploration**: "What if luxury travel doubles?" "What if a disaster hits Country X?"
2. **Policy Testing**: Evaluate overtourism interventions (visitor caps, tourist taxes)
3. **Stress Testing**: Assess system resilience to shocks (pandemic, conflict, natural disaster)
4. **Research**: Study emergent patterns (hub formation, cascading failures, recovery dynamics)
5. **Education**: Demonstrate complexity in global tourism flows

---

## Technical Specifications

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Framework | Custom agent-based (optimized for this use case) |
| Dashboard | Streamlit |
| Visualization | Plotly (interactive choropleths + scatter) |
| Data Processing | pandas, numpy |
| Save Format | JSON (config + seed) |

**Performance Target**: 4,000 tourist agents, 177 countries, <1 second per timestep

---

## Known Limitations (Transparent Documentation)

| Limitation | Mitigation |
|------------|------------|
| TTDI explains only 13% variance | Frame as exploration tool, not prediction |
| Segment shares assumed (30/20/25/25) | User-configurable in dashboard |
| City-level not modeled | Only country-level data available |
| No flight network | Distance friction + visa restrictions as proxies |
| Social media factor | Removed (no empirical data); may add in Stage 3 |

---

## Next Steps

**Immediate**: Begin Phase 1 implementation

1. Create directory structure (modular: agents/, destinations/, mechanics/, dynamics/, data/, validation/)
2. Implement tourist agent class (state machine, trip frequency, memory)
3. Implement destination class (capacity, TFI dynamics, crowding calculation)
4. Implement utility function (6 factors, segment weights, softmax choice)
5. Implement distance matrix (pre-compute 31K pairs)
6. Implement simulation loop (daily timesteps, data collection)
7. Run Tier 1 validation tests (CAGR, pandemic, recovery)

**Upon Phase 1 Completion**: Iterative validation against historical benchmarks, followed by events system (Phase 2) and dashboard development (Phase 3).

---

## Questions?

This is an exploratory tool designed to illuminate system dynamics—not a forecasting model. The simulation makes uncertainty explicit and enables structured experimentation with tourism system behavior.

**All design decisions documented** in `docs/` folder (PRD.md, literature_parameters.md, inferred_rules.md, validation_metrics.md, progress_report.md).

**Next Review**: Phase 1 validation results

---

**Prepared by**: Simulation Development Team  
**Project Repository**: `/Users/joelvzach/Code/ssie_523`
