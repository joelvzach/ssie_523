# Dashboard Enhancement Implementation Plan

**Version**: 1.0  
**Date**: May 3, 2026  
**Status**: Ready for Implementation  

---

## Executive Summary

This document outlines a **phased, modular approach** to enhancing the Global Tourism Simulation dashboard with real-time updates, agent-level visualization, decision transparency, and complexity analysis features.

**Key Principles:**
- ✅ **Modular**: Each phase is independently testable
- ✅ **Low Risk**: Can stop at any phase with working system
- ✅ **Rollback-Safe**: Each phase can be reverted without breaking others
- ✅ **User-Triggered**: Advanced features only render when explicitly requested

---

## Current Issues to Address

### 1. Frame Rate Problem
**Current:** 10 FPS at 1× speed → 365 days renders in 36.5 seconds (too fast)  
**Target:** 1 FPS at 1× speed → 365 days renders in 365 seconds (6 minutes)

### 2. No Agent-Level Visibility
**Current:** Only map dots with basic tooltips  
**Target:** Detailed table showing agent status, with journey path filter

### 3. No Decision Transparency
**Current:** Agents choose destinations invisibly  
**Target:** Show utility breakdown when user clicks agent in CHOOSING state

### 4. Pre-Event Deviation Missing
**Current:** FIFA event only affects during event dates (June 1 - July 15)  
**Target:** Linear ramp-up starting 45 days before event (April 17)

### 5. No Complexity Demonstrations
**Current:** Basic time series and top destinations  
**Target:** 4 tabs showing capacity dynamics, TFI feedback, emergence, event impact

---

## Phase 1: Core Fixes (30 min) 🟢 LOW RISK

### Objective
Fix frame rate timing and add pre-event tourism deviation.

### Changes

#### 1.1 Frame Rate Adjustment
**File:** `simulation/visualization/dashboard.py`  
**Lines:** 607-609

```python
# CURRENT (line 607-609):
frame_time = 0.1 / st.session_state.speed  # 10 FPS at 1×
time.sleep(frame_time)

# PROPOSED:
frame_time = 1.0 / st.session_state.speed  # 1 FPS at 1×
time.sleep(frame_time)
```

**Impact:** 
- 1× speed: 365 ticks in 365 seconds (6 minutes) ✓
- 4× speed: 365 ticks in 91 seconds (1.5 minutes) ✓
- Renders every tick (smoother visualization)

**Test:** Run at 1× speed, verify 1 frame per second

---

#### 1.2 Pre-Event Linear Ramp
**File:** `simulation/events/planned_events.py`  
**Lines:** 16-98 (modify `__init__` and `get_utility_bonus`)

**Changes:**
1. Add `pre_event_days` parameter to `PlannedEvent.__init__`
2. Add linear ramp logic to `get_utility_bonus`
3. Update `create_fifa_world_cup_2026()` with `pre_event_days=45`

**Implementation:**
```python
# In __init__:
self.pre_event_days = pre_event_days
self.pre_event_start = start_date - timedelta(days=pre_event_days)

# In get_utility_bonus:
# Pre-event linear ramp (0% → 30% of full magnitude)
if self.pre_event_start <= tick_date < self.start_date:
    days_into_pre = (tick_date - self.pre_event_start).days
    ramp_factor = days_into_pre / self.pre_event_days  # Linear: 0.0 → 1.0
    appeal = self.segment_appeal.get(tourist_segment, 0.5)
    return self.magnitude * 0.3 * appeal * ramp_factor

# Post-event 15-day decline (20% → 0%)
days_since_end = (tick_date - self.end_date).days
if 0 < days_since_end <= 15:
    decline_factor = 1.0 - (days_since_end / 15)
    appeal = self.segment_appeal.get(tourist_segment, 0.5)
    return self.magnitude * 0.2 * appeal * decline_factor
```

**FIFA 2026 Update:**
```python
def create_fifa_world_cup_2026():
    return PlannedEvent(
        name="FIFA World Cup 2026",
        country_code="US",  # USA only
        start_date=datetime(2026, 6, 1),
        end_date=datetime(2026, 7, 15),
        magnitude=0.8,
        pre_event_days=45,  # Start ramp-up from April 17
        expected_footfall=1000000,
    )
```

**Test:** 
1. Run simulation to mid-April (day ~105)
2. Check USA destination utility - should see gradual increase
3. Verify peak during July 1-15
4. Verify decline through July 30

---

### Success Criteria
- [ ] Simulation runs at 1 frame per second at 1× speed
- [ ] FIFA event ramp-up visible from April 17
- [ ] Post-event decline visible through July 30

### Rollback Plan
Revert 2 files to previous commit:
```bash
git checkout HEAD~1 simulation/visualization/dashboard.py
git checkout HEAD~1 simulation/events/planned_events.py
```

