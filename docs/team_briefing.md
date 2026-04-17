# Global Tourism Simulation - Team Briefing

**Date**: 2026-04-17  
**Stage**: Stage 1 Complete ✅ → Ready for Stage 2 (Simulation Development)  
**Data Coverage**: 177 countries, 30 years (1995-2024), 8,911 observations

---

## Executive Summary

We have successfully compiled and analyzed **8 comprehensive datasets** and **9 academic papers** to create a data-driven foundation for simulating complexity in global tourism. The analysis reveals strong empirical support for our agent-based approach, with **destination attractiveness (TTDI)** showing a **moderate positive correlation (r=0.364)** with tourist arrivals.

**Key Achievement**: Created a single source of truth (`tourism_comprehensive_1995_2024.csv`) merging UN Tourism, OECD, WEF, ACLED, WHO, Numbeo, and UNESCO data.

**Critical Innovation**: Designed **user-configurable tourist segments** - turning our biggest data gap into an experimentation feature where users can test "what-if" scenarios about tourist behavior.

---

## 1. What We Have: Data & Literature Inventory

### Primary Datasets (8 Sources)

| Dataset | Coverage | Records | Status | Key Metrics |
|---------|----------|---------|--------|-------------|
| **UN Tourism** | 215 countries, 1995-2024 | 163,656 | ✅ Complete | Arrivals, expenditure, purpose split (11%/89%) |
| **WEF TTDI** | 119 countries, 2024 | 119 | ✅ Extracted | Attractiveness scores (2.78-5.24) |
| **OECD** | 55 countries, 2008-2023 | ~30,000 | ✅ Complete | GDP share, nights spent |
| **ACLED** | Global, 1997-2026 | ~978,000 events | ✅ Complete | Conflict events, fatalities |
| **WHO Air Quality** | Global, 1990-2021 | 6,603 | ✅ Complete | PM2.5 concentrations |
| **Numbeo Cost** | 156 countries, 2024 | 156 | ✅ Complete | Cost indices (26.6-135.8) |
| **UNESCO** | 60 countries, 2024 | 60 | ✅ Complete | Heritage site counts |
| **World Bank** | 39 countries, 2010-2024 | ~80 | ✅ Complete | Political stability |

### Academic Literature (9 Papers)

| Paper | Citations | Key Contribution | Validation Status |
|-------|-----------|------------------|-------------------|
| **Rosselló et al. (2020)** | 438 | Natural disaster elasticities | ✅ Validates shock magnitudes |
| **Škare et al. (2021)** | 882 | COVID-19 impact analysis | ✅ Validates -70% shock, hybrid recovery |
| **Bertocchi et al. (2020)** | 140 | Venice carrying capacity model | ✅ Validates multi-subsystem capacity |
| **Peng et al. (2014)** | 195 studies | Business/leisure elasticities | ✅ Validates price sensitivity differences |
| **Litvin et al. (2018)** | N/A | eWOM mechanisms | ✅ Validates network effects importance |
| **Leung et al. (2021)** | 149 studies | Social media causal framework | ✅ Validates UGC influence |
| **Sönmez & Graefe (1998)** | N/A | Memory/return visitor patterns | ✅ Validates 0.55-0.65 return probability |
| **Woodside & Lysonski (1989)** | 1,150 | Destination choice theory | ✅ Validates utility-based choice |
| **Seddighi & Theocharous (2002)** | 382 | Choice model empirical test | ✅ Validates softmax mechanism |

### Merged Dataset

**File**: `data/merged/tourism_comprehensive_1995_2024.csv`

**Dimensions**: 8,911 records × 14 variables  
**Coverage**: 177 countries, 1995-2024  
**Completeness**:
- Tourist arrivals: 100%
- TTDI scores: 98.0%
- Risk scores: 100%
- Cost indices: 99.6%
- Air quality: 72.7%

---

## 2. Key Findings: Correlations & Facts

### Baseline Growth Patterns

| Metric | Value | Confidence |
|--------|-------|------------|
| Pre-pandemic CAGR (2010-2019) | **3.69%** | **HIGH** (UN Tourism data) |
| Growth volatility (σ) | 8.52% | **HIGH** |
| Pandemic shock (2020) | **-70.6%** | **HIGH** |
| Recovery (2024) | **94.5%** of 2019 | **HIGH** |
| Fully recovered countries | 42.9% | **HIGH** |

### Correlation Analysis (2019-2024)

**Factors correlated with tourist arrivals:**

