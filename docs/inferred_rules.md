# Inferred Behavioral Rules for Tourism Simulation

**Version**: 2.1  
**Date**: 2026-05-01  
**Based on**: UN Tourism (3,794 records after deduplication fix), OECD, WEF TTDI (119 countries), ACLED, WHO, Numbeo, UNESCO, World Bank GDP + 6 Academic Papers

**Phase 4 Updates**:
- ✅ GDP integration (98 countries with tourism dependency)
- ✅ OECD validation (r = 0.795)
- ✅ Segment distribution calibration (RMSE 3.1%)
- ✅ Country code mapping (100%: 177/177)
- ✅ Data duplication fix (TOTAL indicator filtering)

---

## Executive Summary

Analysis of **8,911 country-year observations** (177 countries, 1995-2024) combined with **6 peer-reviewed academic papers** reveals key patterns that inform agent behavioral rules for the simulation. Tourists make destination choices based on four primary factors: **attractiveness**, **affordability**, **crowding**, and **risk**, with heterogeneity by tourist segment and travel purpose.

**Data Sources**:
- ✅ UN Tourism inbound arrivals (215 countries, 1995-2024)
- ✅ WEF TTDI attractiveness scores (119 countries, extracted from PDF)
- ✅ OECD economic indicators (55 countries)
- ✅ ACLED conflict events (global, 1997-2026)
- ✅ WHO air quality (PM2.5 concentrations)
- ✅ Numbeo cost of living (156 countries)
- ✅ UNESCO heritage sites (60 countries)
- ✅ UN Tourism purpose split (Business 11% / Personal 89%)

**Literature Sources**:
- Rosselló et al. (2020) - Natural disaster impacts (438 citations)
- Škare et al. (2021) - COVID-19 impact (882 citations)
- Bertocchi et al. (2020) - Carrying capacity model (140 citations)
- Peng et al. (2014) - Business/leisure elasticities (meta-analysis)
- Litvin et al. (2018) - Word-of-mouth effects
- Sönmez & Graefe (1998) - Memory/return visitor patterns

---

## Key Findings from Data Analysis

### 1. Baseline Growth Patterns (2010-2019)

| Metric | Value | Source | Confidence |
|--------|-------|--------|------------|
| 2010 arrivals | 6.27B | UN Tourism | **HIGH** |
| 2019 arrivals | 8.67B | UN Tourism | **HIGH** |
| Growth (2010-2019) | +38% | UN Tourism | **HIGH** |
| **CAGR (2010-2019)** | **3.69%** | Our analysis | **HIGH** |
| Growth volatility (σ) | 8.52% | Our analysis | **HIGH** |

**Literature Support**: Song & Li (2007) review (1,358 citations) confirms 3-4% typical growth rates

### 2. Pandemic Shock & Recovery (2020-2024)

| Metric | Value | Source | Confidence |
|--------|-------|--------|------------|
| Shock magnitude (2020) | **-70.6%** | UN Tourism | **HIGH** |
| Recovery (2024) | **94.5%** of 2019 | UN Tourism | **HIGH** |
| Fully recovered countries | 42.9% | UN Tourism | **HIGH** |
| Recovery heterogeneity (σ) | 36.0% | UN Tourism | **HIGH** |
| Recovery pattern | S-curve (years 2+) | Data fit | **MEDIUM** |

**Literature Validation**:
- Škare et al. (2021): -25% to -35% **spending** loss (different metric - arrivals vs. spending)
- Škare et al.: Double-dip pattern in early phase (0-2 years)
- Rosselló et al. (2020): 6-12 month recovery for natural disasters

**Regional Recovery Patterns**:
| Region | 2024 Recovery | Interpretation |
|--------|---------------|----------------|
| Americas | 109% | Leading recovery |
| Europe | 101% | At baseline |
| Africa | 97% | Near baseline |
| Asia-Pacific | 94% | Lagging (China effect) |
| Middle East | 92% | Lagging |

### 3. Business vs. Personal Travel (UN Tourism Purpose Data)

| Metric | Value | Source |
|--------|-------|--------|
| Business travel share | **11.2%** | UN Tourism 2019 |
| Personal/Leisure share | **88.8%** | UN Tourism 2019 |
| Coverage | 183 countries | UN Tourism |

