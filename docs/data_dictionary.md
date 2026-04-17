# Data Dictionary - Global Tourism Simulation

**Version**: 2.0  
**Date**: 2026-04-17  
**Coverage**: 177 countries, 1995-2024, 8,911 observations

---

## Core Dataset: tourism_comprehensive_1995_2024.csv

**Location**: `data/merged/tourism_comprehensive_1995_2024.csv`  
**Records**: 8,911 country-year observations  
**Variables**: 14

### Variable Definitions

| Variable | Type | Range | Source | Description |
|----------|------|-------|--------|-------------|
| `country_code` | Categorical | 3-letter | UN Tourism | ISO-like country identifier |
| `country_name` | Categorical | Text | UN Tourism | Standardized country name |
| `year` | Integer | 1995-2024 | - | Observation year |
| `tourist_arrivals` | Continuous | 0 - 82M | UN Tourism | International tourist arrivals (absolute) |
| `tourism_expenditure_usd_millions` | Continuous | 0.1 - 73,000 | UN Tourism | Inbound tourism expenditure |
| `tourism_gdp_share_pct` | Continuous | 0.5 - 51.4 | OECD | Tourism's share of GDP |
| `ttdi_score` | Continuous | 2.78 - 5.24 | WEF (2024) | Travel & Tourism Development Index |
| `attractiveness_index` | Continuous | 0.09 - 0.91 | Calculated | Normalized TTDI: (TTDI - 2.5) / 3.0 |
| `cost_of_living_index` | Continuous | 26.6 - 135.8 | Numbeo (2024) | Cost of living (NYC = 100) |
| `affordability_index` | Continuous | 0.09 - 0.74 | Calculated | Inverse cost: 1 - (cost / max_cost) |
| `pm25_concentration` | Continuous | 5.0 - 97.9 | WHO | Annual PM2.5 exposure (µg/m³) |
| `air_quality_index` | Continuous | 0.25 - 0.95 | Calculated | Inverse PM2.5: 1 - (pm25 / max_pm25) |
| `conflict_events` | Integer | 0 - 13,664 | ACLED | Annual conflict events |
| `conflict_fatalities` | Integer | 0 - 52,000 | ACLED | Annual conflict fatalities |
| `risk_score` | Continuous | 0.0 - 1.0 | Calculated | Normalized conflict: events / max_events |
| `heritage_sites` | Integer | 0 - 59 | UNESCO | UNESCO World Heritage Sites count |

---

## Derived Variables (For Simulation)

### Utility Function Components (Enhanced)

| Variable | Formula | Range | Purpose |
|----------|---------|-------|---------|
| `attractiveness_normalized` | `(ttdi_score - 2.78) / (5.24 - 2.78)` | 0-1 | Utility function input |
| `cost_normalized` | `(cost_index - 26.6) / (135.8 - 26.6)` | 0-1 | Utility function input |
| `crowding_ratio` | `arrivals / carrying_capacity` | 0-2+ | Overtourism indicator |
| `risk_perception` | `1 - exp(-0.76 × conflict_events_per_10k)` | 0-1 | Rosselló coefficient |
| **`distance_km`** | `haversine(origin_lat, origin_lon, dest_lat, dest_lon)` | 0-20,000 km | **NEW: Geographic friction** |
| **`distance_normalized`** | `distance_km / 20000` | 0-1 | **NEW: Normalized for utility** |
| **`popularity_index`** | `log(arrivals_t-1 + 1) / log(max_arrivals + 1)` | 0-1 | **NEW: Endogenous rich-get-richer** |

### Geographic Parameters (Country Centroids)

**Location**: `data/derived/country_centroids.csv` (to be created)  
**Variables**:

| Variable | Type | Range | Source |
|----------|------|-------|--------|
| `country_code` | Categorical | 3-letter | Standard ISO |
| `country_name` | Categorical | Text | UN Tourism |
| `latitude` | Continuous | -90 to +90 | Standard centroids |
| `longitude` | Continuous | -180 to +180 | Standard centroids |
| `region` | Categorical | 5 regions | UN Tourism classification |

**Regions**:
1. Europe (45% of tourists)
2. Americas (25% of tourists)
3. Asia-Pacific (20% of tourists)
4. Africa (5% of tourists)
5. Middle East (5% of tourists)

### Origin-Destination Flow Parameters

**Regional Clustering** (calibrated from UN Tourism patterns):

| Home Region | Intra-regional % | Extra-regional 1 | Extra-regional 2 |
|-------------|-----------------|------------------|------------------|
| Europe | 65% | Americas (20%) | Asia-Pacific (10%) |
| Americas | 55% | Europe (30%) | Asia-Pacific (10%) |
| Asia-Pacific | 55% | Europe (25%) | Americas (15%) |
| Africa | 45% | Europe (35%) | Middle East (15%) |
| Middle East | 40% | Europe (35%) | Asia-Pacific (20%) |

**Distance Friction Examples**:

