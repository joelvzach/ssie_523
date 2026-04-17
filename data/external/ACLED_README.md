# ACLED Conflict Data

## Status
API requires free registration for research use.

## Data Description
ACLED (Armed Conflict Location & Event Data Project) provides:
- Conflict events by country
- Protest data
- Violence indicators
- Monthly updates from 1997-present

## Relevance for Tourism Simulation
- **Risk factor calibration**: Conflict intensity by country
- **Temporal dynamics**: Monthly risk scores
- **Geographic granularity**: Sub-national conflict locations

## Download Instructions

### Option 1: Web Export (No API)
1. Visit: https://www.acleddata.com/data-export/
2. Select parameters:
   - Regions: All (or select specific)
   - Date range: 2010-2024
   - Event types: All
   - Format: CSV
3. Submit request (data sent via email)

### Option 2: API Access (Recommended)
1. Register at: https://www.acleddata.com/registration/
2. Request API key (free for academic use)
3. Use API endpoint:
   ```
   GET https://api.acleddata.com/api.php?api_key=YOUR_KEY&event_type=All&country=All
   ```

### Option 3: Direct Download (Limited)
Some pre-packaged datasets available at:
https://github.com/ACLED

## Data Processing (After Download)
See download instructions at ACLED website for data format.

## Expected Output
File: `data/external/acled_conflict_data.csv`
Columns:
- country_code
- year
- conflict_events (count)
- fatalities (total)
- risk_index (0-1, normalized)

## Last Updated
2026-04-16
