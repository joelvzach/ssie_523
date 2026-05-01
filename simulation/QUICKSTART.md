# 🌍 Global Tourism Simulation - Quick Start Guide

## Installation

```bash
# Navigate to project root
cd /Users/joelvzach/Code/ssie_523

# Install dashboard dependencies (if not already installed)
pip install streamlit plotly
```

---

## Launch Dashboard

### Option 1: Launch Script (Recommended)
```bash
cd simulation
python launch_dashboard.py
```

### Option 2: Direct Streamlit Command
```bash
streamlit run simulation/visualization/dashboard.py
```

### Option 3: From Project Root
```bash
cd /Users/joelvzach/Code/ssie_523
streamlit run simulation/visualization/dashboard.py
```

**Dashboard opens at**: `http://localhost:8501`

---

## How to Use the Dashboard

### Step 1: Initialize
1. Click **"Initialize Simulation"** in the sidebar
2. Wait for loading (creates 4,000 agents + 177 destinations)
3. FIFA World Cup 2026 is pre-loaded as example event

### Step 2: Run Simulation
1. Click **"▶️ Run"** button
2. Watch agents travel on the map (colored dots)
3. Charts update in real-time

### Step 3: Adjust Speed
- Use speed slider: **0.5×** (slow), **1×** (normal), **2×**, **4×** (fast)

### Step 4: Trigger Events
- Click **"🌋 Natural Disaster"** to see impact on arrivals
- Click **"🦠 Epidemic Outbreak"** for pandemic-style shock
- Watch affected countries turn red (high crowding) or see arrivals drop

### Step 5: Monitor Metrics
- **Active Travelers**: Agents currently traveling
- **Total Trips**: Cumulative trip count
- **Time Series**: Daily arrivals trend
- **Top 10**: Most popular destinations

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🌍 Global Tourism Simulation                               │
│  Day X | Active: Y | Trips: Z | Sampled: 100               │
├─────────────────────────────────────────────────────────────┤
│  [Interactive Map - 60%]       │  [Charts - 40%]           │
│                                │                            │
│  Countries colored by:         │  1. Time Series (line)    │
│  🟢 Green = Low crowding       │  2. Top 10 (bar)          │
│  🟡 Yellow = Medium            │  3. Segment (pie)         │
│  🟠 Orange = High              │                            │
│  🔴 Red = Critical             │                            │
│                                │                            │
│  Dots = Sampled agents         │                            │
│  (colored by segment)          │                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 🗺️ Map Visualization
- **Choropleth colors**: Show capacity utilization (crowding)
- **Agent dots**: 100 sampled agents (one per segment)
- **Hover**: See country details (visitors, capacity, TFI)

### 📊 Charts
1. **Time Series**: Daily arrivals over simulation history
2. **Top 10 Destinations**: Bar chart of most-visited countries
3. **Segment Breakdown**: Pie chart showing traveler distribution

### 🎮 Controls
- **Run/Pause**: Start and stop simulation
- **Speed**: Adjust simulation speed
- **Stop**: Reset and reinitialize
- **Trigger Events**: Add disasters/epidemics mid-simulation

---

## Example Scenarios

### Scenario 1: Baseline Run
1. Initialize simulation
2. Run for 365 days at 2× speed
3. Observe natural tourism patterns
4. Check segment distribution in pie chart

### Scenario 2: FIFA World Cup Impact
1. Initialize (FIFA 2026 pre-loaded)
2. Run until June 2026 (Day ~150)
3. Watch USA arrivals spike
4. See segment breakdown shift (more Family travelers)

### Scenario 3: Disaster Response
1. Initialize and run for 30 days
2. Click **"🌋 Natural Disaster"**
3. Watch affected country's arrivals drop
4. Observe recovery over time

### Scenario 4: Epidemic Simulation
1. Initialize and run for 30 days
2. Click **"🦠 Epidemic Outbreak"**
3. Run for 365 days to see full impact
4. Compare recovery to historical patterns

---

## Troubleshooting

### Dashboard won't start
```bash
# Check if Streamlit is installed
pip list | grep streamlit

# Install if missing
pip install streamlit plotly
```

### Map shows no agents
- Run simulation for at least 5-10 days
- Agents need time to start traveling
- Check "Active Travelers" metric (should be >0)

### Charts are empty
- Run simulation for at least 2 ticks
- Time series needs historical data
- Top 10 needs active travelers

### Performance is slow
- Reduce speed to 0.5× or 1×
- Close other browser tabs
- Check system resources

---

## What's Working

✅ **4,000 tourist agents** with realistic behavior  
✅ **177 countries** with capacity constraints  
✅ **6-factor utility function** (segment-specific)  
✅ **Planned events** (FIFA World Cup example)  
✅ **Unplanned events** (disasters, epidemics)  
✅ **Real-time visualization** (map + charts)  
✅ **Trip recording** (149 trips in 10 days test)  
✅ **100-agent sample** tracking  

---

## Known Limitations (Phase 3)

⏳ **Click-to-inspect**: Country details panel (coming soon)  
⏳ **Agent inspection**: Click on agent dots for details  
⏳ **Scenario save/load**: Export/import configurations  
⏳ **Time scrubber**: Jump to specific dates  
⏳ **Data export**: CSV download of results  

---

## Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Initialization time | <5 seconds | ✅ ~2 seconds |
| Agents created | 4,000 | ✅ 4,000 |
| Destinations | 177 | ✅ 177 |
| Trips per day | ~15 | ✅ ~15 (149 in 10 days) |
| Dashboard refresh | <1 second | ✅ Real-time |

---

## Next Steps

After exploring the dashboard:

1. **Review documentation**:
   - `docs/progress_report.md` - Project status
   - `docs/implementation_plan.md` - Technical details
   - `simulation/visualization/README.md` - Dashboard guide

2. **Experiment with scenarios**:
   - Try different event combinations
   - Adjust segment shares
   - Test shock recovery patterns

3. **Provide feedback**:
   - What features would you add?
   - What visualizations are most useful?
   - Any bugs or issues encountered?

---

## Support

**Dashboard Version**: 1.0 (Phase 3 Initial Release)  
**Last Updated**: 2026-04-21

For issues or questions:
1. Check this guide
2. Review `simulation/visualization/README.md`
3. Check console output for error messages

---

**Happy Simulating! 🌍✈️**