| Route | Distance (km) | Normalized | Friction Penalty (η=0.30) |
|-------|--------------|------------|---------------------------|
| London → Paris | 344 | 0.017 | -0.005 (negligible) |
| New York → London | 5,585 | 0.28 | -0.084 (moderate) |
| Sydney → London | 17,016 | 0.85 | -0.255 (strong) |
| Maximum (antipodal) | 20,000 | 1.00 | -0.30 (maximum) |

### Popularity Feedback Parameters

**Calculation**:
```python
popularity_index = log(previous_period_arrivals + 1) / log(max_observed_arrivals + 1)
```

**Example Values**:

| Destination | Annual Arrivals | Popularity Index | Bonus (θ=0.25) |
|-------------|-----------------|-----------------|----------------|
| France | 82M | 0.94 | +0.235 |
| Spain | 84M | 0.94 | +0.235 |
| Thailand | 40M | 0.89 | +0.223 |
| Maldives | 1.7M | 0.38 | +0.095 |
| Bhutan | 0.3M | 0.28 | +0.070 |

**Why Log-Scale**:
- Prevents winner-take-all dynamics (linear would)
- Captures diminishing returns to popularity
- Consistent with Weber-Fechner law (perception is logarithmic)
- Allows secondary destinations to compete on other factors

### Carrying Capacity Estimates

| Subsystem | Formula | Source | Notes |
|-----------|---------|--------|-------|
| `accommodation_capacity` | `(hotel_beds + extra_hotel_beds) × 0.80` | Bertocchi-inspired | 80% occupancy |
| `transport_capacity` | `airport_seats × 0.75` | Assumption | 75% load factor |
| `infrastructure_capacity` | `population × 0.15` | Assumption | 15% can host tourists |
| `attraction_capacity` | `Σ(site_capacity)` | UNESCO | Sum of heritage site capacities |
| `overall_capacity` | `min(all_subsystems)` | Bertocchi | Bottleneck approach |

---

## Segment Configuration Variables

**User-configurable parameters** (no empirical literature found)

| Parameter | Type | Default Range | Purpose |
|-----------|------|---------------|---------|
| `segment_population_share` | Continuous (0-1) | 0.05-0.50 | Fraction of tourists in segment |
| `segment_trip_frequency` | Continuous | 0.5-4.0 trips/year | How often segment travels |
| `utility_weight_attractiveness` | Continuous (0-1) | 0.20-0.50 | α parameter |
| `utility_weight_cost` | Continuous (0-1) | 0.15-0.50 | β parameter |
| `utility_weight_crowding` | Continuous (0-1) | 0.10-0.25 | γ parameter |
| `utility_weight_risk` | Continuous (0-1) | 0.10-0.30 | δ parameter |
| `social_media_sensitivity` | Continuous (0-1) | 0.30-0.50 | ε parameter |
| `return_probability` | Continuous (0-1) | 0.55-0.65 | ζ parameter (Sönmez & Graefe) |
| `purpose_split_business` | Continuous (0-1) | 0.05-0.40 | Business vs. personal travel |

---

## Shock Parameters

### Shock Types and Magnitudes

| Shock Type | Magnitude | Duration | Recovery Pattern | Source |
|------------|-----------|----------|------------------|--------|
| Pandemic | -70% arrivals | 12 months | Hybrid (double-dip + S-curve) | UN Tourism + Škare |
| Volcanic eruption | -4% per $1B cost | 6-12 months | S-curve | Rosselló et al. |
| Wildfire | -0.035% per $1B cost | 3-6 months | Linear | Rosselló et al. |
| Flood | -0.007% per 1K deaths | 6 months | Linear | Rosselló et al. |
| Storm | -0.003% per $1B cost | 6 months | Linear | Rosselló et al. |
| Earthquake | -1.7% per M affected | 12 months | S-curve | Rosselló et al. |
| Conflict | -30% to -50% | Variable | S-curve (2-8 years) | ACLED + assumption |

### Recovery Function Parameters

```python
# S-curve recovery (default)
recovery(t) = 100 / (1 + exp(-k × (t - t₀)))
where:
  k = 0.8 (growth rate)
  t₀ = 2.5 years (midpoint)

# Double-dip recovery (pandemic early phase)
recovery(t) = base_recovery × (1 - 0.15 × exp(-((t-1.5)² / 0.5)))
for t < 2.0 years

# Linear recovery (natural disasters)
recovery(t) = min(1.0, t / recovery_duration)
```

---

## Business vs. Leisure Elasticities (Peng et al., 2014)

| Elasticity Type | Business Travel | Leisure Travel | Ratio |
|-----------------|-----------------|----------------|-------|
| Price elasticity | -0.350 | -1.102 | 3.15x |
| Income elasticity | 1.605 | 2.401 | 1.49x |

**Application**: Multiply cost weight (β) by 0.3 for business travelers

---

## Network Effects Parameters

### Word-of-Mouth (Litvin et al., 2018)

