"""
Tourism GDP Integration Module

Provides tourism GDP percentage calculations and dependency classification
for destination agents.
"""

from pathlib import Path
from typing import Dict, Optional
from simulation.data.gdp_loader import (
    load_world_bank_gdp,
    calculate_tourism_gdp_pct,
    get_tourism_dependency_category,
    get_tfi_decline_modifier,
)


class TourismGDPManager:
    """
    Manages tourism GDP percentage data for all destinations.

    Pre-computes tourism GDP % at initialization for fast runtime access.
    """

    def __init__(
        self,
        tourism_data_dir: Optional[Path] = None,
        gdp_cache_dir: Optional[Path] = None,
        target_year: int = 2019,
    ):
        """
        Initialize tourism GDP manager.

        Args:
            tourism_data_dir: Path to merged tourism data directory
            gdp_cache_dir: Path to GDP cache directory
            target_year: Target year for GDP calculation (default: 2019 pre-pandemic baseline)
        """
        self.target_year = target_year
        self.tourism_gdp_data: Dict[str, Dict] = {}

        # Load GDP data
        self.gdp_data = load_world_bank_gdp(
            data_dir=gdp_cache_dir,
            use_cache=True,
            target_year=target_year,
        )

        # Load tourism expenditure and calculate tourism GDP %
        self._load_tourism_expenditure(tourism_data_dir)

    def _load_tourism_expenditure(self, tourism_data_dir: Optional[Path] = None):
        """
        Load tourism expenditure from merged dataset and calculate tourism GDP %.

        Tourism data uses UN M49 numeric codes (e.g., 8 = Albania),
        while World Bank GDP uses ISO3 alpha-3 codes (e.g., ALB = Albania).
        This method handles the code mapping.

        Args:
            tourism_data_dir: Path to merged tourism data directory
        """
        import csv

        if tourism_data_dir is None:
            tourism_data_dir = Path(__file__).parent.parent.parent / "data" / "merged"

        tourism_file = tourism_data_dir / "tourism_comprehensive_1995_2024.csv"
        mapping_file = (
            Path(__file__).parent.parent.parent
            / "data"
            / "derived"
            / "country_code_mapping.csv"
        )

        if not tourism_file.exists():
            print(f"[TourismGDP] Warning: Tourism data not found: {tourism_file}")
            return

        # Load country code mapping (numeric → ISO3)
        numeric_to_iso3 = {}
        if mapping_file.exists():
            with open(mapping_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    numeric_code = row.get("country_code", "")
                    iso3_code = row.get("Country Code", "")
                    if numeric_code and iso3_code:
                        numeric_to_iso3[numeric_code] = iso3_code
            print(
                f"[TourismGDP] Loaded code mapping for {len(numeric_to_iso3)} countries"
            )
        else:
            print(f"[TourismGDP] Warning: Code mapping not found: {mapping_file}")

        # Aggregate expenditure by country (multiple rows per country possible)
        country_expenditure = {}

        with open(tourism_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                numeric_code = row.get("country_code", "")
                year = row.get("year", "")

                # Filter to target year
                if str(year) != str(self.target_year):
                    continue

                # Get tourism expenditure
                expenditure_str = row.get("tourism_expenditure_usd_millions", "")
                if not expenditure_str:
                    continue

                try:
                    expenditure = float(expenditure_str)
                except ValueError:
                    continue

                # Aggregate (sum) expenditure for each country
                if numeric_code not in country_expenditure:
                    country_expenditure[numeric_code] = 0.0
                country_expenditure[numeric_code] += expenditure

        # Calculate tourism GDP % for each country (with code mapping)
        unmapped = 0
        no_gdp = 0

        for numeric_code, expenditure in country_expenditure.items():
            # Map numeric code to ISO3
            iso3_code = numeric_to_iso3.get(numeric_code)

            if not iso3_code:
                unmapped += 1
                continue

            # Get GDP
            if iso3_code not in self.gdp_data:
                no_gdp += 1
                continue

            gdp_info = self.gdp_data[iso3_code]
            gdp_usd = gdp_info["gdp_usd"]

            # Calculate tourism GDP %
            tourism_gdp_pct = calculate_tourism_gdp_pct(expenditure, gdp_usd)
            category = get_tourism_dependency_category(tourism_gdp_pct)
            modifier = get_tfi_decline_modifier(tourism_gdp_pct)

            # Store with ISO3 code
            self.tourism_gdp_data[iso3_code] = {
                "numeric_code": numeric_code,
                "tourism_expenditure_usd_millions": expenditure,
                "gdp_usd": gdp_usd,
                "gdp_year": gdp_info["year"],
                "tourism_gdp_pct": tourism_gdp_pct,
                "dependency_category": category,
                "tfi_decline_modifier": modifier,
                "target_year": self.target_year,
            }

        print(
            f"[TourismGDP] Calculated tourism GDP % for {len(self.tourism_gdp_data)} countries "
            f"(baseline: {self.target_year}, unmapped: {unmapped}, no GDP: {no_gdp})"
        )

    def get_tourism_gdp_pct(self, country_code: str) -> float:
        """
        Get tourism GDP percentage for a country.

        Args:
            country_code: ISO3 country code

        Returns:
            Tourism GDP percentage (0-100+), or 0.0 if not found
        """
        if country_code not in self.tourism_gdp_data:
            return 0.0
        return self.tourism_gdp_data[country_code]["tourism_gdp_pct"]

    def get_dependency_category(self, country_code: str) -> str:
        """
        Get tourism dependency category for a country.

        Args:
            country_code: ISO3 country code

        Returns:
            Category string: 'highly_dependent', 'moderately_dependent', 'low_dependency', or 'minimal_dependency'
        """
        if country_code not in self.tourism_gdp_data:
            return "minimal_dependency"
        return self.tourism_gdp_data[country_code]["dependency_category"]

    def get_tfi_decline_modifier(self, country_code: str) -> float:
        """
        Get TFI decline rate modifier for a country.

        Args:
            country_code: ISO3 country code

        Returns:
            Multiplier for base TFI decline rate (0.5 = 50% slower decline)
        """
        if country_code not in self.tourism_gdp_data:
            return 1.0
        return self.tourism_gdp_data[country_code]["tfi_decline_modifier"]

    def get_all_data(self, country_code: str) -> Optional[Dict]:
        """
        Get all tourism GDP data for a country.

        Args:
            country_code: ISO3 country code

        Returns:
            Dict with all tourism GDP data, or None if not found
        """
        return self.tourism_gdp_data.get(country_code)

    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics for tourism GDP data.

        Returns:
            Dict with summary statistics
        """
        if not self.tourism_gdp_data:
            return {}

        values = [d["tourism_gdp_pct"] for d in self.tourism_gdp_data.values()]
        categories = {}
        for d in self.tourism_gdp_data.values():
            cat = d["dependency_category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_countries": len(self.tourism_gdp_data),
            "target_year": self.target_year,
            "mean_tourism_gdp_pct": sum(values) / len(values),
            "median_tourism_gdp_pct": sorted(values)[len(values) // 2],
            "max_tourism_gdp_pct": max(values),
            "min_tourism_gdp_pct": min(values),
            "by_category": categories,
        }

    def get_countries_by_category(self, category: str) -> list:
        """
        Get list of country codes in a dependency category.

        Args:
            category: Category string

        Returns:
            List of country codes
        """
        return [
            code
            for code, data in self.tourism_gdp_data.items()
            if data["dependency_category"] == category
        ]
