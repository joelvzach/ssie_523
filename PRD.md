# Project Requirements Document (PRD)
## Global Tourism Complexity Simulation

**Version**: 2.0 (Stage 2 Ready)  
**Last Updated**: 2026-04-17  
**Status**: Stage 1 Complete ✅, Stage 2 Ready

---

## 1. Project Overview

Build an agent-based simulation to demonstrate complexity in global tourism, where tourist agents make destination choices based on multiple factors (attractiveness, affordability, crowding, risks, **distance, popularity**), leading to emergent patterns.

**Enhanced Scope (v2.0)**:
- ✅ Origin-destination structure (tourists have home countries)
- ✅ Geographic friction (distance decay in destination choice)
- ✅ Network effects (popularity feedback, rich-get-richer)
- ✅ Regional clustering (realistic flow patterns)
- ✅ User-configurable segments (experimentation tool)

**Current Status**: Stage 1 Complete ✅  
**Last Sprint**: Comprehensive data integration, literature review, geographic & network effects added

---

## 2. Project Stages

### Stage 1: Data Analysis ✅ COMPLETE

**Goal**: Analyze global tourism data to infer behavioral rules for simulation

**Status**: ✅ COMPLETE - 8 datasets integrated, 9 papers reviewed, v2.0 rules documented

**Deliverables**:
- [x] Statistical summary report (Python-based EDA)
- [x] Inferred rules document (`docs/inferred_rules.md` v2.0)
- [x] Data source log (`data/SOURCES_LOG.md` v2.0)
- [x] Data dictionary (`docs/data_dictionary.md` v2.0)
- [x] Team briefing (`docs/team_briefing.md` v2.0)
- [x] Validation metrics (`docs/validation_metrics.md`)
- [x] Literature review (`docs/literature_review_summary.md`)
- [x] Literature parameters (`docs/literature_parameters.md` v2.0)
- [x] Merged dataset (`data/merged/tourism_comprehensive_1995_2024.csv`)
- [x] Country centroids (`data/derived/country_centroids.csv`)

**Data Sources Integrated**:
- ✅ UN Tourism (215 countries, 1995-2024, 163,656 records)
- ✅ WEF TTDI (119 countries, extracted from PDF)
- ✅ OECD (55 countries, 2008-2023)
- ✅ ACLED (global conflict, 1997-2026, ~978K events)
- ✅ WHO Air Quality (global, 1990-2021)
- ✅ Numbeo Cost of Living (156 countries, 2024)
- ✅ UNESCO Heritage Sites (60 countries, 2024)
- ✅ World Bank (39 countries, 2010-2024)

**Key Insights**:
- Pre-pandemic CAGR (2010-2019): **3.69%**
- Pandemic shock (2020): **-70.6%**
- Recovery (2024): **94.5%** of 2019 levels
- TTDI correlation: **r = 0.364** (but only 13% variance explained)
- Business/Personal split: **11%/89%** (UN Tourism purpose data)
- **NEW**: Regional flow patterns (65% intra-regional for Europe)
- **NEW**: Distance friction critical for realistic modeling
- **NEW**: Popularity feedback creates rich-get-richer dynamics

**Critical Limitation**: TTDI explains only 13% of variance (r² = 0.13). Model is **exploratory, not predictive**.

**Folder Structure**:
```
data/
├── UN_Tourism/        ✅ 12 CSV files (163,656 records)
├── WEF/               ✅ ttdi_scores_2024.csv (119 countries, extracted)
├── OECD/              ✅ 4 CSV files (~30K records)
├── ACLED/             ✅ 12 CSV files (~978K events)
├── enhanced_data/     ✅ WHO, Numbeo, UNESCO, World Bank
├── merged/            ✅ tourism_comprehensive_1995_2024.csv (8,911 records)
├── derived/           ✅ country_centroids.csv (177 countries)
└── SOURCES_LOG.md     ✅ v2.0
```

### Stage 2: Simulation Development (Ready to Start)

**Goal**: Build agent-based model using inferred rules (v2.0)

**Agent Type**: Tourists (individual agents with home countries)

**Enhanced Key Dynamics** (v2.0):
- **Origin-Destination Structure**: Each tourist has a home country
- **Geographic Friction**: Distance decay in destination choice
- **Network Effects**: Popularity feedback (rich-get-richer)
- **Regional Clustering**: Realistic flow patterns (65% intra-regional for Europe)
- Destination choice based on:
  - Attractiveness (TTDI score)
  - Affordability (cost index)
  - Crowding (multi-subsystem capacity, LINEAR degradation)
  - Risks (ACLED conflict, Rosselló coefficient)
  - **Distance** (great-circle distance, segment-specific weights)
  - **Popularity** (log-scale arrivals, endogenous feedback)
  - Social media (UGC quality/quantity)
  - Memory (return visitor probability)

**Deliverables**:
- [ ] Simulation code (Python/Mesa)
  - [ ] Agent classes (tourist agents with home countries)
  - [ ] Destination classes (multi-subsystem capacity)
  - [ ] Utility function (8 factors)
  - [ ] Softmax choice mechanism
  - [ ] Shock/recovery dynamics (hybrid model)