| Parameter | Value | Source |
|-----------|-------|--------|
| Review consultation rate | 95% | Litvin et al. |
| Reviews read per booking | 6-12 | Litvin et al. |
| Positive review prevalence | 70-94% | Litvin et al. |
| Fraudulent review estimate | ~20% | Litvin et al. |

### Social Media Effects (Leung et al., 2021)

| Factor | Weight | Source |
|--------|--------|--------|
| UGC Quality | 45.6% | Leung et al. |
| UGC Quantity | 36.2% | Leung et al. |
| Reviewer Expertise | 22.8% | Leung et al. |
| Perceived Usefulness | 26.2% | Leung et al. |
| Past Experience | 19.5% | Leung et al. |

---

## Data Quality Assessment

| Variable | Completeness | Confidence | Notes |
|----------|--------------|------------|-------|
| tourist_arrivals | 100% | HIGH | UN Tourism primary data |
| ttdi_score | 98.0% | HIGH | WEF 2024 (extracted) |
| cost_of_living_index | 99.6% | HIGH | Numbeo 2024 |
| risk_score | 100% | HIGH | ACLED 1997-2026 |
| air_quality_index | 72.7% | MEDIUM | WHO (some gaps) |
| tourism_expenditure | 97.3% | HIGH | UN Tourism |
| heritage_sites | 34.0% | MEDIUM | UNESCO (60 countries) |

---

## Correlation Matrix (2019-2024 Data)

**Variables**: tourist_arrivals, ttdi_score, cost_index, risk_score, air_quality_index

|  | Arrivals | TTDI | Cost | Risk | Air Quality |
|--|----------|------|------|------|-------------|
| **Arrivals** | 1.000 | | | | |
| **TTDI** | +0.364 | 1.000 | | | |
| **Cost** | -0.041 | +0.423 | 1.000 | | |
| **Risk** | -0.089 | -0.234 | -0.156 | 1.000 | |
| **Air Quality** | +0.049 | +0.187 | +0.092 | -0.067 | 1.000 |

**Interpretation**:
- TTDI is strongest predictor of arrivals (r = 0.364)
- Cost has negligible correlation (r = -0.041) - quality matters more than price
- Risk has weak negative correlation (r = -0.089)
- Air quality has weak positive correlation (r = 0.049)

---

## Literature Sources

### Primary Data Sources
1. **UN Tourism Database** - Inbound arrivals, expenditure, purpose split
2. **OECD Tourism Statistics** - Economic indicators, nights spent
3. **WEF TTDI 2024** - Attractiveness scores (PDF extraction)
4. **ACLED** - Conflict events and fatalities
5. **WHO Air Quality Database** - PM2.5 concentrations
6. **Numbeo Cost of Living** - Cost indices
7. **UNESCO World Heritage Centre** - Heritage site counts

### Academic Literature
1. **Rosselló et al. (2020)** - Natural disaster impacts, Tourism Management
2. **Škare et al. (2021)** - COVID-19 impact, Technological Forecasting
3. **Bertocchi et al. (2020)** - Carrying capacity model, Sustainability
4. **Peng et al. (2014)** - Business/leisure elasticities, J. Travel Research
5. **Litvin et al. (2018)** - eWOM effects, Int. J. Contemporary Hospitality
6. **Leung et al. (2021)** - Social media framework, Tourism & Hospitality
7. **Sönmez & Graefe (1998)** - Memory/return patterns, J. Travel Research
8. **Woodside & Lysonski (1989)** - Destination choice model, J. Travel Research
9. **Seddighi & Theocharous (2002)** - Choice model validation, Tourism Management

---

## Missing Data & Assumptions

### Assumptions (User-Configurable)

| Parameter | Assumed Value | Justification | Confidence |
|-----------|---------------|---------------|------------|
| Segment population shares | 30/20/25/25 | No literature found | LOW |
| Trip frequency by segment | 0.75-3.0 trips/yr | Logical ranges | LOW |
| Infrastructure capacity | 15% of population | Rough estimate | LOW |
| 80% capacity threshold | User-configurable | Bertocchi misinterpretation corrected | MEDIUM |
| Linear degradation slope | γ = 0.5 | Assumption | LOW |

### Data Gaps

| Missing Data | Impact | Workaround |
|--------------|--------|------------|
| City-level tourism stats | Cannot model sub-national | Country-level only for Stage 2 |
| Monthly seasonality patterns | Cannot calibrate seasonality | Literature estimate (±20%) |
| Actual hotel bed counts | Capacity estimation imprecise | Use OECD accommodation data as proxy |
| Segment-specific behavior | Cannot validate 4 segments | User-configurable, calibrate from correlations |
| Network effect elasticities | Cannot quantify WOM impact | Use literature ranges, sensitivity analysis |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-16 | Initial data dictionary (World Bank only) |
| 2.0 | 2026-04-17 | Comprehensive update with all 8 datasets + literature |

---

**Notes**:
- This is a living document - update as new data sources are added
- User-configurable parameters should be clearly distinguished from empirical values
- All assumptions should be documented with confidence levels
