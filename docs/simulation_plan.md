# Simulation Plan - Global Tourism Complexity

**Version**: 0.1 (Initial Requirements)  
**Date**: 2026-04-21  
**Status**: Requirements Gathering  

---

## 📋 User Requirements Tracker

| ID | Requirement | Status | Priority | Notes |
|----|-------------|--------|----------|-------|
| **REQ-001** | Average vacation duration by demographic | ⏳ Pending | High | For cyclic tourist flux |
| **REQ-002** | Two-level capacity thresholds with visual indicators | ⏳ Pending | High | Level 1 (low→medium), Level 2 (medium→high) + rectification suggestions |
| **REQ-003** | Seasonal trends + planned/unplanned events | ⏳ Pending | High | FIFA World Cup example, disasters/terrorism |
| **REQ-004** | Origin-destination restrictions (agent-level) | ⏳ Pending | Medium | North Korea ↔ South Korea example |
| **REQ-005** | Interactive pause, hover, click, segment statistics | ⏳ Pending | High | UI/UX requirements |

---

## 🔍 Requirement Details

### REQ-001: Vacation Duration by Demographic

**Goal**: Ensure cyclic flux movement of tourists (realistic stay durations)

**Questions to Resolve**:
- Should duration vary by segment (Budget/Luxury/Adventure/Family)?
- Should duration vary by destination type (nearby vs far)?
- Should duration vary by purpose (Business vs Personal)?

**Literature Search Needed**:
- Average trip duration by tourist segment
- Average trip duration by region (Europeans vs Americans vs Asians)
- Average trip duration by distance traveled

**Implementation Approach**:
```python
# In Tourist class
def __init__(self, segment, home_region):
    self.segment = segment
    self.home_region = home_region
    self.stay_duration = self._calculate_stay_duration()

def _calculate_stay_duration(self):
    # Base duration by segment
    base = {
        'budget': 7,      # days
        'luxury': 14,
        'adventure': 21,
        'family': 10
    }[self.segment]
    
    # Modifier by distance (farther = longer stays)
    distance_modifier = ...
    
    # Modifier by purpose
    purpose_modifier = ...
    
    return base * distance_modifier * purpose_modifier
```

**Data Sources**:
- UN Tourism: Average length of stay by origin-destination
- OECD: Tourism nights spent statistics
- Literature: Trip duration by segment

---

### REQ-002: Two-Level Capacity Thresholds

**Goal**: Visual crowding indicators + rectification suggestions

**Specification**:
- **Level 1 Threshold**: 50-60% capacity (low → medium crowding)
  - Visual: Color change (Green → Yellow)
  - No policy action yet
  
- **Level 2 Threshold**: 80-85% capacity (medium → high crowding)
  - Visual: Color change (Yellow → Orange/Red)
  - Trigger rectification suggestions

- **Critical Threshold**: >100% capacity (overcrowded)
  - Visual: Flashing Red
  - TFI decline accelerates
  - Policy restrictions activate

**Rectification Suggestions** (when > Level 2):
1. **Demand Management**:
   - Increase tourist taxes
   - Reduce marketing spend
   - Implement visitor caps
   
2. **Capacity Expansion**:
   - Invest in infrastructure
   - Approve more hotels
   - Expand attraction capacity
   
3. **Distribution**:
   - Promote alternative destinations
   - Seasonal pricing to spread demand
   - Redirect to nearby regions

**Implementation Approach**:
```python
class Destination:
    CAPACITY_THRESHOLDS = {
        'level_1': 0.55,   # 55% = yellow
        'level_2': 0.80,   # 80% = orange/red
        'critical': 1.0    # 100% = flashing red
    }
    
    @property
    def crowding_level(self):
        ratio = self.visitors / self.capacity
        if ratio < self.CAPACITY_THRESHOLDS['level_1']:
            return 'LOW', 'GREEN'
        elif ratio < self.CAPACITY_THRESHOLDS['level_2']:
            return 'MEDIUM', 'YELLOW'
        elif ratio < self.CAPACITY_THRESHOLDS['critical']:
            return 'HIGH', 'ORANGE'
        else:
            return 'CRITICAL', 'RED'
    
    def get_rectification_suggestions(self):
        if self.crowding_level[0] in ['HIGH', 'CRITICAL']:
            return [
                'Implement tourist tax increase',
                'Promote alternative destinations',
                'Cap daily arrivals',
                ...
            ]
        return []
```

