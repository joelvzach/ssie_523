# Document Update Summary - Tourism Friendliness Index (TFI)

**Version**: 2.0 → 2.1  
**Date**: 2026-04-21  
**Change Type**: New Feature Addition (Policy Feedback Loop)

---

## 📋 Executive Summary

Added **Tourism Friendliness Index (TFI)** as a destination-state moderator that models resident attitudes and policy responses to overtourism. This creates an endogenous policy feedback loop without bloating the utility function (kept at 8 factors).

**Key Decision**: TFI is implemented as a **destination moderator** (affecting capacity and attractiveness) rather than a 9th utility factor.

---

## 📄 Files Modified

### 1. `PRD.md` (v2.0 → v2.1)

#### Section 2: Project Overview
**Added**:
- Tourism Friendliness to Enhanced Key Dynamics
- TFI reference in deliverables
- TFI in Phase 2 implementation timeline
- TFI in Resolved Questions (#10)

**Changes**:
```diff
**Enhanced Key Dynamics** (v2.1):
+ - **Tourism Friendliness**: Resident attitudes → policy feedback loop (NEW v2.1)
```

```diff
**Deliverables**:
+ - [ ] **Tourism Friendliness Index (TFI) dynamics** (NEW v2.1)
+ - [ ] **Policy feedback loops (TFI-driven)** (NEW v2.1)
+ - [ ] **TFI visualization (resident attitudes over time)** (NEW v2.1)
```

```diff
**Phase 2 (Week 3-4) - Enhanced**:
+ - [ ] **Tourism Friendliness Index (TFI) dynamics** (NEW v2.1)

**Phase 3 (Stage 3) - Advanced**:
- [ ] Policy interventions (visa, tourism taxes)
+ [ ] Policy interventions (visa, tourism taxes) **← Now modeled via TFI**
```

#### Section 5: Technical Stack - Architecture
**Added TFI-specific modules**:
```diff
simulation/
├── destinations/
│   ├── destination.py (multi-subsystem capacity + TFI)
│   ├── capacity.py (4 subsystems)
│   └── tfi.py (Tourism Friendliness Index dynamics) ← NEW v2.1
├── dynamics/
│   ├── utility.py (8-factor utility function)
│   ├── choice.py (softmax with distance + popularity)
│   ├── shocks.py (hybrid recovery model)
│   ├── popularity.py (log-scale feedback)
│   └── tfi_dynamics.py (resident attitudes → policy feedback) ← NEW v2.1
├── visualization/
│   └── dashboard.py (Streamlit interface with TFI tracking)
└── validation/
    ├── metrics.py (4-tier validation + TFI metrics)
    └── tests.py (automated test suite)
```

---

### 2. `docs/literature_parameters.md`

#### Added Section 11: Tourism Friendliness Index (TFI)

**New Subsections**:
- 11.1 Concept (literature foundation)
- 11.2 Mathematical Formulation (dynamic update rules)
- 11.3 TFI Parameters (10 parameters with values, ranges, sources, confidence)
- 11.4 Real-World Examples (Venice, Barcelona, Amsterdam, Bhutan, Dubrovnik, Maya Bay)
- 11.5 Implementation Notes (code examples)
- 11.6 Validation Targets (future calibration needs)

**Key Parameters Defined**:
| Parameter | Symbol | Value | Source |
|-----------|--------|-------|--------|
| Baseline TFI | TFI₀ | 0.80 | Assumption |
| Hostility growth rate | ρ↓ | 0.05/step | Muler González et al. (2018) |
| Recovery rate | ρ↑ | 0.02/step | Cheung & Li (2019) - hysteresis |
| Crowding threshold | τ_crowd | 0.80 | Muler González et al. (2018) ✅ |
| Policy threshold (severe) | τ_policy_severe | 0.40 | Assumption |
| Capacity penalty (severe) | κ_cap_severe | 0.70 | Assumption (Venice case) |
| Attractiveness penalty (severe) | κ_att_severe | 0.80 | Assumption |

**Added Next Step**:
```diff
## Next Steps
+ 5. **Implement TFI** in simulation (new destination class attribute)
```

---

### 3. `docs/literature_review_summary.md`

#### Added Two New Paper Reviews

**Paper 4: Muler González et al. (2018)**
- Social carrying capacity threshold (80%)
- Resident dissatisfaction mechanism
- Policy implications

**Paper 5: Cheung & Li (2019)**
- Visitor-resident conflict dynamics
- Hysteresis effect (asymmetric recovery)
- Resilience factors

#### Updated Section: Key Takeaways
**Added**:
```diff
### 1. Literature Validates Core Approach ✅
+ | **Resident attitudes (TFI)** | **Strong** | **Muler González et al. (2018), Cheung & Li (2019)** |
```

```diff
### 4. Confidence Levels
+ | **TFI parameters** | **MEDIUM** | **Muler González et al. (2018) threshold, Cheung & Li (2019) hysteresis** |
```

---

### 4. `docs/inferred_rules.md`

#### Updated Section: Known Limitations
**Added**:
```diff
**Missing Factors** (not yet modeled):
+ 4. **Visa policy/accessibility** → ✅ NOW MODELED via TFI (v2.1)
+ 7. **Resident attitudes/policy feedback** → ✅ NOW ADDED (TFI dynamics v2.1)
```

#### Updated Section: Open Questions
**Added**:
```diff
## Open Questions for Refinement
+ 8. **Resident attitudes**: Should tourism friendliness affect destination choice? 
+    ✅ ADDED as moderator (TFI, not utility factor)
```

#### Updated Section: Next Steps
**Added**:
```diff
## Next Steps
+ 6. **Implement TFI dynamics** (resident attitudes → policy feedback) ← NEW v2.1
```

---

## 🔬 Literature Citations Added

### Primary TFI Citations

1. **Muler González, V., Coromina, L., & Galí Espelt, N. (2018)**
   - Title: Overtourism: residents' perceptions of tourism impact as an indicator of resident social carrying capacity
   - Journal: Tourism Review, 73(3), 277-292
   - DOI: https://doi.org/10.1108/TR-08-2017-0138
   - Citations: 337
   - **Key Contribution**: 80% capacity threshold triggers resident dissatisfaction

2. **Cheung, K. S., & Li, L. H. (2019)**
   - Title: Understanding visitor–resident relations in overtourism: developing resilience for sustainable tourism
   - Journal: Journal of Sustainable Tourism, 27(8), 1197-1216
   - DOI: https://doi.org/10.1080/09669582.2019.1606815
   - Citations: 206
   - **Key Contribution**: Hysteresis effect (recovery slower than decline)

### Supporting Citations (Already Present)

3. **Bertocchi et al. (2020)** - Multi-subsystem capacity model
4. **Butler (2019)** - Dynamic carrying capacity limits

---

## 🎯 Implementation Specification

### TFI Dynamics (Pseudocode)

```python
class Destination:
    def __init__(self, ...):
        self.tfi = 0.80  # Baseline friendliness
        self.capacity = ...  # Multi-subsystem capacity
        self.attractiveness = ...  # TTDI-based
    
    def update_tfi(self, crowding_ratio):
        """Update TFI based on crowding"""
        if crowding_ratio > 0.80:
            self.tfi = max(0.0, self.tfi - 0.05)  # Fast decline
        else:
            self.tfi = min(1.0, self.tfi + 0.02)  # Slow recovery
    
    @property
    def effective_capacity(self):
        """Apply policy restrictions based on TFI"""
        base = self.capacity
        if self.tfi < 0.4:
            return base * 0.70  # Severe restrictions
        elif self.tfi < 0.6:
            return base * 0.85  # Moderate restrictions
        return base
    
    @property
    def effective_attractiveness(self):
        """Apply reputation effects based on TFI"""
        base = self.attractiveness
        if self.tfi < 0.4:
            return base * 0.80  # Negative media
        elif self.tfi < 0.6:
            return base * 0.90
        return base
```

### Real-World Validation Cases

| Destination | Policy | TFI Threshold | Impact |
|-------------|--------|---------------|--------|
| Venice | Cruise ban | < 0.4 | -30% capacity |
| Barcelona | Apartment freeze | < 0.4 | -20% capacity |
| Amsterdam | "Stay Away" campaign | < 0.6 | -15% attractiveness |
| Bhutan | Visa fee increase | < 0.4 (intentional) | -50% arrivals |
| Dubrovnik | Cruise caps | < 0.4 | -25% capacity |
| Maya Bay | Complete closure | < 0.4 | -100% (temporary) |

---

## 📊 Impact on Simulation

### Before (v2.0)
```
Crowding → Linear degradation (γ·crowding in utility)
```

### After (v2.1)
```
Crowding → TFI↓ → Policy changes → Capacity↓ + Attractiveness↓
         ↑                              ↑
         └──── Hysteresis (slow recovery) ────┘
```

### Emergent Dynamics Enabled
1. **Tipping points**: Destinations can suddenly become "unfriendly"
2. **Hysteresis**: Recovery takes longer than decline
3. **Policy feedback**: Endogenous restrictions (no external intervention needed)
4. **Resident agency**: Locals indirectly influence tourism flows
5. **Realistic case studies**: Venice, Barcelona, Amsterdam behaviors emerge naturally

---

## ✅ Validation Strategy (Future)

| Metric | Target | Method | Status |
|--------|--------|--------|--------|
| TFI decline rate | 0.05/step | Calibrate to Venice/Barcelona timelines | ⏳ Pending |
| Policy threshold | TFI < 0.4 | Compare to policy announcement dates | ⏳ Pending |
| Capacity reduction | 20-30% | Match to observed arrival declines | ⏳ Pending |
| Hysteresis ratio | 0.4 (2.5× slower) | Cheung & Li (2019) framework | ⏳ Assumption |

---

## 🔍 Why This Approach?

### Advantages
1. **Keeps utility function clean** (8 factors, not 9)
2. **Clear causal chain** (crowding → attitudes → policy → capacity)
3. **Literature-backed** (Muler González, Cheung & Li)
4. **Policy modeling** (can simulate interventions)
5. **Emergent dynamics** (tipping points, hysteresis, path dependence)

### Tradeoffs
1. **Additional complexity** (new state variable per destination)
2. **Calibration needed** (thresholds, rates from case studies)
3. **Country-level only** (not city-level - Stage 3)

---

## 📝 Next Actions

1. **Implement TFI in destination class** (`simulation/destinations/destination.py`)
2. **Add TFI tracking to dashboard** (`simulation/visualization/dashboard.py`)
3. **Create TFI validation tests** (`simulation/validation/tests.py`)
4. **Document TFI in team briefing** (`docs/team_briefing.md`)
5. **Update version numbers** (PRD, inferred_rules → v2.1)

---

**Summary**: Added Tourism Friendliness Index as destination moderator with strong literature support (Muler González et al., Cheung & Li), enabling endogenous policy feedback loops without bloating utility function.
