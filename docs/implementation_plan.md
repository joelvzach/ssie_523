# Stage 2 Implementation Plan - Global Tourism Simulation

**Version**: 2.0  
**Date**: May 1, 2026  
**Status**: ✅ COMPLETE - All Phases 1-4 Delivered  

---

## Overview

**Goal**: Build agent-based simulation with 4,000 tourist agents making destination choices based on 6-factor utility function.

**Timeline**: 4 phases (Core → Events → Dashboard → Validation)

**Key Parameters**:
- 4,000 agents (Budget 30%, Luxury 20%, Adventure 25%, Family 25%)
- 177 countries (top 50 in choice set)
- 1 tick = 1 day
- 6-factor utility: Attractiveness, Cost, Crowding, Risk, Distance, Memory

---

## Phase 1-4: Complete Implementation Summary

### ✅ Phase 1: Core Simulation - COMPLETE
- [x] Tourist agent class with state machine
- [x] Destination class with capacity + TFI
- [x] 8-factor utility function (Attractiveness, Cost, Crowding, Risk, Distance, Popularity, Social Media, Memory)
- [x] Softmax choice mechanism with segment-specific temperature
- [x] Distance matrix (pre-computed, 31K pairs)
- [x] Simulation loop (daily ticks)
- [x] Data collector
- [x] Tier 1 validation tests

### ✅ Phase 2: Events & TFI - COMPLETE
- [x] Seasonality (±20% amplitude, hemisphere-aware)
- [x] TFI dynamics (decline/recovery with hysteresis)
- [x] Visa restrictions (192 country pairs, 6 levels)
- [x] Planned events framework (FIFA World Cup example)
- [x] Unplanned events framework (disasters, terrorism)

### ✅ Phase 3: Dashboard & UI - COMPLETE
- [x] Streamlit dashboard with choropleth visualization
- [x] Interactive controls (pause, speed, segment config)
- [x] Hover tooltips and click details
- [x] Real-time metrics panel
- [x] Scenario save/load

### ✅ Phase 4: GDP Integration & Validation - COMPLETE
- [x] World Bank GDP loader (262 countries)
- [x] Tourism dependency calculator (98 countries)
- [x] TFI modifier (highly dependent >30% = 50% slower decline)
- [x] OECD validation (r = 0.795)
- [x] Sensitivity analysis (15 simulations)
- [x] Segment distribution calibration (RMSE 3.1%)
- [x] Country code mapping (100%: 177/177)
- [x] Data duplication fix (TOTAL indicator filtering)

### File Structure
```
simulation/
├── __init__.py
├── agents/
│   ├── __init__.py
│   └── tourist.py
├── destinations/
│   ├── __init__.py
│   └── destination.py
├── mechanics/
│   ├── __init__.py
│   ├── utility.py
│   ├── choice.py
│   └── distance.py
├── dynamics/
│   ├── __init__.py
│   └── seasonality.py
├── data/
│   ├── __init__.py
│   ├── visa_restrictions.py    # Already exists ✅
│   ├── loaders.py
│   └── country_climate.py
├── data_collection/
│   ├── __init__.py
│   └── collector.py
├── validation/
│   ├── __init__.py
│   └── baseline.py
└── simulation.py
```

### Key Implementations

#### 1. Tourist Agent (`agents/tourist.py`)
```python
class Tourist:
    Attributes:
    - home_country: str
    - segment: str ('budget'/'luxury'/'adventure'/'family')
    - purpose: str ('business'/'personal')
    - state: str ('HOME'/'CHOOSING'/'TRAVELING')
    - current_destination: str or None
    - arrival_date: int (tick)
    - stay_duration: int (days)
    - days_until_next_trip: int
    - visited_destinations: dict[code → satisfaction]
    - utility_weights: dict[α,β,γ,δ,η,ζ]
    - segment_temperature: float
    
    Methods:
    - __init__(segment, home_country)
    - step() → decrement counters, trigger state changes
    - should_start_trip(current_month) → bool
    - choose_destination(destinations) → country_code
    - return_home()
```

**Trip Frequency** (Poisson process):
```python
TRIPS_PER_YEAR = {
    'budget': 0.75,
    'luxury': 3.0,
    'adventure': 1.5,
    'family': 0.75
}

BUSINESS_PROBABILITY = {
    'budget': 0.15,
    'luxury': 0.40,
    'adventure': 0.05,
    'family': 0.00
}
```

