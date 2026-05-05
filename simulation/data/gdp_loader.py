"""
World Bank GDP Data Loader

Parses World Bank GDP data and provides caching for fast re-loads.
"""

import csv
import json
import pickle
from pathlib import Path
from typing import Dict, Optional, List

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def load_world_bank_gdp(
    data_dir: Path = None,
    cache_dir: Path = None,
    use_cache: bool = True,
    target_year: Optional[int] = None,
) -> Dict[str, float]:
    """
    Load World Bank GDP data.

    Args:
        data_dir: Path to World Bank data directory
        cache_dir: Path to cache directory (defaults to data_dir/../cache)
        use_cache: Whether to use cached data if available
        target_year: Target year for GDP data (defaults to most recent available)

    Returns:
        Dict mapping country_code → gdp_usd (current USD)
    """
    if data_dir is None:
        data_dir = (
            Path(__file__).parent.parent.parent
            / "data"
            / "API_NY.GDP.MKTP.CD_DS2_en_csv_v2_126992"
        )

    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "gdp_data_cache.pkl"

    # Try to load from cache
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                cached_data = pickle.load(f)
            print(
                f"[GDP Loader] Loaded cached GDP data for {len(cached_data)} countries"
            )
            return cached_data
        except Exception as e:
            print(f"[GDP Loader] Cache load failed: {e}, re-parsing CSV...")

    # Parse CSV (skip first 5 metadata rows)
    gdp_file = data_dir / "API_NY.GDP.MKTP.CD_DS2_en_csv_v2_126992.csv"

    if not gdp_file.exists():
        print(f"[GDP Loader] Warning: GDP file not found: {gdp_file}")
        return {}

    country_gdp = {}
    latest_year_found = 1960  # Default to earliest year

    # Use pandas if available (handles World Bank CSV format correctly)
    if HAS_PANDAS:
        import pandas as pd

        # Skip first 4 rows, use row 5 as header
        df = pd.read_csv(gdp_file, skiprows=4)

        year_columns = [str(y) for y in range(1960, 2026)]

        for _, row in df.iterrows():
            country_code = row.get("Country Code", "")
            country_name = row.get("Country Name", "")

            if not country_code or pd.isna(country_code):
                continue

            # Find most recent non-empty GDP value
            gdp_value = None
            gdp_year = None

            if target_year is not None and str(target_year) in df.columns:
                val = row.get(target_year)
                if pd.notna(val):
                    try:
                        gdp_value = float(val)
                        gdp_year = target_year
                    except (ValueError, TypeError):
                        pass

            if gdp_value is None:
                # Find most recent available
                for year in reversed(year_columns):
                    if year not in df.columns:
                        continue
                    val = row.get(year)
                    if pd.notna(val):
                        try:
                            gdp_value = float(val)
                            gdp_year = int(year)
                            if gdp_year > latest_year_found:
                                latest_year_found = gdp_year
                            break
                        except (ValueError, TypeError):
                            continue

            if gdp_value is not None:
                country_gdp[country_code] = {
                    "gdp_usd": gdp_value,
                    "year": gdp_year,
                    "name": country_name,
                }
    else:
        # Fallback to csv module (less reliable for World Bank format)
        print("[GDP Loader] Warning: pandas not available, using fallback parser")
        # ... fallback implementation if needed ...
        return {}

    # Save cache
    with open(cache_file, "wb") as f:
        pickle.dump(country_gdp, f)

    print(
        f"[GDP Loader] Parsed GDP data for {len(country_gdp)} countries (year: {latest_year_found if latest_year_found else 'various'})"
    )
    return country_gdp


def calculate_tourism_gdp_pct(
    tourism_expenditure_usd_millions: float,
    gdp_usd: float,
) -> float:
    """
    Calculate tourism GDP percentage.

    Args:
        tourism_expenditure_usd_millions: Tourism expenditure in millions USD
        gdp_usd: GDP in current USD

    Returns:
        Tourism GDP percentage (0-100+)
    """
    if gdp_usd <= 0:
        return 0.0

    tourism_revenue_usd = tourism_expenditure_usd_millions * 1_000_000
    return (tourism_revenue_usd / gdp_usd) * 100


def get_tourism_dependency_category(tourism_gdp_pct: float) -> str:
    """
    Classify tourism dependency based on GDP percentage.

    Thresholds based on WTTC Economic Impact Reports and UNWTO TSA:

    | Category | Tourism-GDP % | Examples |
    |----------|---------------|----------|
    | Highly Dependent | >30% | Maldives, Aruba, Seychelles |
    | Moderately Dependent | 10-30% | Thailand, Croatia, Greece |
    | Low Dependency | 3-10% | Spain, France, Italy, Turkey |
    | Minimal Dependency | <3% | USA, Japan, Germany, China |

    Args:
        tourism_gdp_pct: Tourism GDP percentage

    Returns:
        Category string: 'highly_dependent', 'moderately_dependent', 'low_dependency', or 'minimal_dependency'
    """
    if tourism_gdp_pct > 30:
        return "highly_dependent"
    elif tourism_gdp_pct > 10:
        return "moderately_dependent"
    elif tourism_gdp_pct > 3:
        return "low_dependency"
    else:
        return "minimal_dependency"


