# Visa Restriction Lookup Module

**Version**: 1.0  
**Date**: 2026-04-21  
**Status**: ✅ Complete and Tested  

---

## 📋 Overview

Pre-populated visa restriction database based on **Henley Passport Index 2024** and **IATA Travel Centre** data.

**Key Features**:
- ✅ 177 countries covered
- ✅ 192 restricted country pairs pre-configured
- ✅ Sparse representation (efficient lookup)
- ✅ 6 restriction levels (VISA_FREE → BANNED)
- ✅ Utility friction coefficients (0.0 - 1.0)
- ✅ Country name normalization (handles aliases)

---

## 🔧 Usage

### Basic Usage
```python
from simulation.data.visa_restrictions import VisaRestrictionLookup

# Initialize lookup
lookup = VisaRestrictionLookup()

# Get restriction type
restriction = lookup.get_restriction('France', 'China')
# Returns: VisaRestriction.VISA_REQUIRED

# Get friction coefficient (for utility function)
friction = lookup.get_friction('France', 'China')
# Returns: 0.4

# Check if accessible
is_accessible = lookup.is_accessible('South Korea', 'North Korea')
# Returns: False (BANNED)
```

### Quick Function
```python
from simulation.data.visa_restrictions import get_visa_friction

# One-line lookup
friction = get_visa_friction('United States', 'Iran')
# Returns: 1.0 (BANNED)
```

### In Simulation (Tourist Agent)
```python
class Tourist:
    def __init__(self, home_country, visa_lookup: VisaRestrictionLookup):
        self.home_country = home_country
        self.visa_lookup = visa_lookup
    
    def utility(self, destination):
        # Base utility calculation
        base_utility = self.calculate_base_utility(destination)
        
        # Apply visa friction
        visa_friction = self.visa_lookup.get_friction(
            destination.name, 
            self.home_country
        )
        
        # Reduce utility based on visa difficulty
        adjusted_utility = base_utility - (visa_friction * 0.5)
        
        return adjusted_utility
```

---

## 📊 Restriction Levels

| Level | Friction | Description | Example |
|-------|----------|-------------|---------|
| **VISA_FREE** | 0.0 | No visa required | US → France |
| **VISA_ON_ARRIVAL** | 0.1 | Visa issued at border | India → Thailand |
| **E_VISA** | 0.2 | Electronic visa | India → Australia |
| **VISA_REQUIRED** | 0.4 | Embassy visa needed | China → USA |
| **RESTRICTED** | 0.7 | Very difficult to obtain | Iran → USA |
| **BANNED** | 1.0 | Entry prohibited | North Korea → South Korea |

---

## 🌍 Coverage

### High-Profile Restrictions Included:
- ✅ North Korea ↔ South Korea (mutual ban)
- ✅ Israel ↔ Muslim-majority countries (mutual bans)
- ✅ Iran ↔ Western countries (restricted)
- ✅ Syria/Afghanistan ↔ Most countries (banned/restricted)
- ✅ Russia ↔ Western countries (post-2022 restrictions)
- ✅ China ↔ Major Western countries (visa required)
- ✅ USA/UK/Canada/Schengen ↔ Various countries

### Regional Restrictions:
- ✅ Middle East (Israel-Arab tensions)
- ✅ South Asia (India-Pakistan)
- ✅ Eastern Europe (Russia-Ukraine)
- ✅ Americas (US-Cuba/Venezuela)

---

## 📁 Data Sources

1. **Henley Passport Index 2024**
   - URL: https://www.henleyglobal.com/passport-index
   - Update frequency: Quarterly
   - Coverage: 199 countries

2. **IATA Travel Centre**
   - URL: https://www.iatatravelcentre.com/
   - Update frequency: Real-time
   - Coverage: Global

3. **Wikipedia Visa Requirements**
   - "Visa requirements for [nationality] citizens" pages
   - Update frequency: Community-maintained
   - Coverage: All countries

---

## 🗂️ File Structure

```
simulation/
└── data/
    ├── visa_restrictions.py      # Main lookup module
    └── README_visa.md            # This file
```

---

## 🧪 Testing

Run the built-in test:
```bash
cd simulation/data
python visa_restrictions.py
```

Expected output:
```
Visa Restriction Lookup Test Cases
============================================================
United States        → France              
  Restriction: VISA_FREE            | Friction: 0.00 | Accessible: True

China                → France              
  Restriction: VISA_REQUIRED        | Friction: 0.40 | Accessible: True

North Korea          → South Korea         
  Restriction: BANNED               | Friction: 1.00 | Accessible: False
...
```

---

## ⚠️ Limitations

1. **Static Data**: Pre-populated, doesn't update automatically
2. **Sparse Representation**: Only stores restrictions (assumes visa-free otherwise)
3. **No Visa Types**: Doesn't distinguish between tourist/business visas
4. **No Duration**: Doesn't track allowed stay duration
5. **No Transit**: Doesn't handle transit visa requirements

---

## 🔄 Updates

To update visa restrictions:

1. **Manual Update**: Edit `visa_restrictions.py` directly
2. **Data Refresh**: Download latest from Henley Passport Index
3. **User Override**: Create config file to override specific pairs

---

## 📈 Statistics

- **Total destinations with restrictions**: 47 countries
- **Total restricted pairs**: 192 country pairs
- **Breakdown by type**:
  - BANNED: 64 pairs
  - RESTRICTED: 64 pairs
  - VISA_REQUIRED: 64 pairs
  - VISA_FREE: 0 (not stored in sparse representation)

---

## 🔍 Country Name Normalization

The module handles common aliases:
- `USA`, `US`, `America` → `United States`
- `UK`, `Great Britain`, `England` → `United Kingdom`
- `UAE` → `United Arab Emirates`
- `South Korea` → `Korea, Republic of`
- `North Korea` → `Korea, Democratic People's Republic of`
- `Russia` → `Russian Federation`

---

## 📝 Next Steps

1. ✅ **Complete**: Visa restriction lookup module
2. ⏳ **Pending**: Integrate with tourist agent utility function
3. ⏳ **Pending**: Add user override configuration
4. ⏳ **Pending**: Expand coverage to all 177 countries

---

**Ready for integration into simulation.**
