# Progress Report: Global Tourism Complexity Simulation

**Project**: SSIE 523 - Agent-Based Modeling of Global Tourism Dynamics  
**Date**: April 21, 2026  
**Status**: Stage 2 Development Complete ✅ | Stage 3 Dashboard Operational  

---

## Executive Summary

We set out to build an agent-based simulation that demonstrates complexity in global tourism—not as a predictive forecasting tool, but as an exploratory sandbox for understanding how heterogeneous tourist decisions, destination constraints, and external shocks interact to produce emergent patterns. Our work began with a fundamental question: can we reproduce observed tourism dynamics (pandemic shock, recovery, hub formation) from first principles of individual choice behavior, without hardcoding aggregate outcomes?

After assembling seven major datasets, reviewing six foundational papers, and implementing a 6-factor utility function with segment-specific heterogeneity, we have built a fully functional simulation with 4,000 tourist agents, 177 countries, and an interactive real-time dashboard. The system successfully generates realistic trip frequencies, responds to disaster events with elevated risk perception, and exhibits feedback loops through Tourism Friendliness Index (TFI) dynamics. What emerged from this process is a clearer understanding that tourism complexity arises not from any single mechanism, but from the interaction of geographic friction, capacity constraints, memory effects, and heterogeneous preferences across traveler segments.

---

## 1. Starting Goal: From Static Equilibrium to Dynamic Complexity

Traditional tourism models treat destinations as independent units competing for aggregate market share, calibrated against historical arrival statistics. While useful for forecasting, these approaches cannot answer "what-if" questions about system behavior under novel conditions: What happens when a disaster strikes a popular destination? Do tourists redistribute to nearby alternatives, or does confidence collapse regionally? How do resident attitudes toward tourism evolve under sustained overcrowding, and what policy responses emerge?

Our goal was to build a **complex adaptive system** where:
- Tourist agents make destination choices based on multi-factor utility (not just price or attractiveness)
- Destinations have finite capacity with endogenous policy responses (TFI dynamics)
- External shocks trigger segment-specific behavioral responses (not uniform percentage declines)
- Emergent patterns (hub formation, cascading failures, recovery trajectories) arise from micro-level interactions, not top-down calibration

The simulation was designed from the outset as an **exploratory tool**, explicitly acknowledging that TTDI attractiveness explains only 13% of variance in real tourism flows (r = 0.364 from our correlation analysis). Rather than treating this as a limitation, we treated it as justification for an agent-based approach: if aggregate models cannot explain most variation, perhaps the missing 87% resides in heterogeneous preferences, network effects, and path dependence—phenomena that agent-based modeling is uniquely suited to capture.

---

## 2. Data Assembly and Literature Discovery

### 2.1 Empirical Foundation: Seven Datasets, 30 Years, 177 Countries

We assembled and merged seven major data sources into a unified foundation:

| Dataset | Coverage | Key Variables | Role in Simulation |
|---------|----------|---------------|-------------------|
| **UN Tourism Arrivals** | 215 countries, 1995-2024 | Inbound arrivals, expenditure, purpose (business/personal), transport mode | Baseline calibration, validation targets (CAGR 3.69%, pandemic shock -70.6%, recovery 94.5%) |
| **WEF TTDI Scores** | 119 countries, 2024 | Attractiveness scores (2.78-5.24 range), infrastructure, policy environment | Utility function α factor (attractiveness) |
| **ACLED Conflict Events** | Global, 1997-2026 | Conflict type, fatalities, geographic coordinates | Risk perception δ factor, dynamic updates |
| **Numbeo Cost Indices** | 156 countries | Cost of living, rent, restaurant prices | Utility function β factor (affordability) |
| **WHO Air Quality** | Global | PM2.5 concentrations | Environmental quality modifier (deferred) |
| **UNESCO Heritage Sites** | 60 countries | Site count, type, capacity | Cultural attractiveness (deferred) |
| **OECD Economic Indicators** | 55 countries | GDP, employment, nights spent | Economic context (Stage 3 enhancement) |

The merged dataset contains **8,911 country-year observations** (177 countries × ~50 years), providing empirical grounding for capacity estimation, attractiveness normalization, and validation benchmarks.