**Stay Duration**:
```python
BASE_STAY = {
    'budget': 7,
    'luxury': 14,
    'adventure': 21,
    'family': 10
}

# 80% follow distance trend
if random.random() < 0.80:
    if distance_km < 1000:      duration = base × 0.7
    elif distance_km < 5000:    duration = base × 1.0
    else:                       duration = base × 1.4
else:
    duration = base × random.uniform(0.5, 2.0)
```

---

#### 2. Destination (`destinations/destination.py`)
```python
class Destination:
    Attributes:
    - country_code: str
    - country_name: str
    - capacity: int (hotel_beds × 0.80 × 1.10)
    - current_visitors: int (rolling 30-day)
    - tfi: float (0.0-1.0, starts at 0.80)
    - attractiveness: float (TTDI normalized)
    - cost_index: float (Numbeo normalized)
    - risk_score: float (ACLED-derived)
    - climate_zone: str ('Northern'/'Southern'/'Tropical')
    - arrivals_history: list
    - tfi_history: list
    
    Methods:
    - __init__(country_code, data)
    - update(tick) → update TFI, rolling visitor count
    - get_crowding_ratio() → float (0.0-2.0+)
    - get_effective_capacity() → int (TFI-modified)
    - get_seasonal_multiplier(month) → float (0.8-1.2)
```

**TFI Dynamics**:
```python
if crowding_ratio > 0.80:
    tfi = max(0.0, tfi - 0.05)  # Fast decline
else:
    tfi = min(1.0, tfi + 0.02)  # Slow recovery

# Policy thresholds
if tfi < 0.40:
    effective_capacity = base × 0.70
elif tfi < 0.60:
    effective_capacity = base × 0.85
```

---

#### 3. Utility Function (`mechanics/utility.py`)
```python
def calculate_utility(tourist, destination, tick):
    # Normalize all factors to 0-1
    att = normalize(destination.attractiveness, 2.78, 5.24)
    cost = normalize(destination.cost_index, 26.6, 135.8)
    crowd = min(destination.get_crowding_ratio(), 2.0)
    risk = destination.risk_score
    dist = distance_km / 20000.0
    memory = destination.get_memory_score(tourist)  # -1 to +1
    
    # Segment weights (sum to 1.0)
    w = tourist.utility_weights
    
    utility = (
        w['α'] * att
        - w['β'] * cost
        - w['γ'] * crowd
        - w['δ'] * risk
        - w['η'] * dist
        + w['ζ'] * memory
    )
    
    # Business purpose modifier (Peng et al.)
    if tourist.purpose == 'business':
        utility += w['β'] * cost * 0.7  # Less cost-sensitive
    
    # Event bonus
    utility += get_event_bonus(destination, tourist, tick)
    
    # Visa friction
    utility -= get_visa_friction(destination, tourist.home_country)
    
    return utility
```

**Segment Weights**:
```python
SEGMENT_WEIGHTS = {
    'budget':    {'α':0.20, 'β':0.27, 'γ':0.11, 'δ':0.08, 'η':0.34, 'ζ':0.05},
    'luxury':    {'α':0.28, 'β':0.12, 'γ':0.09, 'δ':0.09, 'η':0.17, 'ζ':0.15},
    'adventure': {'α':0.28, 'β':0.10, 'γ':0.09, 'δ':0.11, 'η':0.22, 'ζ':0.15},
    'family':    {'α':0.21, 'β':0.18, 'γ':0.14, 'δ':0.14, 'η':0.40, 'ζ':0.02},
}

SEGMENT_TEMPERATURE = {
    'budget': 1.2,    # More random exploration
    'luxury': 0.8,    # More deterministic
    'adventure': 1.5, # Highly exploratory
    'family': 1.0,    # Moderate
}
```

---

#### 4. Choice Mechanism (`mechanics/choice.py`)
```python
def choose_destination(tourist, destinations, tick):
    # 1. Filter by visa (exclude BANNED only)
    accessible = [
        d for d in destinations
        if visa_lookup(d.country_code, tourist.home_country) != 'BANNED'
    ]
    
    # 2. Calculate utilities
    utilities = [
        calculate_utility(tourist, dest, tick)
        for dest in accessible
    ]
    
    # 3. Softmax with segment temperature
    tau = SEGMENT_TEMPERATURE[tourist.segment]
    max_u = max(utilities)  # Numerical stability
    exp_utils = [math.exp((u - max_u) / tau) for u in utilities]
    total = sum(exp_utils)
    probs = [e / total for e in exp_utils]
    
    # 4. Weighted random choice
    return weighted_random_choice(accessible, probs)
```