**Visual Design**:
```
Capacity Utilization → Color
0-55%   → Green (#4CAF50)
55-80%  → Yellow (#FFC107)
80-100% → Orange (#FF9800)
>100%   → Red (#F44336) + pulse animation
```

---

### REQ-003: Seasonal Trends + Events System

**Goal**: Demonstrate seasonal patterns + event-driven tourism shifts

**Components**:

#### A. Baseline Seasonality
```python
def seasonality_multiplier(month, hemisphere):
    """Base seasonal pattern (±20% amplitude)"""
    if hemisphere == 'Northern':
        PEAK_MONTHS = [6, 7, 8, 12]      # Summer + Christmas
        SHOULDER_MONTHS = [4, 5, 9, 10]
        LOW_MONTHS = [1, 2, 3, 11]
    else:  # Southern
        PEAK_MONTHS = [12, 1, 2, 6, 7]   # Inverted
        ...
    
    if month in PEAK_MONTHS:
        return 1.2
    elif month in SHOULDER_MONTHS:
        return 1.0
    else:
        return 0.8
```

#### B. Planned Events (User-Configurable)
```python
class PlannedEvent:
    def __init__(self, name, country, start_date, end_date, event_type, magnitude):
        self.name = name  # e.g., "FIFA World Cup 2026"
        self.country = country
        self.start_date = start_date
        self.end_date = end_date
        self.event_type = event_type  # 'sports', 'cultural', 'business', 'festival'
        self.magnitude = magnitude  # 0.0-1.0 (impact strength)
        
        # Segment-specific appeal
        self.segment_appeal = {
            'budget': 0.6,      # Budget travelers interested
            'luxury': 0.8,      # Luxury travelers very interested
            'adventure': 0.5,   # Moderate
            'family': 0.9       # Families highly interested
        }

# Example: FIFA World Cup
fifa_2026 = PlannedEvent(
    name="FIFA World Cup 2026",
    country="United States",
    start_date=datetime(2026, 6, 1),
    end_date=datetime(2026, 7, 15),
    event_type="sports",
    magnitude=0.8,
    segment_appeal={'budget': 0.6, 'luxury': 0.8, 'adventure': 0.5, 'family': 0.9}
)

# Applied to utility function
def utility_with_event(destination, tourist, current_date):
    base_utility = calculate_base_utility(destination, tourist)
    
    # Check for active events
    for event in destination.active_events:
        if event.start_date <= current_date <= event.end_date:
            appeal = event.segment_appeal[tourist.segment]
            base_utility += event.magnitude * appeal * 0.5  # Bonus utility
    
    return base_utility
```

#### C. Unplanned Events (Shocks)
```python
class UnplannedEvent:
    def __init__(self, name, country, start_date, event_type, severity, duration_months):
        self.name = name  # e.g., "Terrorist Attack Paris 2026"
        self.country = country
        self.start_date = start_date
        self.event_type = event_type  # 'disaster', 'terrorism', 'epidemic', 'conflict'
        self.severity = severity  # 0.0-1.0
        self.duration_months = duration_months
        
        # Segment-specific impact
        self.segment_impact = {
            'budget': 0.5,      # Budget travelers less affected
            'luxury': 0.8,      # Luxury travelers highly affected
            'adventure': 0.3,   # Adventure seekers least affected
            'family': 0.9       # Families most affected
        }

# Example: Natural Disaster
earthquake = UnplannedEvent(
    name="Earthquake Japan 2026",
    country="Japan",
    start_date=datetime(2026, 5, 15),
    event_type="disaster",
    severity=0.7,
    duration_months=6
)

# Applied as risk multiplier
def risk_with_event(base_risk, destination, current_date):
    for event in destination.active_shocks:
        if event.start_date <= current_date:
            # Decay over time
            months_elapsed = (current_date - event.start_date).days / 30
            if months_elapsed < event.duration_months:
                decay_factor = 1.0 - (months_elapsed / event.duration_months)
                base_risk += event.severity * decay_factor
    
    return min(1.0, base_risk)
```

**UI Requirements**:
- Event calendar view (Gantt chart style)
- Event creation form (name, country, dates, type, magnitude)
- Event impact visualization (before/during/after comparison)
- Shock trigger button (for unplanned events)

---

### REQ-004: Origin-Destination Restrictions

**Goal**: Model political/cultural/visa restrictions (e.g., North Korea ↔ South Korea)

**Your Concern**: Is this computationally feasible and data-justifiable?