---

## Phase 2: Agent Status Dashboard (40 min) 🟢 LOW RISK

### Objective
Show detailed agent status table when simulation is paused.

### Changes

#### 2.1 New Render Function
**File:** `simulation/visualization/dashboard.py`  
**Lines:** Add new function after `render_segment_breakdown()` (~line 350)

**Function Signature:**
```python
def render_agent_dashboard(sim):
    """
    Render detailed agent status table (visible when paused).
    
    Shows:
    - Agent ID, Category, Status, Duration, Days Until Next Trip
    - Summary charts (state distribution, segment mix, top destinations)
    """
```

**Data Structure:**
```python
agent_data = []
for agent in sim.agents:
    if agent.agent_id in sim.sampled_agent_ids:
        agent_data.append({
            "Name": agent.agent_id,
            "Category": agent.segment.capitalize(),
            "Status": agent.state,  # HOME/CHOOSING/TRAVELING/STAYING
            "Current Destination": agent.current_destination or "-",
            "Duration": f"{agent.stay_duration}d" if agent.state == "STAYING" else "-",
            "Days Until Next Trip": str(agent.days_until_next_trip) if agent.state == "HOME" else "",
        })
```

**UI Layout:**
```python
with st.expander("👥 Sampled Agent Status (100 agents)", expanded=True):
    # Table
    df = pd.DataFrame(agent_data)
    st.dataframe(df, use_container_width=True, height=350)
    
    # Summary charts (3 columns)
    col1, col2, col3 = st.columns(3)
    with col1:
        # State distribution pie chart
    with col2:
        # Segment distribution bar chart
    with col3:
        # Top current destinations bar chart
```

---

#### 2.2 Integration in Main Flow
**File:** `simulation/visualization/dashboard.py`  
**Lines:** After line 623 (after running check)

```python
# Show agent dashboard when paused
if sim and not st.session_state.running:
    st.divider()
    render_agent_dashboard(sim)
```

---

### Success Criteria
- [ ] Agent table appears when simulation is paused
- [ ] Shows 100 sampled agents with correct columns
- [ ] Summary charts render correctly
- [ ] Table disappears when simulation is running

### Rollback Plan
Remove `render_agent_dashboard()` function and its call:
```bash
git diff HEAD~1 simulation/visualization/dashboard.py  # Review changes
git checkout HEAD~1 simulation/visualization/dashboard.py  # Revert
```

---

## Phase 3: Journey Path Filter (30 min) 🟡 MEDIUM RISK

### Objective
Add tab to filter by individual agent and show journey path on mini-map.

### Changes

#### 3.1 Tab Interface
**File:** `simulation/visualization/dashboard.py`  
**Lines:** Modify `render_agent_dashboard()` function

**Structure:**
```python
tab1, tab2 = st.tabs(["All Agents", "🔍 Filter by Agent"])

with tab1:
    # Full table (existing code)
    pass

with tab2:
    # Dropdown to select agent
    selected_agent = st.selectbox("Select Agent:", options=sorted(df["Name"].unique()))
    
    if selected_agent:
        # Filter table to selected agent
        # Show journey trajectory
        # Render mini-map
```

---

#### 3.2 Mini-Map Visualization
**File:** `simulation/visualization/dashboard.py`  
**Lines:** Add new helper function

**Function:**
```python
def render_mini_map(trajectory, sim):
    """
    Render mini-map showing single agent's journey path.
    
    Args:
        trajectory: List of (tick, country_code) tuples
        sim: Simulation object (for country centroids)
    """
    # Create scatter plot with lines connecting visited countries
    # Highlight current location with larger marker
```

**Data Preparation:**
```python
# Convert trajectory to dataframe
journey_df = pd.DataFrame(trajectory, columns=["tick", "country_code"])

# Add coordinates
journey_df["lat"] = journey_df["country_code"].apply(
    lambda code: next(c for c in sim.countries_data if c["code"] == code)["lat"]
)
journey_df["lon"] = journey_df["country_code"].apply(
    lambda code: next(c for c in sim.countries_data if c["code"] == code)["lon"]
)
```

**Plot:**
```python
fig = go.Figure()

# Path lines
fig.add_trace(go.Scattergeo(
    lon=journey_df["lon"],
    lat=journey_df["lat"],
    mode="lines",
    line=dict(width=2, color="blue"),
    name="Journey Path",
))

# Current location (last point)
current = journey_df.iloc[-1]
fig.add_trace(go.Scattergeo(
    lon=[current["lon"]],
    lat=[current["lat"]],
    mode="markers",
    marker=dict(size=15, color="red"),
    name="Current Location",
))
```

---

### Success Criteria
- [ ] "Filter by Agent" tab appears
- [ ] Dropdown shows all 100 sampled agent IDs
- [ ] Selecting agent shows their journey table
- [ ] Mini-map displays path with current location highlighted