- [ ] Visualization of emergent patterns
  - [ ] Hub formation
  - [ ] Regional clustering
  - [ ] Congestion spillover
  - [ ] Rich-get-richer dynamics
- [ ] Validation against historical data
  - [ ] Tier 1: Aggregate metrics (CAGR, shock, recovery)
  - [ ] Tier 2: Distributional metrics (Gini, top 10 share)
  - [ ] Tier 3: Emergent patterns (qualitative)
  - [ ] Tier 4: Sensitivity tests
- [ ] Interactive dashboard (Streamlit)
  - [ ] User-configurable segments
  - [ ] Parameter tuning interface
  - [ ] Scenario exploration

**Implementation Plan**:
- **Phase 1 (Week 1-2)**: Minimal viable simulation (country-level, Business/Personal segments, baseline dynamics)
- **Phase 2 (Week 3-4)**: Enhanced features (4 segments, popularity feedback, seasonality, validation)
- **Phase 3 (Stage 3)**: Advanced features (city-level, network effects, marketing dynamics)

---

## 3. Success Criteria

### Data Analysis Stage ✅ COMPLETE

- [x] Data collected from 8 primary sources (163,656 records)
- [x] Literature reviewed (9 academic papers)
- [x] EDA with key insights (correlation analysis, regional patterns)
- [x] Documented rules for simulation parameters (v2.0)
- [x] Data quality assessment (completeness tables)
- [x] Merged dataset created (8,911 records, 177 countries)
- [x] Validation framework defined (4-tier metrics)
- [x] Team briefing prepared (v2.0)

### Simulation Stage (Stage 2)

**Phase 1 (Week 1-2) - Minimal Viable**:
- [ ] Working agent-based model (country-level)
- [ ] Origin-destination structure implemented
- [ ] Distance friction in utility function
- [ ] Popularity feedback (rich-get-richer)
- [ ] Baseline growth validated (3.69% CAGR)
- [ ] Shock/recovery dynamics (hybrid model)

**Phase 2 (Week 3-4) - Enhanced**:
- [ ] User-configurable segments (4 types + custom)
- [ ] Multi-subsystem capacity (4 subsystems)
- [ ] Social media/WOM effects
- [ ] Seasonality (±20% amplitude)
- [ ] Interactive visualization (Streamlit)
- [ ] Validation dashboard (real-time metrics)

**Phase 3 (Stage 3) - Advanced**:
- [ ] City-level granularity (top 50 destinations)
- [ ] Full network effects (not just popularity proxy)
- [ ] Supply-side dynamics (marketing, investment)
- [ ] Policy interventions (visa, tourism taxes)

**Validation Requirements**:
- **Tier 1 (Must Pass)**: CAGR 3.0-4.5%, Shock -65% to -75%, Recovery 90-100%
- **Tier 2 (Should Pass)**: Gini 0.60-0.80, Top 10 share 40-60%, Regional flows ±15%
- **Tier 3 (Nice to Have)**: Hub formation, regional clustering, congestion spillover

---

## 4. Open Questions

### Resolved ✅
1. **Tourist heterogeneity**: Yes, 4 segments (Budget, Luxury, Adventure, Family) with different weights
2. **Attractiveness modeling**: WEF TTDI scores (0-100 scale)
3. **Crowding**: Density-based (tourists/capacity), threshold at 80%
4. **Risk factors**: Composite score (0-1), critical threshold at 0.7

### Remaining ❓
1. **Time granularity**: Monthly vs yearly timestep? (Recommendation: monthly for seasonality)
2. **Capacity limits**: Hard cap or soft degradation of attractiveness?
3. **Network effects**: Include word-of-mouth dynamics in Stage 2 or later?
4. **Learning**: Should agents remember experiences across timesteps?

---

## 5. Technical Stack

### Data Analysis (Stage 1) ✅
- Python (pandas, numpy)
- Visualization (matplotlib, seaborn)
- Requests (API data collection)

### Simulation (Stage 2) - Proposed
- Python with Mesa (agent-based modeling framework)
- NetworkX for destination connectivity
- Streamlit for interactive visualization
- pytest for validation tests

---

## 6. File Structure

```
ssie_523/
├── PRD.md                      ✅ Living requirements doc
├── sources/                    ✅ Original bibliography
├── data/                       ✅ Collected data
│   ├── World_Bank/
│   ├── WEF/
│   ├── OECD/
│   ├── other/
│   ├── merged/
│   └── SOURCES_LOG.md
├── src/                        ✅ Code
│   ├── data_collection.py      ✅ World Bank API
│   ├── data_collection_additional.py  ✅ WEF, synthetic data
│   ├── eda_tourism.py          ✅ Exploratory analysis
│   └── analysis/output/        ✅ Generated visualizations
├── docs/                       ✅ Documentation
│   └── inferred_rules.md       ✅ Behavioral rules
└── simulation/                 📁 To be created (Stage 2)
```

---

*This is a living document. Update as the project evolves.*