**Literature Validation** (Peng et al., 2014 meta-analysis, 195 studies):
| Travel Purpose | Price Elasticity | Income Elasticity |
|---------------|-----------------|-------------------|
| **Business** | **-0.350** (low sensitivity) | **1.605** (necessity) |
| **Holiday** | **-1.102** (high sensitivity) | **2.401** (luxury) |
| **VFR** | **-0.800** (medium) | **2.192** (luxury) |

**Key Insight**: Business travelers are **3x less price-sensitive** than leisure travelers

### 4. Destination Choice Correlations (Our Analysis)

Based on correlation analysis of 1,773 records (2019-2024):

| Factor | Correlation with Arrivals | Strength | Interpretation |
|--------|--------------------------|----------|----------------|
| Tourism expenditure | **+0.642** | Strong | Validates data quality |
| TTDI attractiveness | **+0.364** | Moderate | Primary driver confirmed |
| Air quality | +0.049 | Weak | Secondary factor |
| Affordability | -0.041 | Very weak | Quality > price for most |

**Implication**: Attractiveness (TTDI) is the strongest predictor, supporting utility-based choice model

### 5. Natural Disaster Impacts (Rosselló et al., 2020)

| Disaster Type | Impact per Unit | Duration |
|--------------|-----------------|----------|
| **Volcano** | -3.44% to -4.52% per $1M cost | 12 months |
| **Wildfire** | -0.03% to -0.04% per $1M cost | 6 months |
| **Flood** | -0.005% to -0.008% per 1,000 deaths | 6 months |
| **Tsunami** | -0.085% to -0.109% per M affected | 12 months |
| **Storm** | -0.003% per $1M cost | 6 months |
| **Earthquake** | -0.017% per M affected | 12 months |

**Key Finding**: Economic costs are most reliable predictor; volcanic eruptions most damaging

### 6. Carrying Capacity & Overtourism (Bertocchi et al., 2020)

**Multi-Subsystem Capacity Model** (7 subsystems identified):
1. Hotel bed capacity
2. Extra-hotel bed capacity (Airbnb, B&Bs)
3. Restaurant meal capacity
4. Parking places
5. Public transportation
6. Waste disposal capacity
7. Attractions (non-reproducible resources)

**Venice Case Study Findings**:
- Optimal daily visitors: **52,111**
- Optimal composition: **28% excursionists, 72% overnight**
- Current problematic ratio: **80% excursionists** (NOT a capacity threshold!)
- Total bed capacity: ~43,000 beds
- Resident population: ~53,000 (2018)

**Critical Finding**: Degradation is **LINEAR** (not quadratic), multi-subsystem (not single threshold)

### 7. Memory & Return Visitor Patterns (Sönmez & Graefe, 1998)

| Region | Return Probability | Experience Effect |
|--------|-------------------|-------------------|
| Europe | 0.65 | Baseline |
| Caribbean | 0.56 | Baseline |
| North America | 0.55 | Baseline |
| Africa (risky) | 0.62 | Experience reduces avoidance by 23 pp |
| Middle East (risky) | 0.60 | Experience reduces avoidance by 31 pp |

**Key Finding**: Past visitors are **3-5x more likely** to return; experience reduces risk avoidance

### 8. Word-of-Mouth & Social Media Effects

**Litvin et al. (2018)**:
- **95%** consult reviews before booking
- Read **6-12 reviews** per booking decision
- **70-94%** of reviews are positive (platform-dependent)
- Negative eWOM has more influence than positive (no specific ratio)

**Leung et al. (2021)** - 149 studies reviewed:
- UGC Quality: 45.6% of studies
- UGC Quantity: 36.2% of studies
- Reviewer Expertise: 22.8% of studies
- Purchase Intention outcome: 21.5% of studies
- eWOM Intention outcome: 12.1% of studies

---

## Inferred Behavioral Rules

### Rule Format 1: Mathematical Utility Function (Enhanced with Geographic & Network Effects)

Each tourist agent maximizes utility when choosing a destination:

```
U(destination) = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk - η·Distance + θ·Popularity + ε·SocialMedia + ζ·Memory
```