### Rollback Plan
Remove tab interface and mini-map function:
```bash
git checkout HEAD~1 simulation/visualization/dashboard.py
```

---

## Phase 4: Decision Breakdown (50 min) 🟠 MEDIUM-HIGH RISK

### Objective
Show utility breakdown when user clicks agent in CHOOSING state.

### Changes

#### 4.1 Capture Decision Data
**File:** `simulation/mechanics/choice.py`  
**Lines:** Modify `choose_destination()` function (~lines 107-151)

**Add Decision Tracking:**
```python
# Store decision breakdown
decision_data = {
    "agent_id": tourist.agent_id,
    "segment": tourist.segment,
    "home_country": tourist.home_country,
    "tick": tick,
    "destinations": [],
    "chosen": chosen.country_code if chosen else None,
}

for i, dest in enumerate(accessible):
    # Calculate factor breakdown
    decision_data["destinations"].append({
        "country_code": dest.country_code,
        "country_name": dest.country_name,
        "utility": utilities[i],
        "probability": probabilities[i],
        "factors": {
            "attractiveness": weights["α"] * att_norm,
            "cost": -weights["β"] * cost_norm,
            "crowding": -weights["γ"] * crowd_norm,
            "risk": -weights["δ"] * risk_norm,
            "distance": -weights["η"] * dist_norm,
            "memory": weights["ζ"] * memory_norm,
        },
    })

# Sort by probability
decision_data["destinations"].sort(key=lambda x: x["probability"], reverse=True)

# Store in agent for dashboard access
tourist.last_decision = decision_data
```

---

#### 4.2 Render Decision Breakdown
**File:** `simulation/visualization/dashboard.py`  
**Lines:** Add new function `render_agent_decision(agent, sim)`

**UI Structure:**
```python
def render_agent_decision(agent, sim):
    """Render decision breakdown for agent in CHOOSING state."""
    
    if not hasattr(agent, 'last_decision') or not agent.last_decision:
        st.warning("No decision data available")
        return
    
    decision = agent.last_decision
    
    st.subheader(f"🧠 Decision Breakdown: {agent.agent_id}")
    
    # Header metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Segment", agent.segment.capitalize())
    with col2:
        st.metric("Home Country", agent.home_country)
    with col3:
        st.metric("Chosen", decision["chosen"])
    
    # Top 10 choices table
    st.write("**Top 10 Destination Choices:**")
    # ... table with utility, probability, chosen marker
    
    # Factor breakdown bar chart
    st.write("**Factor Breakdown (Top 3):**")
    # ... Plotly bar chart showing factor contributions
    
    # Why chosen explanation
    st.write("**Why this destination was chosen:**")
    # ... Highlight strongest positive/negative factors
```

---

#### 4.3 Integration
**File:** `simulation/visualization/dashboard.py`  
**Lines:** In `render_agent_dashboard()`, tab 2

```python
with tab2:
    selected_agent = st.selectbox(...)
    
    if selected_agent:
        agent = next(a for a in sim.agents if a.agent_id == selected_agent)
        
        # Show decision breakdown if CHOOSING
        if agent.state == "CHOOSING":
            st.divider()
            render_agent_decision(agent, sim)
```

---

### Success Criteria
- [ ] Decision data captured during `choose_destination()`
- [ ] Breakdown appears when agent is in CHOOSING state
- [ ] Shows top 10 destinations with utility + probability
- [ ] Factor breakdown bar chart renders correctly
- [ ] "Why chosen" explanation is accurate

### Rollback Plan
Revert 3 files:
```bash
git checkout HEAD~1 simulation/mechanics/choice.py
git checkout HEAD~1 simulation/visualization/dashboard.py
# (No changes to collector.py in this approach)
```

---

## Phase 5: Complexity Analysis Charts (60 min) 🔴 HIGH RISK

### Objective
Add 4 tabs demonstrating complexity concepts (emergence, feedback loops, non-linearity).

### Changes

#### 5.1 Tab Structure
**File:** `simulation/visualization/dashboard.py`  
**Lines:** After line 651 (after segment breakdown)

```python
st.divider()
st.subheader("📊 Complexity Analysis")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏗️ Capacity Dynamics",
    "🔄 TFI Feedback",
    "📈 Emergent Patterns",
    "🎯 Event Impact"
])

with tab1:
    render_capacity_shifts(sim)
with tab2:
    render_tfi_feedback(sim)
with tab3:
    render_emergence_chart(sim)
with tab4:
    render_event_impact_chart(sim)
```

---

#### 5.2 Chart Functions

**All 4 functions added to `dashboard.py`:**

