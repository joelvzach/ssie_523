# Interactive Dashboard - Global Tourism Simulation

## Quick Start

```bash
# Option 1: Use the launch script
cd /Users/joelvzach/Code/ssie_523/simulation
python launch_dashboard.py

# Option 2: Run directly with Streamlit
streamlit run visualization/dashboard.py

# Option 3: From project root
cd /Users/joelvzach/Code/ssie_523
streamlit run simulation/visualization/dashboard.py
```

The dashboard will open in your default browser at `http://localhost:8501`

---

## Features

### 🗺️ Interactive Map
- **Choropleth visualization**: Countries colored by capacity utilization
  - 🟢 Green = Low crowding (<55%)
  - 🟡 Yellow = Medium crowding (55-80%)
  - 🟠 Orange = High crowding (80-100%)
  - 🔴 Red = Critical crowding (>100%)
- **Agent dots**: 100 sampled agents shown as colored dots
  - 🔵 Blue = Budget segment
  - 🟠 Orange = Luxury segment
  - 🟢 Green = Adventure segment
  - 🔴 Red = Family segment

### 📊 Real-Time Charts
1. **Time Series**: Daily arrivals over simulation history
2. **Top 10 Destinations**: Bar chart of most-visited countries
3. **Segment Breakdown**: Pie chart of active travelers by segment

### 🎮 Controls

**Sidebar Controls**:
- **▶️ Run / ⏸️ Pause**: Start/stop simulation
- **Speed Slider**: 0.5×, 1×, 2×, 4× simulation speed
- **⏹️ Stop**: Reset simulation
- **🌋 Natural Disaster**: Trigger random disaster event
- **🦠 Epidemic Outbreak**: Trigger random epidemic event
- **💾 Save Configuration**: Save scenario (coming soon)

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Title + Summary Metrics (4 cards)                  │
├─────────────────────────────────────────────────────────────┤
│  [Map: 60% width]              │  [Charts: 40% width]      │
│                                │                            │
│  - Choropleth (crowding)       │  - Time Series (line)     │
│  - Agent dots (sampled)        │  - Top 10 (bar)           │
│                                │  - Segment (pie)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Guide

### 1. Initialize Simulation
- Click **"Initialize Simulation"** button in sidebar
- Creates 4,000 agents and 177 destinations
- Pre-loads FIFA World Cup 2026 as example planned event

### 2. Run Simulation
- Click **"▶️ Run"** to start
- Watch agents travel in real-time
- Adjust speed with slider (0.5× to 4×)

### 3. Trigger Events
- Click **"🌋 Natural Disaster"** to trigger random disaster
- Click **"🦠 Epidemic Outbreak"** to trigger epidemic
- Watch arrivals drop in affected countries

### 4. Inspect Destinations
- **Coming soon**: Click on country to see details
- View capacity, TFI, crowding level, policy suggestions

### 5. Monitor Metrics
- **Active Travelers**: Agents currently traveling
- **Total Trips**: Cumulative trips recorded
- **Sampled Agents**: 100 agents tracked for visualization

---

## Technical Details

### Dependencies
- `streamlit>=1.28.0` - Dashboard framework
- `plotly>=5.18.0` - Interactive visualizations
- `pandas>=2.0.0` - Data processing

### Performance
- **Target**: 30 FPS for 100-agent animation
- **Actual**: Depends on hardware and simulation speed
- **Optimization**: Uses WebGL rendering via Plotly

### Data Flow
```
Simulation Step → Update Agents/Destinations → 
Collect Data → Render Map + Charts → Repeat
```

---

## Known Limitations

| Limitation | Status | Workaround |
|------------|--------|------------|
| Click-to-inspect countries | Not implemented | View summary metrics in charts |
| Agent detail panel | Not implemented | Hover over agent dots for basic info |
| Scenario save/load | Not implemented | Use seed for reproducibility |
| Historical data scrubbing | Not implemented | Time series shows full history |

---

## Troubleshooting

### Dashboard won't start
```bash
# Check if Streamlit is installed
pip list | grep streamlit

# Reinstall if needed
pip install streamlit plotly
```

### Map doesn't show agents
- Ensure simulation has been running for at least 1 tick
- Check that agents are in TRAVELING state (not HOME)

### Charts are empty
- Run simulation for at least 2 ticks to see time series
- Top 10 chart requires active travelers

### Performance is slow
- Reduce simulation speed to 0.5× or 1×
- Close other browser tabs
- Check system resources (CPU/RAM)

---

## Future Enhancements

**Planned Features**:
- [ ] Click-to-inspect destinations (full detail panel)
- [ ] Agent inspection panel (click on agent dot)
- [ ] Scenario save/load (JSON export/import)
- [ ] Time scrubber (jump to specific date)
- [ ] Segment filters (show/hide segments)
- [ ] Export data (CSV download)
- [ ] Screenshot export (PNG)
- [ ] Event calendar view (Gantt chart)

---

## Support

For issues or questions:
1. Check this README
2. Review console output for error messages
3. Verify dependencies are installed: `pip list`

---

**Dashboard Version**: 1.0 (Phase 3 Initial Release)  
**Last Updated**: 2026-04-21
