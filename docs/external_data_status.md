# External Data Collection Status

**Date**: 2026-04-16  
**Attempted Sources**: OpenSky Network, ACLED, InsideAirbnb

---

## Summary

All three external data sources require **manual registration and download**. Automated API access was attempted but requires user registration.

---

## 1. OpenSky Network ✳️ Registration Required

**Status**: ⚠️ API requires free registration  
**URL**: https://opensky-network.org/register

### What We Tried
- Attempted to access public flight API endpoints
- All requests returned HTTP 400 (Bad Request) - authentication required

### Next Steps
1. **Register** at https://opensky-network.org/register
2. **Request API credentials** (username/password)
3. **Update script** with credentials
4. **Re-run** `src/collect_external_data.py`

### Data Available (After Registration)
- Airport traffic counts (arrivals/departures)
- Flight routes (origin-destination pairs)
- Historical flight data (2019-present)
- Real-time aircraft positions

### Use Case for Simulation
- **Connectivity proxy**: Flight frequency = destination accessibility
- **Tourism flow**: International flights ≈ tourist arrivals
- **Network effects**: Route density = destination popularity

### Download Guide Created
📄 `data/external/OPENVSKY_README.md`

---

## 2. ACLED (Conflict Data) ✳️ Registration Required

**Status**: ⚠️ Free registration required for research use  
**URL**: https://www.acleddata.com/registration/

### What We Tried
- Accessed public data export page (successful)
- Full dataset requires registration

### Next Steps
1. **Register** at https://www.acleddata.com/registration/
2. **Request API key** (free for academic/research use)
3. **Or use web export** (data sent via email)
4. **Download** conflict data for 2010-2024

### Data Available
- Conflict events by country (1997-present)
- Fatality counts
- Protest data
- Violence indicators
- Monthly updates

### Use Case for Simulation
- **Risk factor**: Conflict intensity → tourism risk perception
- **Temporal dynamics**: Monthly risk scores
- **Geographic variation**: Country-level risk indices

### Download Guide Created
📄 `data/external/ACLED_README.md`

---

## 3. InsideAirbnb ✳️ Manual Download Required

**Status**: ⚠️ Direct download from website  
**URL**: http://insideairbnb.com/get-the-data/

### What We Tried
- Attempted automated URL construction
- URL structure varies by city/country
- Manual download required

### Next Steps
1. **Visit** http://insideairbnb.com/get-the-data/
2. **Select cities** (100+ available)
3. **Download** `listings.csv` or `listings_summary.csv` for each city
4. **Save to** `data/insideairbnb/`

### Recommended Cities for Tourism Simulation
| City | Country | Region | Priority |
|------|---------|--------|----------|
| Paris | France | Europe | High |
| London | UK | Europe | High |
| New York | USA | Americas | High |
| Barcelona | Spain | Europe | High |
| Amsterdam | Netherlands | Europe | High |
| Tokyo | Japan | Asia-Pacific | High |
| Singapore | Singapore | Asia-Pacific | High |
| Rome | Italy | Europe | Medium |
| Lisbon | Portugal | Europe | Medium |
| Bangkok | Thailand | Asia-Pacific | Medium |

### Data Available
- Listing counts (accommodation capacity)
- Prices (affordability metric)
- Occupancy rates (demand proxy)
- Reviews (attractiveness proxy)
- Geographic distribution (neighborhood-level)

### Use Case for Simulation
- **Capacity limits**: Total listings = carrying capacity
- **Affordability**: Price levels = cost factor
- **Seasonality**: Occupancy rates = temporal variation
- **Attractiveness**: Review scores = destination quality

### Download Script Created
📄 `data/external/download_airbnb_data.py` (after city list generated)

---

## Files Generated

| File | Location | Purpose |
|------|----------|---------|
| OpenSky Guide | `data/external/OPENVSKY_README.md` | Registration + API instructions |
| ACLED Guide | `data/external/ACLED_README.md` | Registration + download instructions |
| Airbnb Cities | `data/external/insideairbnb_available_cities.csv` | City list (if URLs work) |
| Airbnb Script | `data/external/download_airbnb_data.py` | Automated download (after setup) |

---

## Recommended Action Plan

### Option A: Quick Start (Minimal Data)
**Proceed with simulation using current data:**
- ✅ UN Tourism (215 countries, 1995-2024)
- ✅ OECD (55 countries, economic indicators)
- ⚠️ Use literature estimates for risk, connectivity, accommodation

**Estimated effort**: 0 hours (proceed immediately)

---

### Option B: Enhanced Data (Recommended)
**Register and download 1-2 key sources:**

1. **ACLED** (30 min registration + download)
   - Adds risk factor calibration
   - Critical for shock modeling

2. **InsideAirbnb** (1 hour manual download)
   - Adds accommodation capacity
   - Critical for crowding/overtourism modeling

**Skip for now:**
- OpenSky Network (flight data is proxy for arrivals, which we already have from UN Tourism)

**Estimated effort**: 1-2 hours

---

### Option C: Comprehensive Data
**Register and download all three sources:**

1. ACLED (risk) - 30 min
2. InsideAirbnb (accommodation) - 1 hour
3. OpenSky Network (connectivity) - 1 hour

**Estimated effort**: 2-3 hours

---

## My Recommendation

**Proceed with Option B (Enhanced Data):**

1. **Download ACLED first** (highest priority for risk modeling)
2. **Download InsideAirbnb for 3-5 key cities** (Paris, London, NYC, Barcelona, Tokyo)
3. **Skip OpenSky** (UN Tourism arrivals data is sufficient proxy)
4. **Begin simulation development** with current + ACLED + Airbnb data

**Rationale:**
- Risk factor (ACLED) is critical for shock modeling
- Accommodation capacity (Airbnb) is critical for crowding dynamics
- Flight connectivity (OpenSky) is redundant with arrivals data
- Diminishing returns beyond these three sources

---

## Alternative: Use Literature Estimates

If you prefer to proceed immediately without additional data collection:

| Factor | Literature-Based Estimate | Source |
|--------|--------------------------|--------|
| **Risk index** | Use Fragile States Index (publicly available) | fundforpeace.org |
| **Accommodation capacity** | Use OECD hotel capacity data | Already in OECD dataset |
| **Connectivity** | Use UN Tourism arrivals as proxy | Already collected |

**This allows immediate simulation development with reasonable parameters.**

---

## Decision Point

**Please let me know which option you prefer:**

- **A**: Proceed with simulation using current data only
- **B**: Download ACLED + InsideAirbnb (1-2 hours), then proceed
- **C**: Download all three sources (2-3 hours), then proceed
- **D**: Use literature estimates instead of external data

I recommend **Option B** for best balance of data quality vs. development time.