**Where:**
- `α, β, γ, δ, η, θ, ε, ζ` = segment-specific weight parameters (sum to 1.0)
- `Attractiveness` = TTDI score (normalized 0-1, range 2.78-5.24)
- `Cost` = Numbeo cost index (normalized 0-1, range 26.6-135.8)
- `Crowding` = arrivals / carrying_capacity (multi-subsystem bottleneck)
- `Risk` = ACLED conflict events → risk perception (Rosselló coefficient: -0.76)
- **`Distance` = great_circle_distance(origin, destination) / max_distance (normalized 0-1)**
- **`Popularity` = log(arrivals_previous_period + 1) / log(max_arrivals + 1) (endogenous rich-get-richer)**
- `SocialMedia` = UGC quality × quantity × credibility (Leung et al. framework)
- `Memory` = past experience modifier (Sönmez & Graefe: 0.55-0.65 return probability)

**Critical Addition: Origin-Destination Structure**

Each tourist agent now has a **home country**:
```python
tourist.home_country = sample_from_regional_distribution()
```

**Regional Clustering** (from UN Tourism flow patterns):
| Region | Intra-regional Share | Primary Destinations |
|--------|---------------------|---------------------|
| Europe | 60-70% | Europe + Mediterranean |
| Americas | 50-60% | Americas + Europe |
| Asia-Pacific | 50-60% | Asia + Pacific |
| Africa | 40-50% | Africa + Europe |
| Middle East | 40-50% | Middle East + Europe + Asia |

**Distance Calculation**:
```python
def great_circle_distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371  # Earth's radius in km
    φ1, φ2 = radians(lat1), radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lon2 - lon1)
    
    a = sin(Δφ/2)² + cos(φ1)·cos(φ2)·sin(Δλ/2)²
    c = 2·atan2(√a, √(1-a))
    
    return R · c  # Distance in km
```

**Distance Friction Coefficient** (η):
- **Budget**: 0.30 (moderate distance sensitivity)
- **Luxury**: 0.15 (low distance sensitivity - will travel far)
- **Adventure**: 0.20 (moderate-high, seek remote but accessible)
- **Family**: 0.35 (high distance sensitivity - prefer nearby)

**Popularity Feedback** (Endogenous Rich-Get-Richer):
```python
# Log-scale popularity (diminishing returns)
popularity_index = log(previous_period_arrivals + 1) / log(max_observed_arrivals + 1)

# Applied to utility
U += θ · popularity_index
```

**Why Log-Scale**:
- Prevents runaway monopoly (linear would create winner-take-all)
- Captures social proof without overwhelming other factors
- Consistent with Weber-Fechner law (perception is logarithmic)

**Popularity Weight** (θ):
- **Budget**: 0.20 (moderate - follow trends)
- **Luxury**: 0.30 (high - exclusive destinations become more desirable)
- **Adventure**: 0.10 (low - seek undiscovered places)
- **Family**: 0.25 (moderate-high - safety in numbers)

**Baseline Weights** (user-configurable, literature-informed defaults):

| Segment | α (Attract) | β (Cost) | γ (Crowd) | δ (Risk) | ε (Social) | ζ (Memory) | Population |
|---------|-------------|----------|-----------|----------|------------|------------|------------|
| **Budget** | 0.20 | 0.50 | 0.15 | 0.15 | 0.30 | 0.55 | User-configurable |
| **Luxury** | 0.50 | 0.15 | 0.15 | 0.20 | 0.50 | 0.65 | User-configurable |
| **Adventure** | 0.40 | 0.20 | 0.10 | 0.30 | 0.35 | 0.60 | User-configurable |
| **Family** | 0.30 | 0.30 | 0.25 | 0.15 | 0.45 | 0.65 | User-configurable |

**Trip Frequency** (calibrated May 1, 2026 - RMSE reduced from 15.2% → 3.1%):

| Segment | Original | Calibrated | Rationale |
|---------|----------|------------|-----------|
| **Budget** | 0.75 trips/year | **2.0 trips/year** | Frequent short trips, price-sensitive |
| **Luxury** | 3.0 trips/year | **1.0 trips/year** | Fewer but longer, higher-quality trips |
| **Adventure** | 1.5 trips/year | **0.75 trips/year** | Extended trips, less frequent |
| **Family** | 0.75 trips/year | **1.0 trips/year** | School holidays constrain frequency |

**Calibration Method**: Adjust trip frequencies until segment distribution matches target (30/20/25/25) within ±5%.

**Purpose Modifiers** (Peng et al. elasticities):
- Business travel: β (cost) × 0.3 (less price-sensitive)
- Personal travel: No modification