**Analysis**:

#### Computational Complexity
```python
# Approach 1: Full O-D matrix (177×177 = 31,329 pairs)
# For each tourist, check if destination is allowed
# Complexity: O(n) per tourist choice (acceptable)

# Approach 2: Restriction list per country (sparse representation)
# Each country has list of restricted origins
# Complexity: O(1) lookup with hash set (better)

# VERDICT: Computationally trivial with Approach 2
```

#### Data Availability
| Restriction Type | Data Source | Coverage | Confidence |
|-----------------|-------------|----------|------------|
| **Visa requirements** | IATA Timatic, Wikipedia | Global | **HIGH** ✅ |
| **Travel bans** | Government advisories | Partial | Medium |
| **Political tensions** | Polity IV, bilateral relations | Partial | Medium |
| **Cultural/religious** | Pew Research, World Values Survey | Partial | Low |

**Practical Approach**:
```python
# Restriction types
RESTRICTION_TYPES = {
    'VISA_FREE': 0.0,           # No restriction
    'VISA_ON_ARRIVAL': 0.1,     # Minor friction
    'E_VISA': 0.2,              # Some friction
    'VISA_REQUIRED': 0.4,       # Significant friction
    'RESTRICTED': 0.7,          # Very difficult
    'BANNED': 1.0               # Impossible
}

# Implementation
class Destination:
    # Sparse representation (only store restrictions, not all 176 origins)
    visa_restrictions = {
        'North Korea': 'BANNED',      # South Korea bans NK citizens
        'Iran': 'RESTRICTED',         # Some countries restrict
        ...
    }
    
    def check_accessibility(self, tourist_origin):
        restriction = self.visa_restrictions.get(tourist_origin, 'VISA_FREE')
        return RESTRICTION_TYPES[restriction]

# Applied to utility as friction
utility -= visa_friction * 0.5  # Reduce utility based on visa difficulty
```

**Recommendation**: 
- ✅ **Implement visa restrictions** (data available, computationally cheap)
- ⚠️ **Optional: Political tensions** (use Fragile States Index as proxy)
- ❌ **Skip: Cultural affinity** (too complex for Stage 2)

**Data Sources**:
- Henley Passport Index (visa-free scores)
- IATA Travel Centre (visa requirements by nationality)
- Wikipedia "Visa requirements for [nationality] citizens" pages

---

### REQ-005: Interactive UI (Pause, Hover, Click, Segment View)

**Goal**: Deep inspection capabilities during simulation

**Specification**:

#### A. Pause Functionality
```python
# Simulation state management
class Simulation:
    def __init__(self):
        self.paused = False
        self.tick = 0
        self.speed = 1.0  # 1x, 2x, 4x, 0.5x
    
    def toggle_pause(self):
        self.paused = not self.paused
    
    def step(self):
        if self.paused:
            return  # Don't advance
        self.tick += 1
        self.update_all_agents()
```

#### B. Hover Details (Tooltip)
```python
# Tourist tooltip (on hover)
{
    'Segment': 'Luxury',
    'Home': 'United States',
    'Current Destination': 'France',
    'Days Remaining': 8,
    'Utility Score': 0.73,
    'Memory': {'France': 0.65, 'Italy': 0.42}
}

# Destination tooltip (on hover)
{
    'Country': 'France',
    'Current Visitors': 42000,
    'Capacity': 50000,
    'Utilization': '84% (HIGH)',
    'TFI': 0.72,
    'Active Events': ['Paris Fashion Week'],
    'Risk Score': 0.15
}
```