### 2.2 Literature Review: Six Foundational Papers

We reviewed and integrated findings from six peer-reviewed papers (combined 2,500+ citations):

| Paper | Citations | Key Insight | Implementation |
|-------|-----------|-------------|----------------|
| **Bertocchi et al. (2020)** - Venice carrying capacity | 140 | Multi-subsystem capacity with linear degradation (not quadratic); 80% threshold triggers resident dissatisfaction | Capacity = hotel beds × 0.80 × 1.10; TFI decline at >80% crowding |
| **Rosselló et al. (2020)** - Natural disaster elasticities | 438 | Disaster type matters: volcanic eruptions (-4.5% per $1M cost) more damaging than storms (-0.003%); recovery 6-12 months | Event type differentiation; linear recovery for disasters |
| **Škare et al. (2021)** - COVID-19 impact | 882 | Hybrid recovery pattern: double-dip (years 0-2) followed by S-curve (years 2+); spending loss exceeded arrival loss | Hybrid recovery function for epidemics |
| **Peng et al. (2014)** - Business/leisure elasticities (meta-analysis of 195 studies) | 195 studies | Business travelers 3× less price-sensitive than leisure (elasticity -0.35 vs. -1.10) | Purpose modifier: business cost weight × 0.3 |
| **Sönmez & Graefe (1998)** - Return visitor patterns | 382 | Past visitors 3-5× more likely to return (0.55-0.65 probability); experience reduces risk avoidance | Memory factor ζ in utility; satisfaction recording |
| **Muler González et al. (2018)** - Overtourism thresholds | 337 | 80% capacity triggers resident dissatisfaction; social carrying capacity distinct from physical | TFI dynamics: -0.05/day when crowding >80% |

### 2.3 Critical Empirical Finding: TTDI Explains Only 13% of Variance

Our correlation analysis of the merged dataset revealed that TTDI attractiveness correlates with arrivals at r = 0.364, implying **r² = 0.13**: only 13% of tourism variation is explained by destination quality attributes. The remaining 87% stems from factors not captured in static indices: geographic proximity, flight connectivity, cultural ties, visa policies, marketing spend, and historical patterns.

