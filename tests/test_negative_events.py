"""
Test script to verify negative event system and resilience metrics.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation.data.loaders import load_country_data
from simulation.simulation import Simulation


def test_negative_events():
    """Test that negative events properly affect tourist behavior."""
    
    print(f"\n{'='*70}")
    print(f"NEGATIVE EVENT SYSTEM TEST")
    print(f"{'='*70}\n")
    
    # Load data
    countries = load_country_data()
    
    # Initialize simulation
    config = {
        "agent_count": 40000,  # Higher count for better signal
        "segment_shares": {
            "budget": 0.30,
            "luxury": 0.20,
            "adventure": 0.25,
            "family": 0.25,
        },
        "seed": 42,
        "start_date": "2026-01-01",
    }
    
    sim = Simulation(config=config, countries_data=countries)
    sim.initialize()
    
    print("Phase 0: Warmup (reach steady state)")
    print(f"{'-'*70}")
    
    # Warmup period to reach steady state
    baseline_visitors = defaultdict(list)
    for day in range(60):
        sim.step()
        # Collect baseline from last 30 days of warmup
        if day >= 30:
            for code, dest in sim.destinations.items():
                baseline_visitors[code].append(dest.get_current_visitors())
    
    print(f"Warmup complete. Day {sim.tick}, Active travelers: {sum(1 for a in sim.agents if a.state == 'TRAVELING')}")
    
    # Find destinations with actual traffic
    active_destinations = []
    for code, visitors in baseline_visitors.items():
        avg = sum(visitors) / len(visitors) if visitors else 0
        if avg > 0:
            active_destinations.append((code, avg))
    
    active_destinations.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nDestinations with traffic: {len(active_destinations)}")
    if active_destinations:
        print(f"Top 5: {', '.join([f'{c[0]}({c[1]:.1f})' for c in active_destinations[:5]])}")
    
    # Choose a destination with traffic for the event test
    test_country = "MEX" if any(c[0] == "MEX" for c in active_destinations) else (active_destinations[0][0] if active_destinations else "FRA")
    test_dest_name = sim.destinations.get(test_country)
    
    print(f"\nPhase 1: Baseline (no events)")
    print(f"{'-'*70}")
    print(f"Testing event impact on: {test_dest_name.country_name if test_dest_name else test_country} ({test_country})")
    
    # Get baseline averages for top destinations
    baseline_avg = {
        code: sum(visitors) / len(visitors)
        for code, visitors in baseline_visitors.items()
    }
    
    top_5_baseline = sorted(baseline_avg.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"Top 5 destinations (avg visitors):")
    for code, avg in top_5_baseline:
        dest_name = sim.destinations.get(code)
        print(f"  {dest_name.country_name if dest_name else code}: {avg:.1f}")
    
    print(f"\nPhase 2: Trigger event in {test_dest_name.country_name if test_dest_name else test_country} (Day {sim.tick + 1})")
    print(f"{'-'*70}")
    
    # Trigger event in test country
    from simulation.events.unplanned_events import UnplannedEvent
    
    event = UnplannedEvent(
        name=f"{test_dest_name.country_name if test_dest_name else test_country} Disaster",
        country_code=test_country,
        start_date=sim.current_date,
        event_type="disaster",
        severity=0.8,  # High severity
        duration_months=2,  # 60 days
    )
    
    sim.unplanned_events.add_event(event)
    print(f"Event triggered: {event.name}")
    print(f"  Country: {test_dest_name.country_name if test_dest_name else test_country} ({test_country})")
    print(f"  Severity: {event.severity:.0%}")
    print(f"  Duration: {event.duration_months} months")
    print(f"  End date: {event.end_date.strftime('%Y-%m-%d')}")
    
    # Check risk multiplier
    test_date = sim.current_date
    risk_mult_budget = sim.unplanned_events.get_risk_multiplier(test_country, "budget", test_date)
    risk_mult_family = sim.unplanned_events.get_risk_multiplier(test_country, "family", test_date)
    print(f"\nRisk multipliers on {test_date.strftime('%Y-%m-%d')}:")
    print(f"  Budget tourist: {risk_mult_budget:.2f}x")
    print(f"  Family tourist: {risk_mult_family:.2f}x")
    
    print(f"\nPhase 3: Run simulation with event (Days 31-90)")
    print(f"{'-'*70}")
    
    # Continue running with event active
    event_visitors = defaultdict(list)
    for day in range(60):
        sim.step()
        for code, dest in sim.destinations.items():
            event_visitors[code].append(dest.get_current_visitors())
        
        # Log at key points
        if day in [0, 9, 19, 29, 49, 59]:
            test_visitors = sim.destinations[test_country].get_current_visitors()
            print(f"  Day {sim.tick}: {test_dest_name.country_name if test_dest_name else test_country} visitors = {test_visitors}")
    
    # Analyze impact
    print(f"\n{'='*70}")
    print(f"IMPACT ANALYSIS")
    print(f"{'='*70}\n")
    
    # Test country specific analysis
    test_baseline = baseline_visitors[test_country]
    test_during = event_visitors[test_country][:30]  # First 30 days of event
    test_late = event_visitors[test_country][30:]  # Last 30 days (recovery)
    
    avg_baseline = sum(test_baseline) / len(test_baseline) if test_baseline else 0
    avg_during = sum(test_during) / len(test_during) if test_during else 0
    avg_late = sum(test_late) / len(test_late) if test_late else 0
    
    impact_immediate = (avg_baseline - avg_during) / avg_baseline * 100 if avg_baseline > 0 else 0
    impact_recovery = (avg_baseline - avg_late) / avg_baseline * 100 if avg_baseline > 0 else 0
    
    print(f"{test_dest_name.country_name if test_dest_name else test_country} Visitor Impact:")
    print(f"  Baseline avg (last 30 days):   {avg_baseline:.1f} visitors")
    print(f"  During event (days 1-30):      {avg_during:.1f} visitors")
    print(f"  Late event (days 31-60):       {avg_late:.1f} visitors")
    print()
    print(f"  Immediate impact:              📉 {impact_immediate:.1f}% reduction")
    print(f"  Recovery impact:               📉 {impact_recovery:.1f}% reduction")
    
    # Check if other destinations benefited (substitution effect)
    print(f"\nSubstitution Effect (did tourists go elsewhere?):")
    
    substitution_candidates = []
    for code, visitors in event_visitors.items():
        if code == test_country:
            continue
        
        baseline_avg_code = sum(baseline_visitors[code]) / len(baseline_visitors[code]) if baseline_visitors[code] else 0
        during_avg_code = sum(visitors[:30]) / len(visitors[:30]) if visitors[:30] else 0
        
        change_pct = (during_avg_code - baseline_avg_code) / baseline_avg_code * 100 if baseline_avg_code > 0 else 0
        
        if change_pct > 10:  # More than 10% increase
            dest_name = sim.destinations.get(code)
            substitution_candidates.append((dest_name.country_name if dest_name else code, change_pct))
    
    substitution_candidates.sort(key=lambda x: x[1], reverse=True)
    
    if substitution_candidates:
        for dest, pct in substitution_candidates[:5]:
            print(f"  {dest}: 📈 +{pct:.1f}%")
    else:
        print(f"  No significant substitution detected (may need longer simulation)")
    
    # Resilience metrics
    print(f"\n{'='*70}")
    print(f"RESILIENCE METRICS")
    print(f"{'='*70}\n")
    
    # Recovery rate
    if avg_during > 0:
        recovery_rate = (avg_late - avg_during) / (avg_baseline - avg_during) * 100
        print(f"Recovery Rate: {recovery_rate:.1f}%")
        
        if recovery_rate > 70:
            print(f"  Assessment: ✅ HIGH RESILIENCE - Quick recovery")
        elif recovery_rate > 40:
            print(f"  Assessment: ⚠️  MODERATE RESILIENCE - Partial recovery")
        else:
            print(f"  Assessment: ❌ LOW RESILIENCE - Slow recovery")
    
    # Event visibility
    if impact_immediate > 20:
        print(f"\nEvent Impact: ✅ VISIBLE - Clear {impact_immediate:.0f}% drop in visitors")
    elif impact_immediate > 10:
        print(f"\nEvent Impact: ⚠️  MODERATE - {impact_immediate:.0f}% drop (may be noisy)")
    else:
        print(f"\nEvent Impact: ❌ MINIMAL - Only {impact_immediate:.0f}% drop")
        print(f"  Recommendation: Increase severity or agent count for clearer signal")
    
    print(f"\n{'='*70}\n")
    
    return {
        'baseline_avg': avg_baseline,
        'during_avg': avg_during,
        'late_avg': avg_late,
        'impact_immediate': impact_immediate,
        'impact_recovery': impact_recovery,
        'recovery_rate': recovery_rate if avg_during > 0 else 0,
    }


if __name__ == "__main__":
    metrics = test_negative_events()
    
    # Expected benchmarks:
    # - High severity (0.8) should cause 30-50% immediate drop
    # - Recovery should show 40-70% improvement by end of event
    # - Some substitution to nearby destinations expected
    
    print("BENCHMARK COMPARISON:")
    print(f"{'Metric':<25} {'Actual':>12} {'Target Range':>20} {'Status':>10}")
    print(f"{'-'*70}")
    
    # Immediate impact
    impact_status = "✓" if 30 <= metrics['impact_immediate'] <= 60 else "⚠️" if 15 <= metrics['impact_immediate'] < 30 else "✗"
    print(f"Immediate Impact %:       {metrics['impact_immediate']:>11.1f}%  30-60%              {impact_status}")
    
    # Recovery
    recovery_status = "✓" if 40 <= metrics['recovery_rate'] <= 80 else "⚠️" if 20 <= metrics['recovery_rate'] < 40 else "✗"
    print(f"Recovery Rate %:          {metrics['recovery_rate']:>11.1f}%  40-80%              {recovery_status}")