| Factor | Correlation | Strength | Interpretation |
|--------|-------------|----------|----------------|
| Tourism expenditure | **+0.642** | Strong | Validates data quality |
| TTDI attractiveness | **+0.364** | Moderate | **Primary driver (but only 13% variance explained)** |
| Air quality | +0.049 | Weak | Secondary factor |
| Affordability | -0.041 | Very weak | Quality > price for most |
| Risk score | -0.089 | Weak | Modest negative effect |

**Critical Limitation**: TTDI r² = 0.13 → **87% of variance unexplained**

**Missing Factors** (addressed in model design):
- ✅ Geographic proximity → Added as distance friction term
- ✅ Popularity feedback → Added as endogenous rich-get-richer
- ⚠️ Flight connectivity → Proxy via distance + GDP
- ❌ Cultural/linguistic affinity → Future enhancement
- ❌ Visa policy → Future enhancement

**Key Insight**: Attractiveness (TTDI) is the strongest predictor **in our dataset**, but geographic and network factors are equally important in reality. Model now includes both.

### Regional Flow Patterns (UN Tourism)

| Home Region | Intra-regional % | Primary Extra-regional |
|-------------|-----------------|------------------------|
| Europe | 65% | Americas (20%) |
| Americas | 55% | Europe (30%) |
| Asia-Pacific | 55% | Europe (25%) |
| Africa | 45% | Europe (35%) |
| Middle East | 40% | Europe (35%) |

**Implication**: Strong regional clustering → modeled via origin-destination structure

### Business vs. Leisure Travel (UN Tourism + Literature)

| Metric | Business | Leisure | Ratio |
|--------|----------|---------|-------|
| Share of travel | **11.2%** | **88.8%** | - |
| Price elasticity | **-0.350** | **-1.102** | 3.15x |
| Income elasticity | **1.605** | **2.401** | 1.49x |

**Implication**: Business travelers are 3x less price-sensitive than leisure travelers

### Natural Disaster Impacts (Rosselló et al., 2020)

| Disaster Type | Impact | Duration |
|--------------|--------|----------|
| Volcanic eruption | -3.4% to -4.5% per $1B cost | 12 months |
| Wildfire | -0.035% per $1B cost | 6 months |
| Flood | -0.007% per 1,000 deaths | 6 months |
| Tsunami | -0.09% per million affected | 12 months |

### Carrying Capacity Insights (Bertocchi et al., 2020)

**Multi-Subsystem Model** (7 subsystems identified):
1. Hotel beds
2. Alternative accommodation (Airbnb, B&B)
3. Restaurant capacity
4. Parking
5. Public transport
6. Waste disposal
7. Attractions (non-reproducible)

**Critical Finding**: Degradation is **LINEAR** (not quadratic), with bottleneck determined by minimum subsystem capacity.

### Memory & Return Visitors (Sönmez & Graefe, 1998)

- Past visitors are **3-5x more likely** to return
- Experience reduces risk avoidance by **23-44 percentage points**
- Return probabilities: 0.55-0.65 for familiar destinations

---

## 3. Inferred Rules for Simulation

### Utility Function (Literature-Backed)

```
U(destination) = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk + ε·SocialMedia + ζ·Memory
```

**Segment-Specific Weights** (user-configurable defaults):

| Segment | α (Attract) | β (Cost) | γ (Crowd) | δ (Risk) | ε (Social) | ζ (Memory) |
|---------|-------------|----------|-----------|----------|------------|------------|
| **Budget** | 0.20 | 0.50 | 0.15 | 0.15 | 0.30 | 0.55 |
| **Luxury** | 0.50 | 0.15 | 0.15 | 0.20 | 0.50 | 0.65 |
| **Adventure** | 0.40 | 0.20 | 0.10 | 0.30 | 0.35 | 0.60 |
| **Family** | 0.30 | 0.30 | 0.25 | 0.15 | 0.45 | 0.65 |

**Purpose Modifier** (Peng et al. elasticities):
- Business travel: β (cost weight) × 0.3
- Personal travel: No modification

### Decision Mechanism

**Probabilistic Choice** (Softmax - Woodside & Lysonski, 1989):
```python
P(choose destination i) = exp(U_i / τ) / Σ_j exp(U_j / τ)
```
where τ = 1.0 (temperature parameter controlling randomness)

### Dynamic Parameters

**Shock Types**:
```python
SHOCK_TYPES = {
    'pandemic': {'magnitude': -0.70, 'recovery': 'hybrid'},
    'volcano': {'elasticity': -0.04, 'recovery': 's_curve'},
    'wildfire': {'elasticity': -0.00035, 'recovery': 'linear'},
    # ...
}
```