**Note**: Segment population shares are **user-configurable** (no empirical literature found). Default values are assumptions for experimentation.

---

### Rule Format 2: Decision Tree (Enhanced with Origin-Destination Structure)

```python
# Step 1: Assign home country to tourist (regional clustering)
tourist.home_country = sample_from_regional_distribution(
    region_weights={
        'Europe': 0.45,
        'Americas': 0.25,
        'Asia-Pacific': 0.20,
        'Africa': 0.05,
        'Middle East': 0.05
    }
)

# Step 2: Filter choice set by distance (consider only reachable destinations)
max_distance_km = 15000  # Maximum reasonable travel distance
candidate_destinations = [
    dest for dest in all_destinations
    if great_circle_distance(tourist.home, dest) < max_distance_km
]

# Step 3: Risk assessment
IF Risk > 0.7:  # Critical threshold
    → Skip destination (high risk)
    → Exception: Adventure segment uses Risk × 0.3
    
ELSE:
    # Calculate multi-subsystem capacity
    capacity = min(
        accommodation_capacity,
        transport_capacity,
        infrastructure_capacity,
        attraction_capacity
    )
    
    # Linear crowding degradation (Bertocchi et al., NOT quadratic)
    utilization = arrivals / capacity
    IF utilization > 0.8:  # 80% threshold (user-configurable)
        attractiveness_degradation = γ × (utilization - 0.8)
    
    # Calculate distance friction
    distance_km = great_circle_distance(tourist.home, destination)
    distance_normalized = distance_km / 20000  # Normalize by max Earth distance
    distance_penalty = η × distance_normalized
    
    # Calculate popularity feedback (endogenous rich-get-richer)
    popularity_index = log(previous_period_arrivals + 1) / log(max_arrivals + 1)
    popularity_bonus = θ × popularity_index
    
    # Apply social media modifier (Litvin et al., Leung et al.)
    IF tourist.consults_reviews:  # 95% do
        social_media_effect = f(UGC_quality, UGC_quantity, reviewer_expertise)
    
    # Apply memory effect (Sönmez & Graefe)
    IF tourist.visited_before:
        utility += ζ × 0.65  # Return probability
        risk_perception *= 0.62  # Experience reduces risk avoidance
    
    # Calculate utility with ALL factors
    utility = (
        α × attractiveness
        - β × cost
        - γ × crowding
        - δ × risk
        - η × distance  # NEW: Geographic friction
        + θ × popularity  # NEW: Endogenous popularity
        + ε × social_media
        + ζ × memory
    )
    
    # Probabilistic choice (softmax) - Woodside & Lysonski (1989)
    P(choose) = exp(utility / τ) / Σ exp(all_utilities / τ)
```

**Regional Distribution Parameters** (calibrated from UN Tourism flow patterns):

| Home Region | % Stay Intra-regional | Primary Extra-regional | Secondary Extra-regional |
|-------------|----------------------|------------------------|-------------------------|
| **Europe** | 65% | Americas (20%) | Asia-Pacific (10%) |
| **Americas** | 55% | Europe (30%) | Asia-Pacific (10%) |
| **Asia-Pacific** | 55% | Europe (25%) | Americas (15%) |
| **Africa** | 45% | Europe (35%) | Middle East (15%) |
| **Middle East** | 40% | Europe (35%) | Asia-Pacific (20%) |

**Distance Friction Examples**:
- London → Paris (344 km): distance_penalty = 0.017 × η (negligible)
- New York → London (5,585 km): distance_penalty = 0.28 × η (moderate)
- Sydney → London (17,016 km): distance_penalty = 0.85 × η (strong deterrent)

**Popularity Feedback Dynamics**:
```python
# Example: Two destinations with different arrival volumes
destination_A = 10M arrivals  → popularity = log(10M+1)/log(82M+1) = 0.88
destination_B = 100K arrivals → popularity = log(100K+1)/log(82M+1) = 0.64

# With θ = 0.25 (Family segment):
# Destination A gets +0.22 utility bonus
# Destination B gets +0.16 utility bonus
# Difference: +0.06 (significant but not overwhelming)
```

**Risk Thresholds** (user-configurable):
- 0.0-0.3: Low risk (normal behavior)
- 0.3-0.5: Moderate risk (20% probability reduction)
- 0.5-0.7: High risk (50% probability reduction)
- 0.7-1.0: Critical risk (destination excluded, except Adventure segment)

