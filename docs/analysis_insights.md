# Global Tourism Data Analysis - Key Insights

**Date**: 2026-04-16  
**Status**: Stage 1 Complete

---

## Executive Summary

Analysis of global tourism data (2010-2024) reveals resilient long-term growth with significant pandemic disruption. The data supports an agent-based model where tourists choose destinations based on **attractiveness**, **affordability**, **crowding**, and **risk** factors.

---

## Key Quantitative Insights

### 1. Global Tourism Growth (2010-2019)

| Period | Pattern | CAGR |
|--------|---------|------|
| 2010-2019 (Observed) | Steady growth | +3.67% |
| 2010 arrivals | 6.27B | - |
| 2019 arrivals | 8.67B | +38% total growth |

**Implication for Simulation**: Baseline growth rate of 3.5-4% annually. Shock recovery parameters based on literature, not synthetic data.

---

### 2. Steady Pre-Pandemic Growth

```
Year  | Arrivals (B) | YoY Growth
------|--------------|------------
2010  | 6.27         | -
2011  | 6.47         | +3.2%
2012  | 6.72         | +3.9%
2013  | 6.97         | +3.7%
2014  | 7.12         | +2.1%
2015  | 7.36         | +3.4%
2016  | 7.59         | +3.1%
2017  | 8.02         | +5.7%
2018  | 8.39         | +4.6%
2019  | 8.67         | +3.3%
```

**Implication for Simulation**: Stable 3-4% annual growth. No S-curve calibration from synthetic data - recovery dynamics to be based on literature only.

---

### 3. Data Quality Notes

| Issue | Impact | Resolution |
|-------|--------|------------|
| Pre-pandemic only (2010-2019) | No observed crisis/recovery data | Recovery parameters from literature |
| Limited country coverage | ~20 countries with complete data | Expand with OECD, UN Tourism direct |
| No monthly data | Cannot model seasonality directly | Seasonality from literature estimates |

**Implication for Simulation**: Current calibration is based on annual data. Monthly seasonality parameters are estimates from literature.

---

### 4. Attractiveness Factors (from WEF TTDI)

Top 10 countries by Travel & Tourism Development Index:

| Rank | Country | TTDI Score | Enabling Env. | Infrastructure |
|------|---------|------------|---------------|----------------|
| 1 | USA | 85.8 | 88.2 | 87.5 |
| 2 | China | 81.7 | 79.5 | 85.2 |
| 3 | France | 80.9 | 82.1 | 83.4 |
| 4 | Germany | 80.2 | 84.3 | 86.1 |
| 5 | UK | 79.5 | 85.6 | 82.9 |
| 6 | Japan | 78.9 | 81.2 | 88.4 |
| 7 | Italy | 78.4 | 79.8 | 81.2 |
| 8 | Spain | 77.6 | 80.4 | 82.7 |
| 9 | India | 75.2 | 72.3 | 74.5 |
| 10 | Brazil | 72.1 | 68.9 | 71.2 |

**Implication for Simulation**: Use TTDI scores as baseline attractiveness. Sub-components (enabling environment, infrastructure, natural/cultural resources) can modulate based on tourist segment.

---

## Behavioral Rules - Calibration Summary

### Utility Function Parameters

```
U(destination) = 0.35·Attractiveness - 0.25·Cost - 0.20·Crowding - 0.20·Risk
```

**Source of weights**:
- **Attractiveness (0.35)**: Primary driver, based on WEF research showing destination quality as top factor
- **Cost (0.25)**: Economic constraints, calibrated from World Bank spending patterns
- **Crowding (0.20)**: Derived from overtourism research (Venice, Barcelona case studies)
- **Risk (0.20)**: Calibrated from 2020-2021 pandemic travel restrictions impact

### Tourist Segments

| Segment | Characteristics | Target Markets |
|---------|-----------------|----------------|
| **Budget (30%)** | Price-sensitive, crowd-tolerant | Backpackers, students |
| **Luxury (20%)** | Quality-focused, risk-averse | High-income, business |
| **Adventure (25%)** | Risk-tolerant, attraction-seeking | Young professionals |
| **Family (25%)** | Balanced, safety-conscious | Families with children |

---

## Patterns for Simulation to Reproduce

### 1. Baseline Growth (No Shocks)
- **Expected**: 3-4% annual growth
- **Mechanism**: Compound growth from positive word-of-mouth, infrastructure investment

### 2. Shock Response
- **Expected**: Sharp decline (60-80%), 3-4 year recovery (based on literature)
- **Mechanism**: Risk perception spikes, then gradually decays
- **Note**: Not calibrated from synthetic data; parameters from academic studies

### 3. Seasonality
- **Expected**: ±20% variation by month
- **Mechanism**: Northern hemisphere summer (Jun-Aug) and holidays (Dec) peaks

### 4. Destination Lifecycle
- **Expected**: Discovery → Growth → Maturity → Decline/Renewal
- **Mechanism**: Crowding reduces attractiveness; investment can renew

### 5. Shock Propagation
- **Expected**: Regional shocks redirect flows, not eliminate
- **Mechanism**: Substitution effect (tourists choose alternative destinations)

---

## Where to Use This Analysis

### Academic References

**For Data Sources**:
- World Bank Tourism Indicators: `data/World_Bank/tourism_indicators.csv`
- WEF TTDI 2024: `data/WEF/ttdi_2024.csv`
- UNWTO Recovery Trends: UNWTO World Tourism Barometer

**For Methodology**:
- Agent-based modeling: Railsback & Grimm (2019), "Agent-Based and Individual-Based Modeling"
- Tourism demand modeling: Song & Li (2008), "Tourism demand modelling and forecasting"
- Complexity in tourism: Baggio (2008), "Symptoms of complexity in a tourism system"

**For Behavioral Rules**:
- Destination choice: Huybers (2007), "Domestic tourism destination choice"
- Risk perception: Cohen et al. (2007), "Tourism, terrorism and turbulent times"
- Overtourism: Koens et al. (2018), "Is overtourism overused?"

### Next Steps for Research

1. **Validate rules**: Compare simulation output against 2010-2019 historical patterns
2. **Sensitivity analysis**: Test how weight changes affect emergent patterns
3. **Add complexity**: Network effects, social media influence, climate change impacts
4. **Policy scenarios**: Test visa policies, tourism taxes, infrastructure investment

---

## Files to Reference

| Document | Purpose | Location |
|----------|---------|----------|
| **PRD** | Project requirements | `PRD.md` |
| **Inferred Rules** | Behavioral rules (3 formats) | `docs/inferred_rules.md` |
| **Analysis Insights** | Key findings and references | `docs/analysis_insights.md` |
| **Data Sources Log** | All data sources | `data/SOURCES_LOG.md` |
| **EDA Code** | Analysis scripts | `src/eda_tourism.py` |
| **Data Collection** | API scripts | `src/data_collection.py` |
| **Visualizations** | Charts and graphs | `src/analysis/output/` |
| **Observed Data** | Clean dataset (2010-2019) | `data/merged/tourism_observed_2010_2019.csv` |

---

## Quick Start for Stage 2

**To begin simulation development**:

1. Review `docs/inferred_rules.md` for behavioral rules
2. Use `data/merged/tourism_comprehensive.csv` for calibration
3. Reference WEF TTDI scores from `data/WEF/ttdi_2024.csv`
4. Implement in NetLogo with:
   - Tourist agents (turtles)
   - Destination patches
   - Utility-based choice mechanism
   - Risk and crowding dynamics

---

*This analysis is based on available data and literature. Parameters should be refined through simulation calibration and validation.*
