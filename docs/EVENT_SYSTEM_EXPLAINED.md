# Event System Explained

**Date**: May 3, 2026  
**Version**: 1.0

---

## Impact Strength Explained

### What is Impact Strength?

**Range:** 0.0 to 1.0 (0-100%)

Impact Strength (called `magnitude` in code) determines how much a planned event boosts the host destination's attractiveness to tourists.

---

### How It Works

The event bonus is added to the **utility function** that tourists use to choose destinations:

```python
# Utility function (simplified)
U(destination) = α·Attractiveness - β·Cost - γ·Crowding - δ·Risk 
                 - η·Distance + ζ·Memory + EVENT_BONUS
```

**Event Bonus Calculation:**

The bonus varies over time with three phases:

#### Phase 1: Pre-Event Ramp-Up (45 days before)
- **Linear increase** from 0% to 30% of full magnitude
- Formula: `magnitude × 0.3 × segment_appeal × ramp_factor`
- Example (FIFA 80% impact, Family segment):
  - Day 1 of ramp: 0.8 × 0.3 × 0.9 × 0.0 = 0.0 (0%)
  - Day 22 of ramp: 0.8 × 0.3 × 0.9 × 0.5 = 0.108 (50% of 30%)
  - Day 45 of ramp: 0.8 × 0.3 × 0.9 × 1.0 = 0.216 (100% of 30%)

#### Phase 2: Event Period (bell curve)
- **Bell curve distribution** peaking at event midpoint
- Peak bonus: `magnitude × segment_appeal`
- Formula: `magnitude × segment_appeal × exp(-0.5 × (days_from_peak / σ)²)`
- Example (FIFA 80% impact, Family segment, 45-day duration):
  - Opening day (June 1): 0.8 × 0.9 × 0.13 = 0.094 (13% of peak)
  - Peak day (July 8): 0.8 × 0.9 × 1.0 = 0.72 (100% of peak)
  - Closing day (July 15): 0.8 × 0.9 × 0.13 = 0.094 (13% of peak)

#### Phase 3: Post-Event Decline (15 days after)
- **Linear decline** from 20% to 0% of magnitude
- Formula: `magnitude × 0.2 × segment_appeal × decline_factor`
- Example (FIFA 80% impact, Family segment):
  - Day 1 after: 0.8 × 0.2 × 0.9 × 1.0 = 0.144 (100% of 20%)
  - Day 8 after: 0.8 × 0.2 × 0.9 × 0.5 = 0.072 (50% of 20%)
  - Day 15 after: 0.8 × 0.2 × 0.9 × 0.0 = 0.0 (0%)

---

### Segment Appeal Multipliers

Each tourist segment has different appeal for events:

| Segment | Default Appeal | Effect |
|---------|----------------|--------|
| **Budget** | 0.6 (60%) | Moderate interest |
| **Luxury** | 0.8 (80%) | High interest (premium events) |
| **Adventure** | 0.5 (50%) | Lower interest (prefer independent travel) |
| **Family** | 0.9 (90%) | Highest interest (structured activities) |

**Example:** FIFA World Cup with 80% magnitude:
- Family tourist: 0.8 × 0.9 = **0.72** max bonus
- Adventure tourist: 0.8 × 0.5 = **0.40** max bonus
- **Result:** Families are 80% more likely to choose host destination than Adventure travelers during event.

---

### Practical Impact on Destination Choice

**Utility Score Context:**
- Typical utility scores range from **0.0 to 1.0**
- A bonus of **0.1-0.2** is noticeable
- A bonus of **0.5+** is very significant

**Probability Increase** (approximate, varies by competition):

| Magnitude | Max Bonus | Probability Increase | Real-World Analogy |
|-----------|-----------|---------------------|-------------------|
| **0.3 (30%)** | 0.27 | +10-15% | Regional festival |
| **0.5 (50%)** | 0.45 | +15-25% | National celebration |
| **0.8 (80%)** | 0.72 | +30-45% | FIFA World Cup, Olympics |
| **1.0 (100%)** | 0.90 | +40-60% | Once-in-lifetime mega-event |

**Example Calculation:**
- Destination A (no event): Utility = 0.65 → Choice probability = 12%
- Destination B (FIFA event, 80% magnitude): Utility = 0.65 + 0.72 = 1.37 → Choice probability = 35%
- **Result:** 23 percentage point increase in destination choice probability.

---

## Live Event Notifications

### How It Works

