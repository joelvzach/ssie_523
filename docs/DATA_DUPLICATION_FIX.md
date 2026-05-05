# Data Duplication Fix - Summary

**Date**: May 1, 2026  
**Status**: ✅ **FIXED**

---

## Problem Identified

The `tourism_comprehensive_1995_2024.csv` dataset had **3 duplicate rows per country-year** (8,911 rows instead of ~3,000).

### Root Cause

The UN Tourism inbound expenditure dataset contains **3 indicator categories**:

| Indicator Code | Description | Albania 1995 |
|----------------|-------------|--------------|
| `INBD_EXPD_BPAY_PSTR_VSTR` | Passenger transport | 5.0M USD |
| `INBD_EXPD_BPAY_TRVL_VSTR` | Travel expenditure | 65.0M USD |
| `INBD_EXPD_BPAY_TOTL_VSTR` | **TOTAL** | **70.0M USD** |

**Relationship**: `TOTAL = Passenger Transport + Travel` (verified: 5.0 + 65.0 = 70.0)

The merge script (`src/create_merged_dataset.py`) was loading **ALL three indicators** without filtering, creating 3 rows per country-year with different expenditure values.

---

## Fix Applied

**File Modified**: `src/create_merged_dataset.py` (line 56-68)

**Change**: Added filter to use only the TOTAL indicator:

```python
# FIX: Filter to TOTAL indicator only to avoid duplication
# The dataset contains 3 indicators: passenger transport, travel, and total
# TOTAL = passenger transport + travel, so we use only TOTAL to avoid 3x duplication
print("  Loading UN Tourism inbound expenditure (TOTAL indicator only)...")
un_expenditure = pd.read_csv(
    DATA_ROOT / "UN_Tourism/extracted/UN_Tourism_inbound_expenditure_12_2025.csv"
)
# Filter to TOTAL indicator (includes both passenger transport and travel)
un_expenditure = un_expenditure[
    un_expenditure['indicator_code'] == 'INBD_EXPD_BPAY_TOTL_VSTR'
].copy()
```

---

## Results

### Before Fix
- **Total rows**: 8,911
- **Unique country-year**: 3,794
- **Duplicate rows**: 5,117
- **Albania 1995**: 3 rows (5.0, 70.0, 65.0 M USD)

### After Fix
- **Total rows**: 3,794 ✓
- **Unique country-year**: 3,794 ✓
- **Duplicate rows**: 0 ✓
- **Albania 1995**: 1 row (70.0 M USD - the TOTAL) ✓

### Impact on Derived Data

**Tourism GDP Analysis**:
- Before: 119 countries (with inflated expenditure from summing duplicates)
- After: 93 countries (correct expenditure values)
- OECD correlation improved: r = 0.61 → **r = 0.795** ✓

**Top Tourism-Dependent Economies**:
- Before: Macao (166.4%) - inflated
- After: Macao (83.2%) - correct ✓

---

## Files Regenerated

All derived data and presentation plots have been regenerated with corrected data:

### Data Files
- ✅ `data/merged/tourism_comprehensive_1995_2024.csv` (0.42 MB, down from 0.97 MB)
- ✅ `data/derived/tourism_gdp_analysis_2019.csv` (93 countries)
- ✅ `data/derived/oecd_comparison_2019.csv` (16 countries)

### Presentation Plots
- ✅ `docs/presentation/01_global_trends.png`
- ✅ `docs/presentation/02_top_destinations.png`
- ✅ `docs/presentation/03_tourism_gdp.png`
- ✅ `docs/presentation/04_correlation_heatmap.png`
- ✅ `docs/presentation/05_ttdi_scatter.png`
- ✅ `docs/presentation/06_oecd_validation.png`
- ✅ `docs/presentation/presentation_summary_stats.csv`

---

## Verification

Run this to verify the fix:
```python
import pandas as pd
df = pd.read_csv('data/merged/tourism_comprehensive_1995_2024.csv')
duplicates = df[df.duplicated(subset=['country_code', 'country_name', 'year'], keep=False)]
print(f"Duplicate rows: {len(duplicates)}")  # Should be 0
```

---

## Next Steps

**For Notebook Users**:

The next time you run `notebooks/01_tourism_data_eda.ipynb`, the data will be clean with:
- No duplicate rows
- Correct expenditure values (TOTAL only)
- Accurate tourism GDP percentages
- Improved OECD validation correlation

**No additional action required** - the fix is in the merge script, and all derived data has been regenerated.

---

## Technical Notes

### Why TOTAL indicator is correct:

1. **Official measure**: TOTAL is the official UN Tourism aggregate
2. **Mathematical verification**: TOTAL = Passenger + Travel (correlation = 1.0000)
3. **Comprehensive**: Includes all expenditure categories
4. **No data loss**: Using TOTAL instead of components loses no information

### Coverage:

- TOTAL indicator: 4,608 records (212 countries × ~22 years)
- Coverage: Excellent (no significant gaps)
- Years: 1995-2024 (complete)

---

**End of Fix Summary**