---

#### 5. Distance Matrix (`mechanics/distance.py`)
```python
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def precompute_distance_matrix(countries):
    """One-time cost: ~0.1 seconds"""
    matrix = {}
    for origin in countries:
        for dest in countries:
            if origin != dest:
                dist = haversine(origin.lat, origin.lon, dest.lat, dest.lon)
                matrix[(origin.code, dest.code)] = dist
    return matrix

def get_distance(origin_code, dest_code, matrix):
    """O(1) lookup"""
    return matrix.get((origin_code, dest_code), 0.0)
```

---

#### 6. Seasonality (`dynamics/seasonality.py`)
```python
def assign_climate_zone(latitude):
    if abs(latitude) < 23.5:
        return 'Tropical'
    elif latitude >= 23.5:
        return 'Northern'
    else:
        return 'Southern'

SEASONAL_PATTERNS = {
    'Northern': {
        1:0.8, 2:0.8, 3:0.8, 4:1.0, 5:1.0, 6:1.2,
        7:1.2, 8:1.2, 9:1.0, 10:1.0, 11:0.8, 12:1.2
    },
    'Southern': {
        1:1.2, 2:1.2, 3:1.0, 4:1.0, 5:0.8, 6:1.2,
        7:1.2, 8:0.8, 9:1.0, 10:1.0, 11:0.8, 12:1.2
    },
    'Tropical': {
        1:1.2, 2:1.2, 3:1.0, 4:1.0, 5:0.8, 6:0.8,
        7:1.2, 8:1.2, 9:1.0, 10:1.0, 11:0.8, 12:1.2
    },
}
```

---

#### 7. Data Collector (`data_collection/collector.py`)
```python
class DataCollector:
    Attributes:
    - global_arrivals: list
    - global_active: list
    - segment_arrivals: dict[segment → list]
    - segment_avg_stay: dict[segment → list]
    - dest_visitors: dict[code → list]
    - dest_capacity_util: dict[code → list]
    - dest_tfi: dict[code → list]
    - sampled_agent_ids: set (100 agents)
    - agent_trajectories: dict[agent_id → list[(tick, country)]]
    - trip_records: list[dict]
    
    Methods:
    - record(tick, agents, destinations)
    - get_summary() → dict
    - export_csv(path)
```

---

#### 8. Simulation Loop (`simulation.py`)
```python
class Simulation:
    def __init__(self, config):
        self.config = config
        self.agents = self._create_agents()
        self.destinations = self._create_destinations()
        self.distance_matrix = precompute_distance_matrix(self.destinations)
        self.tick = 0
        self.data_collector = DataCollector()
        self.paused = False
        
    def _create_agents(self):
        agents = []
        for segment, share in SEGMENT_SHARES.items():
            count = int(4000 * share)
            for _ in range(count):
                home = sample_home_country()
                agents.append(Tourist(segment, home))
        return agents
    
    def step(self):
        if self.paused:
            return
        
        # 1. Update destinations
        for dest in self.destinations:
            dest.update(self.tick)
        
        # 2. Agents make decisions
        for agent in self.agents:
            if agent.state == 'HOME':
                if agent.should_start_trip(get_month(self.tick)):
                    dest_code = agent.choose_destination(
                        self.destinations[:50],  # Top 50
                        self.distance_matrix
                    )
                    agent.travel_to(dest_code, self.tick)
            elif agent.state == 'TRAVELING':
                agent.step()  # Decrement stay counter
                if agent.stay_complete():
                    agent.return_home()
        
        # 3. Collect data
        self.data_collector.record(self.tick, self.agents, self.destinations)
        
        self.tick += 1
    
    def run(self, steps=365):
        for _ in range(steps):
            self.step()
```

---