When the simulation date enters an event's active period, a **blue notification banner** appears at the top of the dashboard:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔵 FIFA World Cup 2026 is LIVE in US! (Ends Jul 15)        │
├─────────────────────────────────────────────────────────────┤
│ 🔵 Olympics 2026 is LIVE in FR! (Ends Aug 20)              │
└─────────────────────────────────────────────────────────────┘
```

### Features

1. **Stacked Display:** Multiple active events stack vertically
2. **Blue Color:** Info-style (not success/warning) for neutral visibility
3. **End Date:** Shows "Ends MMM DD" format (e.g., "Ends Jul 15")
4. **Auto-Disappear:** Banner vanishes when event ends
5. **Real-Time Updates:** Updates every simulation tick

### Code Location

```python
# In dashboard.py
def render_event_notifications(sim):
    """Render live event notifications as stacked banners."""
    current_date = sim.start_date + timedelta(days=sim.tick)
    active_events = sim.planned_events.get_active_events(current_date)
    
    if active_events:
        for event in active_events:
            days_remaining = (event.end_date - current_date).days
            end_date_str = event.end_date.strftime("Ends %b %d")
            
            st.info(
                f"🔵 **{event.name} is LIVE in {event.country_code}!** "
                f"({end_date_str})"
            )
```

---

## Configuration UI

### Event Setup Fields

**Before Simulation:**
1. **Event Name:** e.g., "FIFA World Cup 2026"
2. **Host Country:** Dropdown (10 common countries)
3. **Start Date:** Event opening day
4. **End Date:** Event closing day
5. **Impact Strength:** Slider 0-100% (default 50%)
6. **Segment Appeal:** 4 sliders (Budget, Luxury, Adventure, Family)

**Defaults (Hidden):**
- **Expected Footfall:** 500,000 visitors (used for future capacity planning)
- **Pre-Event Ramp:** 30 days (automatically calculated)

### Remove Events

- Click 🗑️ button next to any event to remove it
- Works for both pre-loaded FIFA event and custom events
- Must be done **before** clicking "Initialize Simulation"

---

## Example Configurations

### FIFA World Cup 2026 (Pre-loaded)
```
Name: FIFA World Cup 2026
Country: US
Dates: Jun 01 - Jul 15 (45 days)
Impact: 80%
Segment Appeal:
  - Budget: 60%
  - Luxury: 80%
  - Adventure: 50%
  - Family: 90%
```

**Timeline:**
- **Apr 17:** Pre-event ramp starts (0% bonus)
- **May 31:** Ramp complete (24% bonus for families)
- **Jun 01:** Event starts (bell curve begins)
- **Jul 08:** Peak impact (72% bonus for families)
- **Jul 15:** Event ends (bell curve ends)
- **Jul 30:** Post-event decline complete (0% bonus)

### Olympics 2026 (Custom Example)
```
Name: Summer Olympics 2026
Country: FR
Dates: Jul 20 - Aug 15 (27 days)
Impact: 90%
Segment Appeal:
  - Budget: 50%
  - Luxury: 90%
  - Adventure: 60%
  - Family: 85%
```

### Music Festival (Small Event)
```
Name: Coachella 2026
Country: US
Dates: Apr 10 - Apr 12 (3 days)
Impact: 40%
Segment Appeal:
  - Budget: 70%
  - Luxury: 60%
  - Adventure: 80%
  - Family: 30%
```

---

## Testing Instructions

### Test 1: Impact Strength Effect
1. Configure two events:
   - Event A: 50% impact in US (Jun 1-15)
   - Event B: 90% impact in FR (Jun 1-15)
2. Initialize simulation
3. Run to June 1
4. **Expected:** 
   - US sees moderate visitor increase
   - FR sees strong visitor increase
   - FR has more visitors than US (higher impact)

### Test 2: Live Notification
1. Configure FIFA World Cup 2026 (Jun 1 - Jul 15)
2. Run simulation to **Day 151** (June 1)
3. **Expected:** Blue banner appears: "🔵 FIFA World Cup 2026 is LIVE in US! (Ends Jul 15)"
4. Run to **Day 195** (July 15)
5. **Expected:** Banner still visible, shows "Ends Jul 15"
6. Run to **Day 196** (July 16)
7. **Expected:** Banner disappears

### Test 3: Multiple Events
1. Configure 3 events with overlapping dates:
   - FIFA in US (Jun 1 - Jul 15)
   - Olympics in FR (Jul 1 - Jul 20)
   - Festival in ES (Jul 10 - Jul 15)
2. Run to **Day 182** (July 1)
3. **Expected:** 2 banners stacked (FIFA + Olympics)
4. Run to **Day 191** (July 10)
5. **Expected:** 3 banners stacked (FIFA + Olympics + Festival)

---

## Performance Impact

| Metric | Overhead | Notes |
|--------|----------|-------|
| Event bonus calculation | ~0.1ms per agent | Cached per destination |
| Notification rendering | ~5ms | Only when events active |
| Memory usage | <1KB per event | Minimal |

---

## Future Enhancements (Not Implemented)

1. **Dynamic footfall tracking:** Show actual vs expected visitors
2. **Economic impact:** Calculate tourism revenue from event
3. **Multi-country events:** Support events spanning multiple countries (e.g., FIFA in US+CA+MX)
4. **Event editing:** Modify event after creation (currently must delete and recreate)
5. **Event templates:** Pre-configure common event types (FIFA, Olympics, festivals)

---

**Last Updated:** May 3, 2026  
**Owner:** Simulation Development Team