---

### Rule Format 3: Dynamic Parameters (Time-Varying)

**Geographic Parameters** (Country Centroids for Distance Calculation):

| Country | Latitude | Longitude | Source |
|---------|----------|-----------|--------|
| France | 46.2276 | 2.2137 | Standard centroids |
| United States | 37.0902 | -95.7129 | Standard centroids |
| China | 35.8617 | 104.1954 | Standard centroids |
| ... | ... | ... | (All 177 countries) |

**Distance Calculation Implementation**:
```python
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points on Earth
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# Example distances:
# London to Paris: 344 km
# New York to London: 5,585 km
# Sydney to London: 17,016 km
# Maximum possible: ~20,000 km (antipodal)
```

**Seasonality** (literature-based, ±20% amplitude):
```python
def seasonality_multiplier(month, hemisphere):
    if hemisphere == 'Northern':
        if month in [6, 7, 8, 12]:  # Peak
            return 1.2
        elif month in [4, 5, 9, 10]:  # Shoulder
            return 1.0
        else:  # Low (Jan-Mar)
            return 0.8
    else:  # Southern
        # Inverted pattern
        ...
```

**Shock Dynamics** (literature + data):
```python
SHOCK_TYPES = {
    'pandemic': {
        'magnitude': -0.70,  # From UN Tourism data
        'duration_months': 12,
        'recovery_pattern': 'hybrid',  # Double-dip (0-2yr) + S-curve (2+yr)
    },
    'volcano': {
        'elasticity': -0.04,  # Per $1B cost (Rosselló et al.)
        'duration_months': 12,
        'recovery_pattern': 's_curve',
    },
    'wildfire': {
        'elasticity': -0.00035,  # Per $1B cost
        'duration_months': 6,
        'recovery_pattern': 'linear',
    },
    # ... other disaster types
}
```

**Recovery Function** (hybrid model):
```python
def recovery_fraction(years_since_shock, shock_type):
    if shock_type == 'pandemic':
        if years_since_shock < 2.0:
            # Double-dip pattern (Škare et al.)
            return double_dip_recovery(years_since_shock)
        else:
            # S-curve fits 2020-2024 data
            return 100 / (1 + exp(-0.8 × (years_since_shock - 2.5)))
    elif shock_type in ['flood', 'storm', 'wildfire']:
        # Linear recovery (Rosselló et al.: 6-12 months)
        return min(1.0, years_since_shock / 0.5)
    else:
        # Default S-curve
        return 100 / (1 + exp(-0.8 × (years_since_shock - 2.5)))
```

---

## Parameter Calibration from Data

### Carrying Capacity Estimation (Bertocchi-Inspired)

```python
def calculate_capacity(destination):
    """Multi-subsystem capacity bottleneck model"""
    subsystems = {
        'accommodation': (
            destination.hotel_beds + 
            destination.extra_hotel_beds
        ) × 0.80,  # 80% occupancy rate
        
        'transport': (
            destination.airport_seats_per_year × 
            0.75  # 75% load factor
        ),
        
        'infrastructure': (
            destination.population × 
            0.15  # 15% can host tourists (assumption)
        ),
        
        'attractions': sum([
            site.capacity for site in destination.heritage_sites
        ])
    }
    
    # Bottleneck = minimum capacity
    overall_capacity = min(subsystems.values())
    return overall_capacity, subsystems
```

**Note**: This is an **estimation method**. Users can override with actual capacity data if available.

### Risk Score Calculation (Rosselló et al. Coefficient)

```python
def calculate_risk_score(acled_events, population):
    """Map ACLED conflict events to risk perception using Rosselló coefficient"""
    events_per_10k = (acled_events / population) × 10000
    
    # Rosselló et al. crime coefficient: -0.76
    # Transform to 0-1 risk perception scale
    risk_perception = 1 - exp(-0.76 × events_per_10k)
    
    return risk_perception  # Range: 0-1
```

### Social Media Utility Modifier (Leung et al. Framework)