def get_tfi_decline_modifier(tourism_gdp_pct: float) -> float:
    """
    Get TFI decline rate modifier based on tourism dependency.

    Literature basis: Butler (2019), Muler González et al. (2018)
    Economic necessity moderates resident tolerance for overtourism.

    Args:
        tourism_gdp_pct: Tourism GDP percentage

    Returns:
        Multiplier for base TFI decline rate (0.5 = 50% slower decline)
    """
    if tourism_gdp_pct > 30:
        return 0.5  # 50% slower decline (highly dependent)
    elif tourism_gdp_pct > 10:
        return 0.75  # 25% slower decline (moderately dependent)
    else:
        return 1.0  # Normal decline rate


def export_tourism_gdp_table(
    tourism_data_dir: Path = None,
    gdp_data: Dict = None,
    output_file: Path = None,
    target_year: int = 2019,
) -> List[Dict]:
    """
    Export tourism GDP percentage table for analysis.

    Args:
        tourism_data_dir: Path to merged tourism data
        gdp_data: Pre-loaded GDP data (or None to load)
        output_file: Output CSV path (or None for in-memory only)
        target_year: Year for analysis

    Returns:
        List of dicts with country tourism GDP data
    """
    import csv

    if tourism_data_dir is None:
        tourism_data_dir = Path(__file__).parent.parent.parent / "data" / "merged"

    if gdp_data is None:
        gdp_data = load_world_bank_gdp(target_year=target_year)

    tourism_file = tourism_data_dir / "tourism_comprehensive_1995_2024.csv"
    mapping_file = (
        Path(__file__).parent.parent.parent
        / "data"
        / "derived"
        / "country_code_mapping.csv"
    )

    # Load country code mapping
    numeric_to_iso3 = {}
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                numeric_code = row.get("country_code", "")
                iso3_code = row.get("Country Code", "")
                if numeric_code and iso3_code:
                    numeric_to_iso3[numeric_code] = iso3_code

    if not tourism_file.exists():
        print(f"[GDP Loader] Tourism data not found: {tourism_file}")
        return []

    results = []
    seen_countries = set()

    with open(tourism_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            country_code = row.get("country_code", "")
            year = row.get("year", "")

            if str(year) != str(target_year):
                continue

            if country_code in seen_countries:
                continue
            seen_countries.add(country_code)

            expenditure_str = row.get("tourism_expenditure_usd_millions", "")
            if not expenditure_str or country_code not in gdp_data:
                continue

            try:
                expenditure = float(expenditure_str)
            except ValueError:
                continue

            gdp_info = gdp_data[country_code]
            gdp_usd = gdp_info["gdp_usd"]

            tourism_gdp_pct = calculate_tourism_gdp_pct(expenditure, gdp_usd)
            category = get_tourism_dependency_category(tourism_gdp_pct)
            modifier = get_tfi_decline_modifier(tourism_gdp_pct)

            results.append(
                {
                    "country_code": country_code,
                    "country_name": row.get("country_name", ""),
                    "year": target_year,
                    "tourism_expenditure_usd_millions": expenditure,
                    "gdp_usd": gdp_usd,
                    "tourism_gdp_pct": tourism_gdp_pct,
                    "dependency_category": category,
                    "tfi_decline_modifier": modifier,
                }
            )

    # Sort by tourism GDP percentage (descending)
    results.sort(key=lambda x: x["tourism_gdp_pct"], reverse=True)

    # Export to CSV if requested
    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = [
                "country_code",
                "country_name",
                "year",
                "tourism_expenditure_usd_millions",
                "gdp_usd",
                "tourism_gdp_pct",
                "dependency_category",
                "tfi_decline_modifier",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(
            f"[GDP Loader] Exported tourism GDP table: {output_file} ({len(results)} countries)"
        )

    return results


if __name__ == "__main__":
    # Test run
    print("=" * 80)
    print("GDP LOADER TEST RUN")
    print("=" * 80)

    # Load GDP data
    gdp_data = load_world_bank_gdp(use_cache=False)
    print(f"\nLoaded GDP for {len(gdp_data)} countries")

    # Show sample
    sample_codes = ["ABW", "BHS", "SYC", "MDV", "USA", "ESP", "FRA", "DEU"]
    print("\nSample GDP data:")
    for code in sample_codes:
        if code in gdp_data:
            info = gdp_data[code]
            print(
                f"  {code} ({info['name']}): ${info['gdp_usd'] / 1e9:.2f}B ({info['year']})"
            )

    # Export tourism GDP table
    print("\nExporting tourism GDP table...")
    results = export_tourism_gdp_table(
        output_file=Path(__file__).parent.parent.parent
        / "data"
        / "derived"
        / "tourism_gdp_analysis_2019.csv",
        target_year=2019,
    )

    # Show top 10 tourism-dependent economies
    print("\nTop 10 Tourism-Dependent Economies (2019):")
    for i, row in enumerate(results[:10], 1):
        print(
            f"  {i:2d}. {row['country_name']:30s} {row['tourism_gdp_pct']:6.1f}% ({row['dependency_category']})"
        )

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