**Recovery Function** (hybrid model):
- Years 0-2: Double-dip pattern (Škare et al.)
- Years 2+: S-curve (fits 2020-2024 data)
- Natural disasters: Linear recovery (6-12 months)

**Carrying Capacity** (Bertocchi-inspired):
```python
capacity = min(
    accommodation_capacity,
    transport_capacity,
    infrastructure_capacity,
    attraction_capacity
)
```

**Crowding Degradation** (LINEAR, not quadratic):
```python
if arrivals > 0.8 × capacity:
    degradation = γ × (arrivals/capacity - 0.8)
```

---

## 4. Critical Design Decisions

### ✅ What's Empirically Validated

| Component | Evidence | Confidence |
|-----------|----------|------------|
| Baseline growth (3.69% CAGR) | UN Tourism 2010-2019 | **HIGH** |
| Pandemic shock (-70%) | UN Tourism 2020 | **HIGH** |
| Recovery pattern (S-curve) | UN Tourism 2024 fit | **HIGH** |
| TTDI as attractiveness | WEF 2024 (119 countries) | **HIGH** |
| Business/Personal split (11%/89%) | UN Tourism purpose data | **HIGH** |
| Business less price-sensitive | Peng et al. meta-analysis | **HIGH** |
| Multi-subsystem capacity | Bertocchi et al. | **HIGH** |
| Linear degradation | Bertocchi et al. | **HIGH** |
| Return visitor probability (0.55-0.65) | Sönmez & Graefe | **HIGH** |
| Utility-based choice | Woodside & Lysonski, Seddighi & Theocharous | **HIGH** |
| Softmax mechanism | Seddighi & Theocharous empirical test | **HIGH** |

### ⚠️ What's User-Configurable (No Empirical Basis)

| Parameter | Why Configurable | Default |
|-----------|------------------|---------|
| Segment population shares | No literature found | 30/20/25/25 |
| Trip frequency by segment | No empirical data | 0.75-3.0 trips/yr |
| Social media sensitivity | Literature provides framework, not values | 0.30-0.50 |
| 80% capacity threshold | Bertocchi's 80% was excursionist rate, not threshold | 0.80 (user-adjustable) |

**Design Philosophy**: Turn assumptions into **experimentation parameters** - users can test how different segment configurations affect global tourism patterns.

---

## 5. Simulation Architecture

### Agent Types

**Tourist Agents** (heterogeneous):
- Segment membership (Budget/Luxury/Adventure/Family - user-configurable)
- Travel purpose (Business/Personal - 11%/89% from data)
- Memory of past visits (return probability 0.55-0.65)
- Social media sensitivity (0.30-0.50)

**Destination Agents** (countries):
- Attractiveness (TTDI score, dynamic)
- Multi-subsystem capacity
- Risk perception (from ACLED data)
- Recovery dynamics (shock-type-specific)

### Time Granularity

**Monthly timesteps** (recommended):
- Captures seasonality (±20% amplitude, literature-based)
- Aligns with booking patterns
- Allows shock propagation modeling

### Spatial Granularity

**Country-level** (177 destinations):
- Matches data availability
- Computationally tractable
- Policy-relevant (national interventions)

**Future enhancement**: City-level for top 50 destinations

---

## 6. Validation Strategy

### Historical Fit Tests

| Metric | Target | Acceptable Range | Data Source |
|--------|--------|------------------|-------------|
| Growth rate (2010-2019) | 3.69% CAGR | 3.0-4.5% | UN Tourism |
| Shock magnitude (2020) | -70.6% | -65% to -75% | UN Tourism |
| Recovery (2024) | 94.5% of 2019 | 90-100% | UN Tourism |
| TTDI correlation | r = 0.364 | r = 0.30-0.45 | Our analysis |
| Business/Personal split | 11%/89% | 8-14% / 86-92% | UN Tourism |

### Emergent Patterns to Reproduce

1. ✅ **Recovery curves** (S-shaped post-crisis)
2. ⚠️ **Seasonal oscillation** (±20%, literature-based)
3. ✅ **Hub formation** (preferential attachment via utility)
4. ⚠️ **Cascading effects** (crisis redirects flow)
5. ✅ **Carrying capacity limits** (linear degradation)

---

## 7. Open Questions & Limitations

### Known Gaps