```python
def social_media_modifier(destination, tourist):
    """Apply social media effects based on Leung et al. causal chain"""
    # UGC Quality (45.6% of studies - most important)
    ugc_quality = destination.avg_review_rating / 5.0  # Normalize to 0-1
    
    # UGC Quantity (36.2% of studies)
    review_volume = log(destination.num_reviews + 1) / log(10000 + 1)  # Normalize
    
    # Reviewer Expertise (22.8% of studies)
    reviewer_credibility = destination.avg_reviewer_expertise  # Assume 0-1 scale
    
    # Tourist segment sensitivity (user-configurable)
    sensitivity = tourist.social_media_sensitivity  # 0.0-1.0
    
    # Calculate modifier
    modifier = sensitivity × (
        0.45 × ugc_quality +
        0.36 × review_volume +
        0.23 × reviewer_credibility
    )
    
    return modifier  # Range: approximately 0-1
```

---

## Inferred Behavioral Rules

### Rule Format 1: Mathematical Utility Function

Each tourist agent maximizes utility when choosing a destination:

```
U(destination) = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk
```

**Where:**
- `α, β, γ, δ` = weight parameters (sum to 1.0)
- `Attractiveness` = composite score (0-100) based on WEF TTDI
- `Cost` = relative cost index (normalized 0-1)
- `Crowding` = current tourist density (tourists/capacity)
- `Risk` = composite risk factor (0-1)

**Recommended weights (baseline):**
- `α = 0.35` (attractiveness)
- `β = 0.25` (cost/affordability)
- `γ = 0.20` (crowding avoidance)
- `δ = 0.20` (risk sensitivity)

---

### Rule Format 2: Decision Tree

```
IF Risk > 0.7:
    → Skip destination (high risk threshold)
ELSE:
    IF Cost > budget_threshold:
        → Skip destination (unaffordable)
    ELSE:
        IF Crowding > 0.8:
            → Probability reduced by 50%
        ELSE:
            → Calculate utility score
            → Choose if utility > alternative_threshold
```

**Risk thresholds:**
- 0.0-0.3: Low risk (normal behavior)
- 0.3-0.5: Moderate risk (20% probability reduction)
- 0.5-0.7: High risk (50% probability reduction)
- 0.7-1.0: Critical risk (destination excluded)

---

### Rule Format 3: Weighted Scoring Model

**Step 1: Normalize all factors (0-100 scale)**

| Factor | Normalization Formula |
|--------|----------------------|
| Attractiveness | `WEF_TTDI_score` (already 0-100) |
| Affordability | `100 - Cost_Index` (inverse) |
| Low Crowding | `100 × (1 - current_density)` |
| Low Risk | `100 × (1 - risk_score)` |

**Step 2: Calculate weighted score**

```
Score = (0.35 × Attractiveness) + 
        (0.25 × Affordability) + 
        (0.20 × Low_Crowding) + 
        (0.20 × Low_Risk)
```

**Step 3: Choice probability (softmax)**

```
P(choose destination i) = exp(Score_i) / Σ exp(Score_all_destinations)
```

---

## Parameter Calibration from Data

### Seasonality Factor

Based on temporal patterns, introduce monthly variation:

```
Seasonality_Multiplier = 
    1.2 (peak season: Jun-Aug, Dec)
    1.0 (shoulder: Apr-May, Sep-Oct)
    0.8 (low: Jan-Mar)
```

### Risk Sensitivity Calibration

From literature on crisis impacts (not from synthetic data):
- **Risk elasticity**: Estimated -0.60 to -0.80 (based on Cohen et al. 2007)
- **Recovery lag**: 2-4 years for full recovery post-crisis (based on historical patterns)

### Crowding Tolerance

From pre-pandemic data:
- **Optimal density**: 60-70% capacity
- **Tolerance threshold**: 85% (sharp decline beyond this)
- **Avoidance behavior**: Increases exponentially above 80%

---

## Agent Heterogeneity

Not all tourists are identical. Introduce segments:

| Segment | α (Attract) | β (Cost) | γ (Crowd) | δ (Risk) | % of Population |
|---------|-------------|----------|-----------|----------|-----------------|
| Budget Travelers | 0.20 | 0.50 | 0.15 | 0.15 | 30% |
| Luxury Travelers | 0.50 | 0.15 | 0.15 | 0.20 | 20% |
| Adventure Seekers | 0.40 | 0.20 | 0.10 | 0.30 | 25% |
| Family Tourists | 0.30 | 0.30 | 0.25 | 0.15 | 25% |

---

## Emergent Patterns to Validate

