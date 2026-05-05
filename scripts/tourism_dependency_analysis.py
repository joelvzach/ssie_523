#!/usr/bin/env python3
"""
Tourism Dependency Analysis Script

Analyzes tourism GDP percentages across countries and generates:
1. CSV export with tourism GDP data
2. Summary statistics table
3. Top tourism-dependent economies ranking
4. Validation vs OECD data (where available)

Usage:
    python scripts/tourism_dependency_analysis.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.data.gdp_loader import (
    load_world_bank_gdp,
    export_tourism_gdp_table,
    get_tourism_dependency_category,
)
from simulation.data.tourism_gdp import TourismGDPManager


def print_separator(title: str = ""):
    print("\n" + "=" * 80)
    if title:
        print(f" {title}")
        print("=" * 80)


def print_table(headers: list, rows: list, col_widths: list = None):
    """Print formatted table."""
    if col_widths is None:
        col_widths = [
            max(len(str(row[i])) for row in [headers] + rows)
            for i in range(len(headers))
        ]

    # Header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))

    # Rows
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))


def main():
    print_separator("TOURISM DEPENDENCY ANALYSIS")

    # 1. Initialize tourism GDP manager
    print("\n[1/5] Loading tourism GDP data...")
    manager = TourismGDPManager(target_year=2019)

    summary = manager.get_summary_statistics()
    print(f"  Countries analyzed: {summary['total_countries']}")
    print(f"  Baseline year: {summary['target_year']}")
    print(f"  Mean tourism GDP %: {summary['mean_tourism_gdp_pct']:.2f}%")
    print(f"  Median tourism GDP %: {summary['median_tourism_gdp_pct']:.2f}%")
    print(
        f"  Range: {summary['min_tourism_gdp_pct']:.2f}% - {summary['max_tourism_gdp_pct']:.2f}%"
    )

    # 2. Export CSV
    print("\n[2/5] Exporting tourism GDP table...")
    output_file = (
        Path(__file__).parent.parent
        / "data"
        / "derived"
        / "tourism_gdp_analysis_2019.csv"
    )
    results = export_tourism_gdp_table(output_file=output_file, target_year=2019)
    print(f"  Exported: {output_file}")

    # 3. Summary by category
    print_separator("TOURISM DEPENDENCY BY CATEGORY")

    categories = summary["by_category"]
    category_headers = ["Category", "Count", "Pct of Total"]
    category_rows = []
    total = sum(categories.values())

    for cat in [
        "highly_dependent",
        "moderately_dependent",
        "low_dependency",
        "minimal_dependency",
    ]:
        count = categories.get(cat, 0)
        pct = (count / total * 100) if total > 0 else 0
        cat_display = cat.replace("_", " ").title()
        category_rows.append([cat_display, count, f"{pct:.1f}%"])

    print_table(category_headers, category_rows, col_widths=[25, 10, 15])

    # 4. Top tourism-dependent economies
    print_separator("TOP 20 TOURISM-DEPENDENT ECONOMIES (2019)")

    top_headers = ["Rank", "Country", "Tourism GDP %", "Category", "TFI Modifier"]
    top_rows = []

    for i, row in enumerate(results[:20], 1):
        cat_short = (
            row["dependency_category"]
            .replace("_dependent", "")
            .replace("_dependency", "")
            .title()
        )
        top_rows.append(
            [
                str(i),
                row["country_name"][:30],
                f"{row['tourism_gdp_pct']:.1f}%",
                cat_short,
                f"{row['tfi_decline_modifier']:.2f}x",
            ]
        )

    print_table(top_headers, top_rows, col_widths=[6, 30, 12, 15, 12])

    # 5. Small Island States (SIDS) analysis
    print_separator("SMALL ISLAND DEVELOPING STATES (SIDS)")

    sids_codes = [
        "MDV",
        "SYC",
        "MUS",
        "FJI",
        "VUT",
        "WSM",
        "TON",
        "VCT",
        "LCA",
        "GRD",
        "ABW",
        "BHS",
        "BRB",
    ]
    sids_results = [r for r in results if r["country_code"] in sids_codes]
    sids_results.sort(key=lambda x: x["tourism_gdp_pct"], reverse=True)

    sids_headers = ["Country", "Tourism GDP %", "Category", "TFI Modifier"]
    sids_rows = []

    for row in sids_results:
        cat_short = (
            row["dependency_category"]
            .replace("_dependent", "")
            .replace("_dependency", "")
            .title()
        )
        sids_rows.append(
            [
                row["country_name"][:30],
                f"{row['tourism_gdp_pct']:.1f}%",
                cat_short,
                f"{row['tfi_decline_modifier']:.2f}x",
            ]
        )

    if sids_rows:
        print_table(sids_headers, sids_rows, col_widths=[30, 12, 15, 12])
    else:
        print("  No SIDS data available (may not have tourism expenditure data)")

    # 6. Validation vs OECD data
    print_separator("VALIDATION VS OECD DATA (Selected Countries)")

    # Known OECD tourism GDP shares for 2019
    oecd_validation = {
        "ESP": 12.4,  # Spain
        "HRV": 11.8,  # Croatia
        "ISL": 8.0,  # Iceland
        "MEX": 8.1,  # Mexico
        "PRT": 7.5,  # Portugal (estimated)
        "FRA": 7.2,  # France
        "MAR": 6.8,  # Morocco
        "TUR": 6.5,  # Turkey (estimated)
        "GRC": 6.0,  # Greece (estimated)
        "ITA": 5.5,  # Italy (estimated)
    }

    validation_headers = ["Country", "Calculated", "OECD Ref", "Diff"]
    validation_rows = []

    for code, oecd_val in oecd_validation.items():
        calc_row = next((r for r in results if r["country_code"] == code), None)
        if calc_row:
            calc_val = calc_row["tourism_gdp_pct"]
            diff = calc_val - oecd_val
            status = "✓" if abs(diff) < 2.0 else "⚠"
            validation_rows.append(
                [
                    calc_row["country_name"][:20],
                    f"{calc_val:.1f}%",
                    f"{oecd_val:.1f}%",
                    f"{diff:+.1f}% {status}",
                ]
            )

    if validation_rows:
        print_table(validation_headers, validation_rows, col_widths=[20, 12, 12, 15])
        print("\n  Note: Differences may arise from:")
        print("    - Different baseline years (OECD 2019 vs. our 2019)")
        print("    - Tourism expenditure vs. tourism value-added measurement")
        print("    - Direct vs. indirect + direct GDP contribution")
    else:
        print("  No validation data available")

    # 7. Regional summary
    print_separator("REGIONAL SUMMARY")

    # Simple regional mapping (could be enhanced with UN M49 standard)
    regional_mapping = {
        "Europe": [
            "ESP",
            "FRA",
            "ITA",
            "GBR",
            "DEU",
            "PRT",
            "GRC",
            "HRV",
            "AUT",
            "NLD",
        ],
        "Americas": ["USA", "MEX", "BRA", "CAN", "ARG", "COL", "DOM", "CUB"],
        "Asia-Pacific": [
            "CHN",
            "JPN",
            "THA",
            "KOR",
            "IND",
            "IDN",
            "MYS",
            "SGP",
            "VNM",
            "PHL",
        ],
        "Middle-East": ["ARE", "SAU", "TUR", "EGY", "JOR", "LBN"],
        "Africa": ["ZAF", "MAR", "TUN", "KEN", "TZA", "MUS", "SYC"],
    }

    # Reverse mapping
    country_to_region = {}
    for region, codes in regional_mapping.items():
        for code in codes:
            country_to_region[code] = region

    regional_stats = {}
    for row in results:
        code = row["country_code"]
        region = country_to_region.get(code, "Other")
        if region not in regional_stats:
            regional_stats[region] = []
        regional_stats[region].append(row["tourism_gdp_pct"])

    region_headers = ["Region", "Countries", "Mean %", "Max %", "Min %"]
    region_rows = []

    for region in sorted(regional_stats.keys()):
        values = regional_stats[region]
        region_rows.append(
            [
                region,
                len(values),
                f"{sum(values) / len(values):.1f}",
                f"{max(values):.1f}",
                f"{min(values):.1f}",
            ]
        )

    print_table(region_headers, region_rows, col_widths=[20, 12, 10, 10, 10])

    # 8. Key findings
    print_separator("KEY FINDINGS")

    highly_dependent = manager.get_countries_by_category("highly_dependent")
    moderately_dependent = manager.get_countries_by_category("moderately_dependent")

    print(
        f"\n  1. Highly dependent economies (>30%): {len(highly_dependent)} countries"
    )
    if highly_dependent:
        print(f"     Examples: {', '.join(highly_dependent[:5])}")

    print(
        f"\n  2. Moderately dependent economies (10-30%): {len(moderately_dependent)} countries"
    )
    if moderately_dependent:
        print(f"     Examples: {', '.join(moderately_dependent[:5])}")

    print(f"\n  3. TFI decline modification:")
    print(f"     - Highly dependent: 50% slower decline (economic necessity)")
    print(f"     - Moderately dependent: 25% slower decline")
    print(f"     - Low/Minimal: Normal decline rate")

    print(f"\n  4. Literature basis:")
    print(f"     - Butler (2019): Dynamic carrying capacity")
    print(
        f"     - Muler González et al. (2018): Economic dependency moderates tolerance"
    )
    print(f"     - Thresholds: WTTC Economic Impact Reports, UNWTO TSA")

    print_separator("ANALYSIS COMPLETE")
    print(f"\n  Output file: {output_file}")
    print(f"  Total countries: {len(results)}")
    print(f"  Baseline year: 2019 (pre-pandemic)")

    return results


if __name__ == "__main__":
    main()