| Gap | Impact | Mitigation |
|-----|--------|------------|
| No city-level data | Cannot model sub-national dynamics | Country-level for Stage 2 |
| No monthly seasonality data | Cannot calibrate seasonal patterns | Literature estimate (±20%) |
| No segment behavior data | Cannot validate 4 segments | User-configurable, calibrate from correlations |
| No network effect elasticities | Cannot quantify WOM impact | User-configurable, sensitivity analysis |

### Design Decisions Needed

1. **Segment configuration**: Presets + custom, or fully open?
2. **Parameter ranges**: Constrain to literature bounds, or allow full exploration?
3. **Validation mode**: Compare simulation output to real data automatically?
4. **Network effects**: Include in Stage 2, or defer to Stage 3?

---

## 8. Next Steps

### Immediate (Week 1-2): Phase 1 Implementation

**Minimal Viable Simulation**:
- ✅ 177 countries with real data (TTDI, cost, risk)
- ✅ Business/Personal segments (data-backed)
- ✅ Utility-based choice (softmax)
- ✅ Baseline growth (3.69% CAGR)
- ✅ Pandemic shock (-70%) + hybrid recovery
- ✅ Multi-subsystem capacity (4 subsystems)
- ✅ Linear crowding degradation

**Expected emergent patterns**: Recovery curves, hub formation, capacity limits

### Short-Term (Week 3-4): Phase 2 Enhancements

**Add Complexity**:
- ⚠️ 4 segments (user-configurable, calibrate from correlations)
- ⚠️ Segment-specific trip frequencies
- ⚠️ Cascading effects (risk perception updates)
- ⚠️ Seasonality (±20%)
- ⚠️ Social media/WOM effects (user-configurable)

**Expected emergent patterns**: Seasonal oscillation, cascading effects

### Medium-Term (Stage 3): Advanced Features

**Nice-to-Have**:
- 📋 City-level granularity (top 50 destinations)
- 📋 Medical/Pilgrimage/Education sub-segments
- 📋 Network effects (calibrated from data)
- 📋 Agent memory/learning (beyond simple return probability)

---

## 9. Files to Reference

| File | Location | Purpose |
|------|----------|---------|
| **Merged Dataset** | `data/merged/tourism_comprehensive_1995_2024.csv` | Single source of truth |
| **Data Dictionary** | `docs/data_dictionary.md` | Variable definitions |
| **Sources Log** | `data/SOURCES_LOG.md` | Data provenance |
| **Inferred Rules** | `docs/inferred_rules.md` | Behavioral rules (updated v2.0) |
| **Literature Review** | `docs/literature_review_summary.md` | Paper findings |
| **Literature PDFs** | `docs/literature_pdfs/` | 8 reviewed papers |
| **Correlation Matrix** | `data/merged/correlation_matrix.csv` | Variable relationships |

---

## 10. Success Criteria

### Stage 1 (Data Analysis) - ✅ Complete

- [x] Data collected from 8+ sources (163,656 records)
- [x] Literature reviewed (9 academic papers)
- [x] Merged dataset created (8,911 records)
- [x] Correlation analysis completed
- [x] Inferred rules documented (v2.0)
- [x] Data dictionary created
- [x] Team briefing prepared

### Stage 2 (Simulation) - In Progress

**Phase 1 (Week 1-2)**:
- [ ] Working agent-based model (country-level)
- [ ] Utility-based destination choice
- [ ] Baseline growth validated (3.69% CAGR)
- [ ] Shock/recovery dynamics implemented

**Phase 2 (Week 3-4)**:
- [ ] User-configurable segments
- [ ] Multi-subsystem capacity
- [ ] Social media/WOM effects
- [ ] Interactive visualization (Streamlit)

---

## 11. Team Discussion Points

### For Next Meeting

1. **Segment configuration approach**: 
   - Presets (Budget/Luxury/Adventure/Family)?
   - Fully custom (users define segments)?
   - Hybrid (presets + customization)?

2. **Validation priorities**:
   - Which metrics are most important to match?
   - What's "good enough" fit to real data?

3. **Scope decisions**:
   - City-level: Stage 2 or Stage 3?
   - Network effects: Include now or defer?

4. **Timeline**:
   - Phase 1 completion target?
   - Demo readiness?

---

**Contact**: For questions about data or analysis, refer to:
- `docs/data_dictionary.md` - Variable definitions
- `docs/inferred_rules.md` - Behavioral rules
- `data/SOURCES_LOG.md` - Data sources

**Last Updated**: 2026-04-17  
**Status**: Ready for Stage 2 implementation