#### 9. Validation Tests (`validation/baseline.py`)
```python
def test_cagr_2010_2019(sim):
    """Target: 3.0-4.5% CAGR"""
    sim.run(365*10)  # 10 years
    arrivals_2010 = sim.data_collector.global_arrivals[0]
    arrivals_2019 = sim.data_collector.global_arrivals[-1]
    cagr = (arrivals_2019 / arrivals_2010) ** (1/10) - 1
    assert 0.03 <= cagr <= 0.045, f"CAGR {cagr:.2%} outside target"

def test_pandemic_shock(sim):
    """Target: -65% to -75% drop in 2020"""
    inject_shock('pandemic', tick=365*10, magnitude=-0.70)
    sim.run(365)
    drop = calculate_drop(sim.data_collector.global_arrivals)
    assert 0.65 <= drop <= 0.75, f"Shock {drop:.2%} outside target"

def test_recovery_2024(sim):
    """Target: 90-100% of 2019 levels"""
    sim.run(365*4)  # 2020-2024
    recovery = sim.data_collector.global_arrivals[-1] / baseline_2019
    assert 0.90 <= recovery <= 1.00, f"Recovery {recovery:.2%} outside target"
```

---

## Phase 2: Events & Dynamics

### New Files
```
simulation/
├── events/
│   ├── __init__.py
│   ├── planned_events.py
│   └── unplanned_events.py
└── dynamics/
    └── recovery.py
```

### Planned Events (`events/planned_events.py`)
```python
class PlannedEvent:
    def __init__(self, name, country_code, start_date, end_date, 
                 magnitude, segment_appeal):
        self.name = name
        self.country_code = country_code
        self.start_date = start_date  # datetime
        self.end_date = end_date
        self.magnitude = magnitude  # 0.0-1.0
        self.segment_appeal = {
            'budget': 0.6,
            'luxury': 0.8,
            'adventure': 0.5,
            'family': 0.9
        }  # Example
    
    def get_utility_bonus(self, tourist_segment, days_from_peak):
        # Bell curve distribution
        peak_bonus = self.segment_appeal[tourist_segment] * self.magnitude
        curve_factor = math.exp(-days_from_peak**2 / 100)
        return peak_bonus * curve_factor
```

### Unplanned Events (`events/unplanned_events.py`)
```python
class UnplannedEvent:
    def __init__(self, name, country_code, start_tick, 
                 event_type, severity, duration_months):
        self.name = name
        self.country_code = country_code
        self.start_tick = start_tick
        self.event_type = event_type  # 'disaster'/'terrorism'/'epidemic'
        self.severity = severity  # 0.0-1.0
        self.duration_months = duration_months
        self.segment_impact = {
            'budget': 0.5,
            'luxury': 0.8,
            'adventure': 0.3,
            'family': 0.9
        }
    
    def get_risk_multiplier(self, tourist_segment, ticks_elapsed):
        decay = 1.0 - (ticks_elapsed / (self.duration_months * 30))
        base_impact = self.segment_impact[tourist_segment]
        return 1.0 + (self.severity * base_impact * decay)
```

---

## Phase 3: Interactive Dashboard

### New Files
```
simulation/
├── visualization/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── map_view.py
│   ├── charts.py
│   └── controls.py
└── scenario/
    ├── __init__.py
    └── save_load.py
```

### Dashboard Layout (`visualization/dashboard.py`)
```python
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Global Tourism Simulation")
with col2:
    st.metric("Simulation Day", sim.tick)

# Controls
pause_play = st.toggle("Pause")
speed = st.selectbox("Speed", ["0.5×", "1×", "2×", "4×"])

# Main layout
col_map, col_charts = st.columns([60, 40])

with col_map:
    # Choropleth base
    fig_map = px.choropleth(
        data_frame=dest_data,
        locations="country_code",
        color="crowding_ratio",
        color_continuous_scale="RdYlGn_r"
    )
    
    # Add agent sample overlay
    fig_map.add_scattergeo(
        lon=agent_lons,
        lat=agent_lats,
        mode="markers",
        marker=dict(size=6, color=agent_colors)
    )
    
    st.plotly_chart(fig_map, use_container_width=True)

with col_charts:
    # Time series
    st.line_chart(sim.data_collector.global_arrivals)
    
    # Top 10 destinations
    st.bar_chart(top_10_data)
    
    # Click details panel
    selected = st.session_state.get("selected_country")
    if selected:
        show_destination_details(selected)
```