1. **`render_capacity_shifts(sim)`** - Stacked area chart of top 10 destinations by capacity utilization
2. **`render_tfi_feedback(sim)`** - Scatter plot of TFI vs crowding (feedback loop visualization)
3. **`render_emergence_chart(sim)`** - Gini coefficient over time with target range
4. **`render_event_impact_chart(sim)`** - Actual vs baseline arrivals with event shading

**Helper Function (for emergence):**
```python
def calculate_gini(values):
    """Calculate Gini coefficient."""
    n = len(values)
    if n == 0 or sum(values) == 0:
        return 0.0
    
    sorted_values = sorted(values)
    cumsum = np.cumsum(sorted_values)
    return (2 * sum((i + 1) * v for i, v in enumerate(sorted_values)) - (n + 1) * cumsum[-1]) / (n * cumsum[-1])
```

---

### Success Criteria
- [ ] All 4 tabs render without errors
- [ ] Capacity chart shows top 10 destinations
- [ ] TFI scatter shows feedback loop pattern
- [ ] Gini chart shows inequality evolution
- [ ] Event impact shows deviation from baseline

### Rollback Plan
Remove complexity tabs section:
```bash
git checkout HEAD~1 simulation/visualization/dashboard.py
```

---

## Implementation Schedule

### Recommended Order (Highest Impact First)

| Phase | Time | Risk | Priority | Dependencies |
|-------|------|------|----------|--------------|
| **Phase 1** | 30 min | 🟢 Low | **HIGH** | None |
| **Phase 2** | 40 min | 🟢 Low | **HIGH** | Phase 1 |
| **Phase 4** | 50 min | 🟠 Med-High | MEDIUM | Phase 2 |
| **Phase 3** | 30 min | 🟡 Medium | LOW | Phase 2 |
| **Phase 5** | 60 min | 🔴 High | LOW | Phase 1 |

**Total Time:** ~210 minutes (3.5 hours) for all phases

**Minimum Viable Enhancement (Phases 1-2):** ~70 minutes
- ✅ Frame rate fix (critical for usability)
- ✅ Pre-event deviation (demonstrates planning)
- ✅ Agent status table (shows agent-level detail)

---

## Testing Protocol

### After Each Phase

1. **Run simulation** at 1× speed for 30 seconds
2. **Verify** phase-specific success criteria
3. **Check** existing features still work
4. **Commit** if all tests pass

### After All Phases

**Full Test Suite:**
1. Initialize simulation
2. Run at 1× speed for 100 ticks
3. Pause, verify agent table appears
4. Select agent in CHOOSING state, verify decision breakdown
5. Open all 4 complexity tabs, verify charts render
6. Trigger unplanned event, verify impact visible
7. Switch to 4× speed, verify performance acceptable

---

## Risk Mitigation

### General Strategies

1. **Frequent Commits:** Commit after each phase
2. **Git Branches:** Consider feature branches for Phases 4-5
3. **Logging:** Add debug logs for decision capture
4. **Graceful Degradation:** Features only render when explicitly requested

### Known Risks

| Risk | Phase | Mitigation |
|------|-------|------------|
| Performance degradation at 4× speed | Phase 1 | Monitor frame time, can add frame skipping |
| Decision data structure too large | Phase 4 | Store only top 10 destinations, not all |
| Mini-map rendering slow | Phase 3 | Use scatter instead of choropleth |
| Complexity charts memory usage | Phase 5 | Calculate on-demand, don't cache |

---

## Success Metrics

### Quantitative
- Frame rate: 1.0 ± 0.1 FPS at 1× speed
- Agent table render time: < 2 seconds
- Decision breakdown render time: < 3 seconds
- Complexity chart render time: < 5 seconds each

### Qualitative
- User can see agent-level detail when paused ✓
- User can understand why agent chose destination ✓
- Complexity concepts demonstrated (emergence, feedback, non-linearity) ✓
- Pre-event tourism deviation visible ✓

---

## Post-Implementation

### Documentation Updates
- [ ] Update `simulation/visualization/README.md` with new features
- [ ] Add screenshot examples to docs
- [ ] Update user guide with decision breakdown feature

### Future Enhancements (Not in Scope)
- Real-time agent trajectory animation on map
- Agent-to-agent interaction modeling
- Multi-country event support (e.g., FIFA across USA/Canada/Mexico)
- Export decision data to CSV for analysis

---

**Approval to Proceed:**  
Phases 1-2 approved for implementation by Joel.  
Phases 3-5 pending testing of Phases 1-2.

**Next Steps:**
1. Implement Phase 1 (frame rate + pre-event)
2. Implement Phase 2 (agent dashboard)
3. Test and commit
4. Await user feedback before proceeding to Phases 3-5

---

**Document Status**: Ready for Implementation  
**Last Updated**: May 3, 2026  
**Owner**: Simulation Development Team