The simulation should reproduce these observed patterns:

1. **Recovery curves**: Post-crisis S-shaped recovery
2. **Seasonal oscillation**: Regular annual patterns
3. **Hub formation**: Popular destinations attract more visitors (preferential attachment)
4. **Cascading effects**: Crisis in one region redirects flow to alternatives
5. **Carrying capacity limits**: Overcrowding leads to decline in attractiveness

---

## Known Limitations & Model Boundaries

### Critical Limitation: TTDI Explains Only 13% of Variance

**The Elephant in the Room**:
- TTDI correlation with arrivals: **r = 0.364**
- **R² = 0.13** → Only **13% of variance explained**
- **87% of variation** comes from factors NOT in our model

**Missing Factors** (not yet modeled):
1. **Geographic proximity** → ✅ NOW ADDED (distance friction term)
2. **Flight network connectivity** → ⚠️ Proxy via distance + GDP
3. **Cultural/linguistic affinity** → ❌ Not modeled (future enhancement)
4. **Visa policy/accessibility** → ✅ NOW MODELED via TFI (v2.1)
5. **Colonial/historical ties** → ❌ Not modeled (future enhancement)
6. **Marketing/advertising spend** → ❌ Not modeled (future enhancement)
7. **Resident attitudes/policy feedback** → ✅ NOW ADDED (TFI dynamics v2.1)

**Implication**: This model is **exploratory, NOT predictive**. It explores plausible dynamics under constraints, but should NOT be used for forecasting.

---

### Model Scope Boundaries

| What the Model DOES | What the Model DOES NOT Do |
|---------------------|---------------------------|
| Explore emergent patterns from utility-based choice | Predict exact tourist volumes |
| Test "what-if" scenarios (segment changes, shocks) | Forecast future tourism trends |
| Demonstrate complexity in global tourism | Replace econometric forecasting models |
| Validate theoretical mechanisms | Provide policy recommendations without calibration |

---

## Open Questions for Refinement

1. **Network effects**: Should word-of-mouth/recommendations influence choices? ✅ PARTIALLY ADDED (popularity feedback)
2. **Learning**: Do agents remember bad experiences and avoid repeat visits? ✅ YES (memory term)
3. **Loyalty**: Should there be a "home bias" or repeat visitation tendency? ✅ YES (return probability)
4. **Information asymmetry**: Do all agents have perfect information about destinations? ⚠️ PARTIALLY (choice set filtered by distance)
5. **Group behavior**: Should agents travel in groups or individually? ❌ Not modeled (individual agents)
6. **Flight network approximation**: Should we add connectivity proxy beyond distance? ⚠️ FUTURE (distance + GDP proxy suggested)
7. **Cultural affinity**: Should we add linguistic/colonial ties? ❌ FUTURE enhancement
8. **Resident attitudes**: Should tourism friendliness affect destination choice? ✅ ADDED as moderator (TFI, not utility factor)

---

## Next Steps

1. **Implement baseline simulation** with current rules
2. **Validate against historical data** (2010-2019 patterns)
3. **Stress-test with shocks** (simulate pandemic-like events)
4. **Refine parameters** based on fit to real data
5. **Add complexity incrementally** (network effects, learning, etc.)
6. **Implement TFI dynamics** (resident attitudes → policy feedback) ← NEW v2.1

---

## Data Sources Used

### Primary Data
- **World Bank Tourism Indicators** (2010-2019) - Baseline growth calibration
  - Location: `data/merged/tourism_observed_2010_2019.csv`
  - Coverage: ~20 regional aggregates
  - Variables: Arrivals, departures

### Literature-Based Parameters (Not from Data)
- **Attractiveness weights** - From WEF TTDI framework (data pending manual download)
- **Risk elasticity** - From Cohen et al. (2007) and tourism crisis literature
- **Recovery lag** - From historical crisis studies (no observed pandemic data used)
- **Seasonality** - From tourism seasonality literature
- **Crowding thresholds** - From overtourism case studies (Venice, Barcelona)

### Data Pending Manual Download
- WEF TTDI 2024 scores (no API; manual extraction required)
- UN Tourism country-level data (no API; manual download required)
- Risk indices (Fragile States Index, etc.)

**Note**: No synthetic or generated data is used. All parameters are either from observed data or academic literature.

---

*This is a living document. Update as simulation development reveals new insights.*