This finding fundamentally shaped our approach. Rather than attempting to build a predictive model (which would require data we don't have), we built an **exploratory tool** that makes uncertainty explicit. The simulation does not forecast "France will receive 82M tourists in 2026." Instead, it answers: "If Luxury travelers double their trip frequency, how do destination patterns shift? If a disaster hits Thailand, do nearby countries benefit from spillover or suffer from regional confidence collapse?"

---

## 3. Relevant Learnings: What Shaped the Simulation Design

### 3.1 Distance as Dominant Factor for Budget and Family Segments

Initial literature suggested cost would dominate Budget traveler decisions and quality would dominate Luxury decisions. However, when we normalized all utility factors to 0-1 scales and calibrated weights against observed correlations, **distance emerged as the strongest predictor** for Budget (η = 0.34) and Family (η = 0.40) segments. This aligns with geographic economics literature on distance decay, but contradicts naive assumptions that "budget travelers chase low prices regardless of location."

**Implementation consequence**: The utility function includes a dedicated distance factor calculated via haversine formula (great-circle distance between country centroids), pre-computed for all 31,329 country pairs at startup for O(1) lookup during simulation.

### 3.2 Business Travel Embedded in Segments, Not Separate

UN Tourism data reports an 11%/89% business/personal split, but does not cross-tabulate by traveler type (Budget/Luxury/etc.). Rather than create a parallel "purpose" dimension (which would double segment complexity), we embedded business probability within segments: Luxury travelers have 40% business probability (executive travel), Budget travelers 15% (cost-conscious corporate travel), Adventure 5%, and Family 0%. This produces ~11% overall business travel while maintaining segment coherence.

**Implementation consequence**: Purpose is assigned at agent creation, not per trip. Business travelers apply a cost-sensitivity modifier (β weight × 0.3) reflecting Peng et al.'s elasticity findings.

### 3.3 TFI as Moderator, Not Utility Factor

Early drafts included TFI as a ninth utility factor. However, literature (Muler González, Cheung & Li) describes TFI as a **destination-state moderator**: resident attitudes affect policy (capacity restrictions) and reputation (media coverage), not individual tourist utility directly. A tourist doesn't think "locals dislike tourists, so I'll assign -0.1 utility." Instead, the destination responds to overcrowding by reducing effective capacity and suffering negative media coverage.

**Implementation consequence**: TFI modifies destination.effective_capacity and destination.effective_attractiveness properties, not the utility function. This keeps the utility function at 6 factors while capturing policy feedback dynamics.

### 3.4 Popularity and Social Media Removed for Lack of Empirical Grounding

The initial 8-factor utility function included Popularity (θ, rich-get-richer feedback) and Social Media (ε, UGC influence). However, neither factor had direct empirical support: popularity mechanisms are theorized in network science literature but not calibrated for tourism, and social media effects (Litvin, Leung) lack quantitative parameters.

**Implementation consequence**: Removed both factors, resulting in a cleaner 6-factor utility function with stronger empirical backing. Popularity-like dynamics emerge endogenously through memory effects (return visitors) and capacity constraints (popular destinations fill up, forcing redistribution).

### 3.5 Trip Frequency as Poisson Process, Not Fixed Schedule

Literature on trip frequency by segment is nonexistent. Rather than assign fixed intervals (e.g., "Budget travelers take 1 trip every 365 days"), we modeled trip initiation as a **Poisson process** with segment-specific rates: each day, a home-based tourist has probability p = (trips_per_year / 365) of starting a trip, modified by seasonality and event appeal. This produces natural variation: some Budget travelers take 0 trips in a year, others take 2; Luxury travelers cluster around 3 but exhibit stochasticity.

**Implementation consequence**: The `Tourist._sample_next_trip_interval()` method uses exponential distribution sampling, producing realistic inter-trip variability.

---

## 4. Narrowed Approach: Demonstrating Complex Systems Concepts

Our final design prioritizes **mechanism clarity** over comprehensiveness. Rather than model every conceivable factor (flight networks, city-level granularity, marketing spend, colonial history), we focus on six core mechanisms that demonstrate complex systems concepts taught in this course:

### 4.1 Emergence: Hub Formation from Micro-Level Choices

**Concept**: Macro patterns (Paris, Bangkok, Dubai as hubs) emerge from micro-level destination choices, not top-down assignment.

**Mechanism**: Tourists choose destinations via softmax probabilistic choice with segment-specific temperatures. Luxury travelers (τ = 0.8) make more deterministic choices, concentrating in high-attractiveness destinations. Budget travelers (τ = 1.2) explore more widely. Over time, this produces hub-and-spoke patterns without explicit "hub" designation.

**Validation**: Top 10 destinations by arrivals should capture 40-60% of total flows (Gini coefficient 0.60-0.80).

### 4.2 Feedback Loops: TFI Dynamics and Policy Responses

**Concept**: System state (crowding) triggers endogenous responses (policy restrictions) that alter future dynamics.

**Mechanism**: When crowding >80%, TFI declines at 0.05/day. When TFI <0.60, effective capacity reduces to 85%; when TFI <0.40, capacity reduces to 70% and attractiveness suffers 20% penalty (negative media). This creates a balancing feedback loop: overcrowding → restrictions → reduced arrivals → recovery.

**Validation**: Destinations exceeding 80% capacity should show TFI decline within 10-20 days, followed by arrival reduction.

### 4.3 Heterogeneity: Segment-Specific Shock Responses

**Concept**: System components respond differently to the same perturbation.

**Mechanism**: Disaster events apply risk multipliers that vary by segment: Family travelers multiply risk by 1.9 (0.7 severity × 0.9 sensitivity + baseline), Adventure travelers by 1.21 (0.7 × 0.3 + baseline). This produces differential behavioral responses: Family arrivals drop 40%, Adventure arrivals drop 15%.

**Validation**: Post-disaster, segment mix should shift toward Adventure/Budget, away from Family/Luxury.

### 4.4 Critical Transitions: 80% Capacity Threshold

**Concept**: Systems exhibit qualitative behavioral shifts at threshold points.

**Mechanism**: The 80% crowding threshold (from Muler González et al.) triggers TFI decline. Below 80%, destinations are "normal" (green/yellow visualization). Above 80%, they enter "high crowding" (orange) and eventually "critical" (red, >100%). The transition is continuous in crowding ratio but discontinuous in policy response.

**Validation**: Destinations should spend most time in 40-70% utilization, with brief excursions to 80-100% during peak seasons.

### 4.5 Path Dependence: Memory and Return Visitors

**Concept**: History matters; past states influence future behavior.

**Mechanism**: When tourists complete trips, they record satisfaction scores (-1 to +1) for visited destinations. On future choice occasions, previously visited destinations receive utility bonuses proportional to satisfaction. This creates path dependence: tourists who enjoyed France are more likely to return, reinforcing hub status.

**Validation**: Return visitor probability should be 0.55-0.65 (matching Sönmez & Graefe).

### 4.6 Geographic Friction: Distance Decay

**Concept**: Interaction strength declines with separation.

**Mechanism**: Distance penalty = η × (distance_km / 20,000). For Family travelers (η = 0.40), a 10,000 km trip incurs -0.20 utility (equivalent to -20% attractiveness). This produces realistic regional clustering: Europeans travel within Europe (65% intra-regional), Americans within Americas (55%).

**Validation**: Intra-regional flow percentages should match UN Tourism patterns (Europe 65%, Americas 55%, Asia-Pacific 55%).

---

## 5. Current Status and Next Steps

### 5.1 What Is Operational

- ✅ **Core simulation**: 4,000 agents, 177 destinations, 6-factor utility, softmax choice
- ✅ **Events system**: Planned events (FIFA 2026 pre-loaded), unplanned events (disaster/epidemic triggers)
- ✅ **TFI dynamics**: Crowding → TFI decline → policy restrictions → capacity reduction
- ✅ **Dashboard**: Real-time map visualization, time series charts, speed controls, event triggering
- ✅ **Data collection**: Aggregate metrics, segment breakdowns, 100-agent trajectory sampling
- ✅ **Validation tests**: Trip frequency by segment matches literature (±50% tolerance)

### 5.2 What Requires Further Work

- ⏳ **Full validation suite**: Tier 2-4 tests (distributional, emergent, sensitivity) not yet automated
- ⏳ **Performance optimization**: Current timestep ~100ms; target <50ms for 4× speed smoothness
- ⏳ **Dashboard enhancements**: Click-to-inspect countries, scenario save/load, data export
- ⏳ **Documentation**: Inline docstrings, module READMEs, user guide

### 5.3 Stage 3 Enhancements (Optional, Time-Permitting)

- Flight network proxy (GDP-based connectivity)
- City-level granularity (multiple cities per country)
- Dynamic capacity investment (infrastructure growth)
- Policy intervention toolkit (tourist taxes, visa changes)

---

## 6. Conclusion: Tourism as a Complex Adaptive System

Our work suggests that global tourism exhibits the hallmarks of complex adaptive systems:

1. **Emergence**: Hub formation arises from distributed choices, not central planning
2. **Feedback loops**: TFI dynamics create balancing responses to overcrowding
3. **Heterogeneity**: Segment-specific responses produce differential impacts
4. **Critical transitions**: 80% capacity threshold triggers qualitative behavioral shifts
5. **Path dependence**: Memory effects create lock-in and return visitor loyalty
6. **Geographic friction**: Distance decay produces regional clustering patterns

These characteristics imply that tourism policy cannot rely on aggregate equilibrium models alone. Interventions (tourist taxes, capacity caps, marketing campaigns) interact with heterogeneous agent behavior in non-linear ways. A tax that reduces Budget traveler arrivals by 30% may have minimal impact on Luxury arrivals, shifting segment mix and altering destination economics in unpredictable ways.

The simulation we have built does not predict the future. It illuminates plausible dynamics under specified conditions, making uncertainty explicit and enabling structured experimentation. We believe this approach—agent-based, empirically grounded, exploratory rather than predictive—offers a more honest and useful tool for understanding complexity in global tourism than traditional forecasting models that claim precision they cannot deliver.

---

**Prepared by**: Simulation Development Team  
**Date**: April 21, 2026  
**Project Repository**: `/Users/joelvzach/Code/ssie_523`
