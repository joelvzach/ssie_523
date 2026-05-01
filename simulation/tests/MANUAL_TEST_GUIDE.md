# Manual Dashboard Testing Guide

## Automated Tests: PASSED ✅

All 6 logic tests passed:
- ✅ Simulation creation (4,000 agents, 177 destinations)
- ✅ Single step (tick advances correctly)
- ✅ Multiple steps (10 days simulation)
- ✅ Event trigger (disaster creation)
- ✅ Risk multiplier (elevated risk after disaster)
- ✅ Speed calculation (frame time logic)

---

## Manual Testing Checklist

### Test 1: Dashboard Launch
- [ ] Run: `cd /Users/joelvzach/Code/ssie_523 && python simulation/launch_dashboard.py`
- [ ] Browser opens to `http://localhost:8501`
- [ ] Welcome screen appears with "Initialize Simulation" button
- [ ] No console errors (F12 → Console tab)

**Expected**: Dashboard loads in <3 seconds

---

### Test 2: Initialize Simulation
- [ ] Click **"Initialize Simulation"** button (sidebar)
- [ ] Wait for loading spinner
- [ ] Summary metrics appear (4 cards at top)
- [ ] Map appears (colored countries)
- [ ] Charts appear (right side)

**Expected**: 
- "Simulation Day: Day 0"
- "Active Travelers: 0"
- "Total Trips: 0"
- "Sampled Agents: 100"

**Check terminal for**:
```
INFO - Initialized simulation state: None
INFO - Initialized running state: False
INFO - Simulation initialized: 4000 agents, 177 destinations
```

---

### Test 3: Run Button
- [ ] Click **"▶️ Run"** button
- [ ] Button changes to **"⏸️ Pause"**
- [ ] Simulation Day counter increments
- [ ] Active Travelers count increases
- [ ] Map shows colored dots (agents)
- [ ] Time series chart populates

**Expected**:
- Tick advances every ~100ms (at 1× speed)
- Active travelers: ~15-20 after 1 day
- Dots appear on map (colored by segment)

**Check terminal for**:
```
INFO - Toggled running state: True
INFO - Simulation tick: 100, active travelers: XX
```

---

### Test 4: Pause Button
- [ ] Click **"⏸️ Pause"** button
- [ ] Button changes back to **"▶️ Run"**
- [ ] Simulation Day counter STOPS
- [ ] Wait 5 seconds, verify tick doesn't change

**Expected**: Tick counter freezes

**Check terminal for**:
```
INFO - Toggled running state: False
```

---

### Test 5: Step Button
- [ ] Ensure simulation is PAUSED
- [ ] Click **"⏭️ Step (1 day)"** button
- [ ] Tick advances by exactly 1
- [ ] Click 3 more times, verify tick advances +1 each time

**Expected**: Precise control over simulation advancement

**Check terminal for**:
```
INFO - Manual step: tick XX
```

---

### Test 6: Speed Slider
- [ ] Set speed to **0.5×** (slow)
- [ ] Click Run, observe tick advances slowly (~1 every 200ms)
- [ ] Set speed to **2.0×** (fast)
- [ ] Observe tick advances quickly (~2 steps every 50ms)
- [ ] Set speed to **4.0×** (very fast)
- [ ] Observe rapid advancement

**Expected**: Visible difference in tick advancement speed

---

### Test 7: Disaster Event
- [ ] Click **"🌋 Natural Disaster"** button
- [ ] Success message appears: "Disaster triggered in [country]"
- [ ] Check terminal for disaster log
- [ ] Continue running simulation
- [ ] Watch affected country's arrivals drop (over next few ticks)

**Expected**:
```
INFO - Disaster triggered in [country_code]
```

---

### Test 8: Epidemic Event
- [ ] Click **"🦠 Epidemic Outbreak"** button
- [ ] Success message appears
- [ ] Check terminal log
- [ ] Run for 30+ days to see prolonged impact

**Expected**:
```
INFO - Epidemic triggered in [country_code]
```

---

### Test 9: Stop Button (Two-Click Confirm)
- [ ] Click **"⏹️ Stop"** button once
- [ ] Button changes to **"⚠️ Confirm Stop"**
- [ ] Click again
- [ ] Dashboard returns to welcome screen
- [ ] Must click "Initialize Simulation" to restart

**Expected**: Prevents accidental resets

---

### Test 10: Charts Update
- [ ] Run simulation for 30+ days
- [ ] Verify time series chart shows arrivals trend
- [ ] Verify top 10 destinations updates
- [ ] Verify segment pie chart shows distribution

**Expected**:
- Time series: Line chart with daily arrivals
- Top 10: Bar chart (countries may vary)
- Segment pie: Budget ~30%, Luxury ~20%, Adventure ~25%, Family ~25%

---

## Known Issues to Watch For

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Infinite rerun loop | Loading spinner never stops | Fixed in this version |
| Buttons don't respond | Click but nothing happens | Fixed with callback pattern |
| Map doesn't show agents | No colored dots | Ensure simulation runs for 5+ days |
| Charts are empty | No data | Run for 2+ ticks minimum |

---

## Success Criteria

**Dashboard is working if**:
- ✅ All buttons respond on first click
- ✅ Run/Pause toggles correctly
- ✅ Speed slider affects tick rate
- ✅ Event buttons trigger successfully
- ✅ Step button advances exactly 1 day
- ✅ Stop button requires confirmation
- ✅ Terminal shows INFO logs for button clicks
- ✅ No JavaScript errors in console

---

## Reporting Issues

If you encounter problems:

1. **Check terminal output** for error messages
2. **Check browser console** (F12 → Console tab)
3. **Note which button failed** and what happened
4. **Share the logs** from terminal

---

## Next Steps After Testing

If all tests pass:
- ✅ Dashboard is production-ready
- ✅ Proceed to Phase 4 (validation & documentation)
- ✅ Consider Stage 3 enhancements if needed

If tests fail:
- 📝 Document which tests failed
- 🔍 Review terminal/browser logs
- 🛠️ Create bug fix plan

---

**Good luck with testing! 🚀**