#### C. Click Details (Detail Panel)
```python
# Tourist detail panel (on click)
{
    'Agent ID': 'T-004521',
    'Segment': 'Luxury',
    'Home Country': 'United States',
    'Home Region': 'Americas',
    
    # Current Trip
    'Destination': 'France',
    'Arrival Date': '2026-04-10',
    'Planned Duration': 14,
    'Days Remaining': 8,
    
    # Preferences
    'Utility Weights': {
        'Attractiveness': 0.50,
        'Cost': 0.15,
        'Crowding': 0.15,
        'Risk': 0.20
    },
    
    # History
    'Past Visits': [
        {'Country': 'Italy', 'Year': 2024, 'Satisfaction': 0.82},
        {'Country': 'Spain', 'Year': 2023, 'Satisfaction': 0.75}
    ],
    
    # Current State
    'State': 'STAYING',
    'Next Destination Choice': 'Pending (day 8)'
}

# Destination detail panel (on click)
{
    'Country': 'France',
    'Country Code': 'FR',
    'Region': 'Europe',
    
    # Capacity
    'Current Visitors': 42000,
    'Total Capacity': 50000,
    'Utilization': '84%',
    'Crowding Level': 'HIGH',
    
    # Subsystem Capacities
    'Accommodation': '45000 / 50000 (90%)',
    'Transport': '48000 / 55000 (87%)',
    'Infrastructure': '52000 / 60000 (87%)',
    'Attractions': '40000 / 45000 (89%)',
    
    # TFI
    'Tourism Friendliness': 0.72,
    'Trend': '↓ Declining (crowding > 80%)',
    
    # Metrics
    'TTDI Score': 5.07,
    'Cost Index': 76.2,
    'Risk Score': 0.15,
    
    # Events
    'Active Events': [
        {'Name': 'Paris Fashion Week', 'Type': 'cultural', 'Ends': '2026-04-25'}
    ],
    
    # History (last 12 months)
    'Arrivals Trend': [38000, 39500, 41000, 42000, ...]
}
```

#### D. Segment Statistics View
```python
# Separate dashboard tab: "Segment Statistics"

# Summary Cards
{
    'Budget': {
        'Active Tourists': 1240,
        'Avg Stay': 7.2,
        'Top Destination': 'Thailand',
        'Avg Satisfaction': 0.78,
        'Avg Spending': '$45/day'
    },
    'Luxury': {
        'Active Tourists': 680,
        'Avg Stay': 14.5,
        'Top Destination': 'France',
        'Avg Satisfaction': 0.85,
        'Avg Spending': '$320/day'
    },
    'Adventure': {
        'Active Tourists': 890,
        'Avg Stay': 21.3,
        'Top Destination': 'New Zealand',
        'Avg Satisfaction': 0.82,
        'Avg Spending': '$85/day'
    },
    'Family': {
        'Active Tourists': 1050,
        'Avg Stay': 10.8,
        'Top Destination': 'United States',
        'Avg Satisfaction': 0.80,
        'Avg Spending': '$150/day'
    }
}

# Charts
1. Segment Distribution (Pie Chart)
2. Avg Stay by Segment (Bar Chart)
3. Satisfaction by Segment (Radar Chart)
4. Destination Preferences by Segment (Stacked Bar)
5. Utility Weight Comparison (Parallel Coordinates)
```

**Technology Stack**:
- **Streamlit** for dashboard (pause, segment view, statistics)
- **Plotly** for interactive charts (hover tooltips)
- **Altair** for static visualizations
- **AgGrid** for data tables (sortable, filterable)

---

## 📅 Implementation Priority

### Phase 1 (Week 1-2): Core Mechanics
- [ ] **REQ-001**: Vacation duration by demographic
- [ ] **REQ-002**: Two-level capacity thresholds (backend only)
- [ ] Basic simulation loop (no UI yet)

### Phase 2 (Week 3-4): Events System
- [ ] **REQ-003**: Seasonal trends
- [ ] **REQ-003**: Planned events (FIFA example)
- [ ] **REQ-003**: Unplanned events (disasters)

### Phase 3 (Week 5-6): Restrictions & UI
- [ ] **REQ-004**: Visa/origin restrictions
- [ ] **REQ-005**: Pause functionality
- [ ] **REQ-005**: Hover tooltips
- [ ] **REQ-005**: Click details panel

### Phase 4 (Week 7-8): Advanced UI
- [ ] **REQ-005**: Segment statistics view
- [ ] **REQ-002**: Visual color indicators
- [ ] **REQ-002**: Rectification suggestions panel
- [ ] Polish & validation

---

## 🔍 Open Questions

| Question | Related REQ | Decision Needed |
|----------|-------------|-----------------|
| Vacation duration data sources? | REQ-001 | Literature search or assume? |
| Threshold values (55%, 80%)? | REQ-002 | Calibrate from literature or user-configurable? |
| Event magnitude scaling? | REQ-003 | How to quantify FIFA vs local festival? |
| Visa restriction data granularity? | REQ-004 | All 177 countries or top 50 only? |
| UI framework choice? | REQ-005 | Streamlit only or Streamlit + Pygame? |

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-04-21 | Initial requirements capture |

---

**Next Steps**:
1. Review and refine requirements with user
2. Prioritize features for MVP
3. Create technical specification document
4. Begin implementation (Phase 1)
