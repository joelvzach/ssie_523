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

**Enhanced Key Dynamics** (v2.1):
- **Origin-Destination Structure**: Each tourist has a home country
- **Geographic Friction**: Distance decay in destination choice
- **Network Effects**: Popularity feedback (rich-get-richer)
- **Regional Clustering**: Realistic flow patterns (65% intra-regional for Europe)
- **Tourism Friendliness**: Resident attitudes → policy feedback loop (NEW v2.1)
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
  - [ ] Destination classes (multi-subsystem capacity + TFI)
  - [ ] Utility function (8 factors)
  - [ ] Softmax choice mechanism
  - [ ] Shock/recovery dynamics (hybrid model)
  - [ ] **Tourism Friendliness Index (TFI) dynamics** (NEW v2.1)
- [ ] Visualization of emergent patterns
  - [ ] Hub formation
  - [ ] Regional clustering
  - [ ] Congestion spillover
  - [ ] Rich-get-richer dynamics
  - [ ] **Policy feedback loops (TFI-driven)** (NEW v2.1)
- [ ] Validation against historical data
  - [ ] Tier 1: Aggregate metrics (CAGR, shock, recovery)
  - [ ] Tier 2: Distributional metrics (Gini, top 10 share)
  - [ ] Tier 3: Emergent patterns (qualitative)
  - [ ] Tier 4: Sensitivity tests
- [ ] Interactive dashboard (Streamlit)
  - [ ] User-configurable segments
  - [ ] Parameter tuning interface
  - [ ] Scenario exploration
  - [ ] **TFI visualization (resident attitudes over time)** (NEW v2.1)

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
- [ ] **Tourism Friendliness Index (TFI) dynamics** (NEW v2.1)
- [ ] Interactive visualization (Streamlit)
- [ ] Validation dashboard (real-time metrics)

**Phase 3 (Stage 3) - Advanced**:
- [ ] City-level granularity (top 50 destinations)
- [ ] Full network effects (not just popularity proxy)
- [ ] Supply-side dynamics (marketing, investment)
- [ ] Policy interventions (visa, tourism taxes) **← Now modeled via TFI**

**Validation Requirements**:
- **Tier 1 (Must Pass)**: CAGR 3.0-4.5%, Shock -65% to -75%, Recovery 90-100%
- **Tier 2 (Should Pass)**: Gini 0.60-0.80, Top 10 share 40-60%, Regional flows ±15%
- **Tier 3 (Nice to Have)**: Hub formation, regional clustering, congestion spillover

---

## 4. Open Questions

### Resolved ✅

1. **Tourist heterogeneity**: Yes, 4 segments (Budget, Luxury, Adventure, Family) with different weights - **USER-CONFIGURABLE**
2. **Attractiveness modeling**: WEF TTDI scores (0-100 scale, normalized 0-1)
3. **Crowding**: Multi-subsystem capacity (accommodation, transport, infrastructure, attractions), LINEAR degradation above 80% threshold
4. **Risk factors**: ACLED conflict events → risk perception (Rosselló coefficient: -0.76)
5. **Geographic structure**: Origin-destination with home countries, great-circle distance friction
6. **Network effects**: Popularity feedback (log-scale, rich-get-richer) - **INCLUDED in v2.0**
7. **Memory/learning**: Return visitor probability (0.55-0.65 from Sönmez & Graefe)
8. **Regional clustering**: 5 regions with intra-regional flow patterns (65% for Europe)
9. **Model purpose**: **Exploratory sandbox, NOT predictive** (TTDI r² = 0.13 acknowledged)
10. **Tourism Friendliness**: TFI models resident attitudes → policy feedback (Muler González et al., Cheung & Li) - **INCLUDED in v2.1**

### Remaining ❓

1. **Time granularity**: Monthly recommended for seasonality, but computationally heavier than yearly
2. **Flight network proxy**: Use distance + GDP, or get actual flight connectivity data?
3. **Cultural affinity**: Add linguistic/colonial ties as additional friction modifier?
4. **City-level**: Stage 2 (top 10 cities) or Stage 3 (comprehensive)?
5. **Supply-side dynamics**: Include destination marketing, infrastructure investment in Stage 3?
6. **Validation automation**: Real-time validation dashboard during simulation, or post-hoc analysis?

---

## 5. Technical Stack

### Data Analysis (Stage 1) ✅ COMPLETE
- Python (pandas, numpy, scipy)
- Visualization (matplotlib, seaborn)
- PDF extraction (pdfplumber)
- Data merging (custom scripts)

### Simulation (Stage 2) - Implementation Plan
- **Core Framework**: Python with Mesa (agent-based modeling)
- **Geographic Calculations**: haversine formula (custom implementation)
- **Network Effects**: NetworkX (for future full network modeling)
- **Visualization**: 
  - Static: matplotlib, seaborn
  - Interactive: Streamlit dashboard
- **Validation**: pytest (automated validation tests)
- **Data Management**: pandas, numpy (existing merged dataset)

**Architecture**:
```
simulation/
├── agents/
│   ├── tourist.py (with home_country, segment, memory)
│   └── segments.py (user-configurable parameters)
├── destinations/
│   ├── destination.py (multi-subsystem capacity + TFI)
│   ├── capacity.py (4 subsystems: accommodation, transport, infrastructure, attractions)
│   └── tfi.py (Tourism Friendliness Index dynamics) ← NEW v2.1
├── dynamics/
│   ├── utility.py (8-factor utility function)
│   ├── choice.py (softmax with distance + popularity)
│   ├── shocks.py (hybrid recovery model)
│   ├── popularity.py (log-scale feedback)
│   └── tfi_dynamics.py (resident attitudes → policy feedback) ← NEW v2.1
├── visualization/
│   └── dashboard.py (Streamlit interface with TFI tracking)
└── validation/
    ├── metrics.py (4-tier validation + TFI metrics)
    └── tests.py (automated test suite)
```

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