### Scenario Save Format (`scenario/save_load.py`)
```json
{
  "metadata": {
    "scenario_name": "Baseline 2026",
    "created_at": "2026-04-21T10:30:00Z",
    "simulation_version": "1.0.0"
  },
  "configuration": {
    "segment_shares": {
      "budget": 0.30,
      "luxury": 0.20,
      "adventure": 0.25,
      "family": 0.25
    },
    "trip_frequencies": {
      "budget": 0.75,
      "luxury": 3.0,
      "adventure": 1.5,
      "family": 0.75
    },
    "utility_weights": {...},
    "tfi_parameters": {
      "baseline": 0.80,
      "decline_rate": 0.05,
      "recovery_rate": 0.02,
      "crowding_threshold": 0.80
    },
    "planned_events": [
      {
        "name": "FIFA World Cup 2026",
        "country_code": "US",
        "start_date": "2026-06-01",
        "end_date": "2026-07-15",
        "magnitude": 0.8,
        "segment_appeal": {...}
      }
    ]
  },
  "initial_state": {
    "seed": 42,
    "start_date": "2026-01-01",
    "agent_count": 4000,
    "duration_days": 365
  }
}
```

---

## Phase 4: Validation & Polish

### Validation Tiers

**Tier 1: Aggregate (Must Pass)**
- [ ] CAGR 2010-2019: 3.0-4.5%
- [ ] Pandemic shock 2020: -65% to -75%
- [ ] Recovery 2024: 90-100% of 2019

**Tier 2: Distributional (Should Pass)**
- [ ] Gini coefficient: 0.60-0.80
- [ ] Top 10 share: 40-60%
- [ ] Intra-regional Europe: 55-75%

**Tier 3: Emergent (Nice to Have)**
- [ ] Hub formation detected
- [ ] Regional clustering observed
- [ ] Congestion spillover present

**Tier 4: Sensitivity (Robustness)**
- [ ] Segment weights ±20%: model stable
- [ ] TFI threshold 75-85%: behavior consistent
- [ ] Trip frequency ±50%: no crashes

### Performance Targets
- [ ] 4,000 agents, 177 countries
- [ ] <1 second per timestep (1× speed)
- [ ] <2GB RAM usage
- [ ] 30 FPS animation for 100-agent sample

---

## Implementation Checklist

### Phase 1
- [ ] Create directory structure
- [ ] Implement `agents/tourist.py`
- [ ] Implement `destinations/destination.py`
- [ ] Implement `mechanics/utility.py`
- [ ] Implement `mechanics/choice.py`
- [ ] Implement `mechanics/distance.py`
- [ ] Implement `dynamics/seasonality.py`
- [ ] Implement `data/loaders.py`
- [ ] Implement `data/country_climate.py`
- [ ] Implement `data_collection/collector.py`
- [ ] Implement `simulation.py`
- [ ] Implement `validation/baseline.py`
- [ ] Run Tier 1 validation tests

### Phase 2
- [ ] Implement `events/planned_events.py`
- [ ] Implement `events/unplanned_events.py`
- [ ] Implement `dynamics/recovery.py`
- [ ] Integrate events with utility function
- [ ] Test event scenarios

### Phase 3
- [ ] Implement `visualization/dashboard.py`
- [ ] Implement `visualization/map_view.py`
- [ ] Implement `visualization/charts.py`
- [ ] Implement `visualization/controls.py`
- [ ] Implement `scenario/save_load.py`
- [ ] Test dashboard interactions
- [ ] Optimize rendering performance

### Phase 4
- [ ] Run Tier 2 validation tests
- [ ] Run Tier 3 pattern detection
- [ ] Run Tier 4 sensitivity analysis
- [ ] Performance profiling and optimization
- [ ] Write README documentation
- [ ] Write user guide
- [ ] Final testing and bug fixes

---

## Quick Reference: Key Formulas

### Utility Function
```
U = α·A - β·C - γ·Cr - δ·R - η·D + ζ·M + Events - Visa
```

### Softmax Choice
```
P(i) = exp(U_i / τ) / Σ_j exp(U_j / τ)
```

### TFI Update
```
if crowding > 0.80: TFI -= 0.05
else:               TFI += 0.02
```

### Trip Probability
```
p = (trips_per_year / 365) × seasonal_mod × event_mod
```

### Stay Duration
```
if random < 0.80:
    duration = base × distance_factor
else:
    duration = base × random(0.5, 2.0)
```

### Distance (Haversine)
```
a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
c = 2·atan2(√a, √(1-a))
d = R·c  (R = 6371 km)
```

---

**Ready to begin Phase 1 implementation.**
