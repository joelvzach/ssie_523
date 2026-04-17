# Enhanced Data Download Guide

**Date**: 2026-04-16  
**Status**: Partial - 3 real datasets collected, 4 require manual download

---

## ✅ Currently Available (REAL DATA)

| Dataset | File | Countries | Ready |
|---------|------|-----------|-------|
| UNESCO World Heritage Sites | unesco_world_heritage_sites.csv | 60 | ✅ |
| World Bank Political Stability | world_bank_political_stability.csv | 39 | ✅ |
| World Bank Policy Assessment | world_bank_policy_institutional_assessment.csv | 39 | ✅ |
| Air Quality Proxy | who_air_quality_proxy.csv | 4 (income groups) | ⚠️ Limited |
| Global Peace Index Proxy | global_peace_index.csv | 39 | ✅ (using WB proxy) |

---

## ⏳ Manual Download Required (4 datasets)

### 1. Cost of Living (Numbeo) - 15 minutes

**Source**: Kaggle  
**URL**: https://www.kaggle.com/datasets/prasertk/numbeo-cost-of-living-2024

**Steps**:
1. Visit the URL above (requires Kaggle account - free)
2. Click "Download" button
3. Extract the CSV file
4. Rename to: `numbeo_cost_of_living.csv`
5. Place in: `data/enhanced_data/`

**Alternative** (no account needed):
- Visit: https://www.numbeo.com/cost-of-living/rankings_by_country.jsp
- Manually copy the table to Excel/CSV
- Save as: `numbeo_cost_of_living.csv`

---

### 2. Air Quality (WHO) - 15 minutes

**Source**: Our World in Data  
**URL**: https://ourworldindata.org/grapher/annual-pm25-concentrations

**Steps**:
1. Visit the URL above
2. Click "Download" → "CSV"
3. Save as: `who_air_quality_pm25.csv`
4. Place in: `data/enhanced_data/`

---

### 3. Climate Data - 20 minutes

**Source**: Climate-Data.org  
**URL**: https://en.climate-data.org/

**Steps**:
1. Visit the URL above
2. Search for major tourism countries (France, Spain, USA, etc.)
3. Click "Download" for each country
4. Combine into single CSV or keep separate
5. Save as: `climate_data.csv`

**Alternative** (easier):
- Visit: https://ourworldindata.org/grapher/average-deadly-heat-events
- Download temperature data
- Save as: `climate_temperature.csv`

---

### 4. Global Peace Index - 10 minutes

**Source**: Vision of Humanity  
**URL**: https://www.visionofhumanity.org/resources/

**Steps**:
1. Visit the URL above
2. Click "Global Peace Index 2024"
3. Download data tables (usually in appendix)
4. Save as: `global_peace_index_2024.csv`

**Alternative** (easier):
- Use Fragile States Index: https://fundforpeace.org/fpi/fsi-2023/
- Download CSV from their website
- Save as: `fragile_states_index.csv`

---

## Quick Download Script

After manual downloads, run this to verify:

```bash
cd /Users/joelvzach/Code/ssie_523
python3 src/analyze_enhanced_data.py
```

---

## Current Analysis Possible

With current 3 datasets, you can analyze:
- ✅ Cultural attractiveness (UNESCO sites)
- ✅ Political stability/risk (World Bank)
- ✅ Correlation between stability and tourism
- ✅ Country profiling

---

**Total Manual Download Time**: ~1 hour
**Priority**: Cost of Living > Air Quality > Climate > GPI
