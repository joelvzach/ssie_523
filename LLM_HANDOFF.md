# 🤖 LLM Handoff Document - Global Tourism Simulation

**Project**: SSIE 523 - Global Tourism Complexity Simulation  
**Status**: Plan Mode Complete ✅, Ready for Implementation  
**Last Updated**: 2026-04-21  
**Handoff Version**: 1.0  

---

## 🎯 Quick Start for New LLM

**Read these files first** (in order):
1. `docs/simulation_plan.md` - User requirements (REQ-001 to 005)
2. `PRD.md` - Project requirements (v2.1 with TFI dynamics)
3. `docs/literature_parameters.md` - All parameters with citations
4. `simulation/data/visa_restrictions.py` - Already complete (working code)

**Then start implementation** at: `simulation/agents/tourist.py`

---

## 📋 Project Overview

### Goal
Build an agent-based simulation where tourist agents make destination choices based on an **8-factor utility function**, leading to emergent patterns like hub formation, overtourism, and policy feedback loops.

### Core Philosophy
*"Use what we have, acknowledge what we don't"*
- ✅ Data-driven where possible (UN Tourism, WEF, ACLED)
- ⚠️ Literature-informed where data gaps exist (Bertocchi, Rosselló)
- ❌ No fabricated proxies (if we don't have data, acknowledge the limitation)

---

## ✅ What's Already Complete

### 1. Visa Restriction Lookup Module
**Location**: `simulation/data/visa_restrictions.py`

**Features**:
- 192 restricted country pairs pre-configured
- 6 restriction levels (VISA_FREE → BANNED)
- Friction coefficients (0.0 to 1.0) for utility function
- Sparse representation (efficient lookup)
- Comprehensive citations (Henley Passport Index 2024, IATA)

**Test It**:
```bash
cd simulation/data
python visa_restrictions.py
```

**Expected Output**:
```
North Korea → South Korea: BANNED (1.00 friction)
Iran → United States: BANNED (1.00 friction)
China → France: VISA_REQUIRED (0.40 friction)
US → France: VISA_FREE (0.00 friction)
```

### 2. Documentation (All in `docs/`)
| File | Purpose | Status |
|------|---------|--------|
| `PRD.md` | Project requirements (v2.1) | ✅ Complete |
| `simulation_plan.md` | User requirements (REQ-001 to 005) | ✅ Complete |
| `literature_parameters.md` | All parameters with citations | ✅ Complete |
| `literature_review_summary.md` | 5 papers reviewed | ✅ Complete |
| `inferred_rules.md` | Behavioral rules | ✅ Complete |
| `data_dictionary.md` | Variable definitions | ✅ Complete |
| `UPDATE_SUMMARY_TFI_v2.1.md` | TFI dynamics summary | ✅ Complete |

### 3. Data Sources (All in `data/`)
| Source | Location | Coverage | Use |
|--------|----------|----------|-----|
| UN Tourism Arrivals | `data/UN_Tourism/extracted/` | 215 countries, 1995-2024 | Baseline, validation |
| UN Tourism Hotel Beds | `data/UN_Tourism/extracted/` | 180 countries | **Capacity calculation** |
| WEF TTDI | `data/WEF/ttdi_scores_2024.csv` | 119 countries | Attractiveness (α) |
| Numbeo Cost | `data/enhanced_data/` | 156 countries | Affordability (β) |
| ACLED Conflict | `data/ACLED/` | Global, 1997-2026 | Risk perception (δ) |
| Country Centroids | `data/derived/` | 177 countries | Distance calculation (η) |

---

## 🏗️ Architecture Overview

### Utility Function (8 Factors)

```python
U = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk 
    - η·Distance + θ·Popularity + ε·SocialMedia + ζ·Memory
    + EventBonus - VisaFriction
```

| Factor | Symbol | Data Source | Confidence |
|--------|--------|-------------|------------|
| Attractiveness | α | WEF TTDI (0-100 scale) | **HIGH** ✅ |
| Cost | β | Numbeo Cost Index | **HIGH** ✅ |
| Crowding | γ | Hotel beds × 80% occupancy | **HIGH** ✅ |
| Risk | δ | ACLED conflict events | **HIGH** ✅ |
| Distance | η | Haversine (pre-computed matrix) | **HIGH** ✅ |
| Popularity | θ | Log-scale arrivals (endogenous) | **MEDIUM** ⚠️ |
| Social Media | ε | Placeholder (0.5) | **LOW** ⚠️ |
| Memory | ζ | Agent history (satisfaction scores) | **MEDIUM** ⚠️ |

### Segment-Specific Weights

| Segment | α | β | γ | δ | η | θ | ε | ζ | **τ (Temperature)** |
|---------|---|---|---|---|---|---|---|---|---------------------|
| **Budget** | 0.18 | 0.24 | 0.10 | 0.07 | 0.30 | 0.04 | 0.03 | 0.04 | **1.2** |
| **Luxury** | 0.24 | 0.10 | 0.08 | 0.08 | 0.15 | 0.12 | 0.10 | 0.13 | **0.8** |
| **Adventure** | 0.25 | 0.09 | 0.08 | 0.10 | 0.20 | 0.08 | 0.07 | 0.13 | **1.5** |
| **Family** | 0.18 | 0.16 | 0.12 | 0.12 | 0.35 | 0.03 | 0.02 | 0.02 | **1.0** |

### Agent Choice Mechanism

**Process** (Softmax Probabilistic Choice):
1. Filter destinations by visa restrictions
2. Calculate utility for each destination (top 50 by 2019 arrivals)
3. Apply softmax with segment-specific temperature (τ)
4. Random draw based on probabilities

```python
def choose_destination(tourist, destinations, current_date):
    # 1. Filter by visa
    accessible = [d for d in destinations 
                  if visa_lookup.is_accessible(d.name, tourist.home_country)]
    
    # 2. Calculate utilities
    utilities = [calculate_utility(tourist, dest, current_date) 
                 for dest in accessible]
    
    # 3. Softmax (segment-specific temperature)
    tau = tourist.segment_temperature  # Budget=1.2, Luxury=0.8, etc.
    probabilities = softmax(utilities, tau)
    
    # 4. Random draw
    return weighted_random_choice(accessible, probabilities)
```

---

## 📋 User Requirements (REQ-001 to 005)

### REQ-001: Vacation Duration by Demographic
**Decision**: Base duration × distance modifier (90% follow trend)

```python
def calculate_duration(segment, distance_km):
    base = {'budget': 7, 'luxury': 14, 'adventure': 21, 'family': 10}[segment]
    
    if random.random() < 0.90:  # 90% follow trend
        if distance_km < 1000:      return int(base * 0.7)
        elif distance_km < 5000:    return int(base * 1.0)
        else:                       return int(base * 1.4)
    else:  # 10% exceptions
        return int(base * random.uniform(0.5, 2.0))
```

### REQ-002: Two-Level Capacity Thresholds
**Decision**: Auto-apply restrictions (no user intervention)

| Threshold | Utilization | Color | Action |
|-----------|-------------|-------|--------|
| **Level 1** | 55% | Yellow | Warning only |
| **Level 2** | 80% | Orange | TFI starts declining |
| **Critical** | 100% | Red + pulse | Auto-apply restrictions |

```python
if crowding_ratio > 0.80:
    destination.tfi -= 0.05  # Fast decline
elif crowding_ratio > 0.55:
    pass  # Warning only (yellow)

if destination.tfi < 0.4:
    effective_capacity = base_capacity * 0.70  # Severe restrictions
elif destination.tfi < 0.6:
    effective_capacity = base_capacity * 0.85  # Moderate restrictions
```

### REQ-003: Seasonal Trends + Events
**Decision**: User inputs planned events before simulation; unplanned events triggered mid-sim

**Planned Events** (user input):
- Name, start/end date, location, expected footfall, segment tags (multiselect)
- Example: FIFA World Cup 2026, USA, Jun 1 - Jul 15, 1M footfall, tags=[Family, Luxury]
- Distribution: Bell curve (build up → peak → decline)

**Unplanned Events** (mid-simulation):
- User pauses → clicks country → selects "Trigger Event" → chooses type + severity
- Types: disaster, terrorism, epidemic
- Impact: Segment-specific (Family most affected, Adventure least)

**Seasonality** (baseline ±20%):
```python
def seasonality_multiplier(month, hemisphere):
    if hemisphere == 'Northern':
        if month in [6, 7, 8, 12]:      return 1.2  # Peak
        elif month in [4, 5, 9, 10]:    return 1.0  # Shoulder
        else:                           return 0.8  # Low
```

### REQ-004: Origin-Destination Restrictions
**Decision**: Pre-populate from Henley/IATA (already complete in `visa_restrictions.py`)

- 192 restricted country pairs
- 6 levels: VISA_FREE (0.0), VISA_ON_ARRIVAL (0.1), E_VISA (0.2), VISA_REQUIRED (0.4), RESTRICTED (0.7), BANNED (1.0)
- Applied as utility friction: `utility -= visa_friction * 0.5`

### REQ-005: Interactive UI
**Decision**: Overlay summary statistics (collapsible panel)

**Features**:
- Pause/play button
- Speed control: 0.5×, 1×, 2×, 4× (1 tick = 1 day)
- Hover tooltips (Plotly)
- Click detail panels (Streamlit side panel)
- Overlay statistics panel (segment-level metrics)

---

## 🚧 Implementation Phases

### Phase 1 (Week 1-2): Core Mechanics
- [ ] Create `simulation/agents/tourist.py`
  - Home country, segment, memory
  - Stay duration calculation (REQ-001)
  - Utility function (8 factors)
- [ ] Create `simulation/destinations/destination.py`
  - Hotel bed capacity (UN Tourism data)
  - Crowding ratio calculation
  - TFI dynamics
- [ ] Create `simulation/dynamics/choice.py`
  - Softmax choice mechanism
  - Segment-specific temperature
- [ ] Create `simulation/data/distance_matrix.py`
  - Pre-compute 31K distance pairs
  - O(1) lookup
- [ ] Create `simulation/visualization/base.py`
  - Basic country nodes (color-coded by crowding)
  - Tourist dots (color-coded by segment)

### Phase 2 (Week 3-4): Events & TFI
- [ ] Create `simulation/dynamics/seasonality.py`
  - Baseline ±20% amplitude
  - Hemisphere-aware
- [ ] Create `simulation/events/planned_events.py`
  - User input form (before simulation)
  - Bell curve footfall distribution
  - Segment-specific appeal
- [ ] Create `simulation/events/unplanned_events.py`
  - Mid-simulation trigger (click country)
  - Type selection (disaster/terrorism/epidemic)
  - Severity slider
- [ ] Create `simulation/dynamics/tfi.py`
  - TFI update loop (decline/recovery rates)
  - Policy restrictions (auto-apply)
  - Hysteresis modeling

### Phase 3 (Week 5-6): UI/UX
- [ ] Create `simulation/visualization/dashboard.py` (Streamlit)
  - Pause/play controls
  - Speed selector
  - Hover tooltips (Plotly)
  - Click detail panels
- [ ] Create `simulation/visualization/overlay.py`
  - Segment statistics panel
  - Collapsible design
- [ ] Create `simulation/visualization/context_menu.py`
  - "Trigger Event" option on country click
  - Event type selection dialog

### Phase 4 (Week 7-8): Validation & Polish
- [ ] Create `simulation/validation/baseline.py`
  - Validate against 2019 arrivals (should be 60-80% capacity)
  - CAGR validation (3.69% target)
- [ ] Create `simulation/validation/sensitivity.py`
  - Segment weight variations
  - TFI threshold sensitivity
- [ ] Performance optimization
  - Target: 177 countries, 10K tourists, <1s per tick
- [ ] Documentation
  - README for each module
  - Inline docstrings

---

## 📊 Key Parameters Reference

### Capacity Calculation
```python
def calculate_capacity(country):
    """
    Use ONLY UN Tourism hotel bed data.
    No fabricated proxies.
    """
    hotel_beds = get_un_tourism_data(country, 'hotel_beds')
    capacity = hotel_beds * 0.80  # Bertocchi et al. (2020) assumption
    return int(capacity)
```

### TFI Dynamics
```python
# Parameters (from Muler González et al., Cheung & Li)
TFI_BASELINE = 0.80
TFI_DECLINE_RATE = 0.05  # per tick when crowding > 80%
TFI_RECOVERY_RATE = 0.02  # per tick (hysteresis: slower than decline)
CROWDING_THRESHOLD = 0.80

# Policy thresholds
TFI_SEVERE_THRESHOLD = 0.40   # Capacity × 0.70
TFI_MODERATE_THRESHOLD = 0.60 # Capacity × 0.85
```

### Distance Matrix
```python
# Pre-compute at startup (one-time cost: ~0.1 seconds)
def precompute_distance_matrix(countries):
    """
    Calculate all pairwise distances (177×177 = 31,329 pairs)
    Cache in memory for O(1) lookup during simulation
    """
    distance_matrix = {}
    for origin in countries:
        for dest in countries:
            if origin != dest:
                dist_km = haversine(origin.lat, origin.lon, dest.lat, dest.lon)
                distance_matrix[(origin.code, dest.code)] = dist_km
    return distance_matrix

# Usage during simulation (instant lookup)
distance_km = distance_matrix[(tourist.home_country, destination.code)]
```

### Softmax Choice
```python
def softmax_choice(destinations, utilities, tau):
    """
    Convert utilities to probabilities using softmax with temperature.
    
    tau (temperature):
    - Budget: 1.2 (more random exploration)
    - Luxury: 0.8 (more deterministic, choose best)
    - Adventure: 1.5 (highly exploratory)
    - Family: 1.0 (moderate randomness)
    """
    max_u = max(utilities)  # Numerical stability
    exp_utils = [math.exp((u - max_u) / tau) for u in utilities]
    total = sum(exp_utils)
    probabilities = [e / total for e in exp_utils]
    
    # Weighted random choice
    r = random.random()
    cumsum = 0.0
    for dest, prob in zip(destinations, probabilities):
        cumsum += prob
        if cumsum >= r:
            return dest
    return destinations[-1]  # Fallback
```

---

## ⚠️ Known Limitations (Acknowledge in Documentation)

| Limitation | Why | Mitigation |
|------------|-----|------------|
| **Accommodation-only capacity** | No data for transport/restaurant/attractions | Acknowledge as lower-bound estimate |
| **Social media placeholder** | No empirical data available | Use 0.5, note in docs |
| **Segment shares assumed** | No empirical data (30/20/25/25 split) | User-configurable in dashboard |
| **Top 50 countries only** | Computational efficiency | Note for future expansion to 177 |
| **No flight network** | No connectivity data | Distance-only, visa restrictions capture political barriers |
| **City-level not modeled** | Only country-level data available | Defer to Stage 3 |

---

## 🛠️ Technical Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| **Language** | Python 3.10+ | Team familiarity |
| **ABM Framework** | Mesa (or custom) | Agent-based modeling |
| **Dashboard** | Streamlit | Interactive, easy to build |
| **Visualization** | Plotly | Hover tooltips, interactive charts |
| **Data Processing** | pandas, numpy | Standard stack |
| **Geographic** | Custom haversine | No external dependency needed |
| **Testing** | pytest | Automated validation |

---

## 📚 Literature Citations (Key Sources)

| Concept | Citation | Confidence |
|---------|----------|------------|
| **Capacity (80% occupancy)** | Bertocchi et al. (2020), Sustainability 12(2):512 | **HIGH** ✅ |
| **80% crowding threshold** | Muler González et al. (2018), Tourism Review 73(3):277-292 | **HIGH** ✅ |
| **TFI hysteresis** | Cheung & Li (2019), J. Sustainable Tourism 27(8):1197-1216 | **MEDIUM** ⚠️ |
| **Shock elasticities** | Rosselló et al. (2020), Tourism Management 79:104080 | **HIGH** ✅ |
| **Recovery patterns** | Škare et al. (2021), Technological Forecasting 163:120469 | **HIGH** ✅ |
| **Visa restrictions** | Henley Passport Index 2024, IATA Travel Centre | **HIGH** ✅ |
| **Segment weights** | Literature-informed assumptions | **LOW** ⚠️ |

---

## 🔄 Immediate Next Steps

1. **Read all documentation** in `docs/` folder (start with `simulation_plan.md`)
2. **Test visa_restrictions.py** to ensure it works:
   ```bash
   cd simulation/data
   python visa_restrictions.py
   ```
3. **Start Phase 1** implementation:
   - Create `simulation/agents/tourist.py`
   - Create `simulation/destinations/destination.py`
   - Create `simulation/dynamics/choice.py`
4. **Implement distance matrix** pre-computation
5. **Build utility function** with 8 factors
6. **Test softmax choice** with sample agents

---

## ❓ Open Decisions (If User Hasn't Specified)

1. **GDP Data**: User indicated download from World Bank (for flight proxy in Stage 3)
   - Action: Add to `data/World_Bank/gdp_current_usd.csv`
   - Coverage: 199 countries, 1990-2024
   - Source: World Bank API (free)

2. **Tourist Population**: Not yet specified
   - Recommendation: Start with 1,000-5,000 agents (debugging), scale to 10K-50K (production)

3. **Validation Target**: Not yet specified
   - Recommendation: Compare to 2019 peak arrivals (should be 60-80% of capacity)

---

## 📞 If You Get Stuck

1. **Check `docs/literature_parameters.md`** for parameter values
2. **Check `simulation_plan.md`** for user requirements
3. **Check `visa_restrictions.py`** for example implementation pattern
4. **Ask the user** for clarification on open decisions

---

**Good luck with implementation! 🚀**
