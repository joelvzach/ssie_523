"""
UN Tourism Data Extraction Script

Extracts data from UN Tourism bulk download ZIP file and creates clean CSV files.
"""

import pandas as pd
import zipfile
from pathlib import Path

# Paths
DATA_ROOT = Path(__file__).parent.parent / "data"
UN_TOURISM_ZIP = DATA_ROOT / "UN_Tourism/UN_Tourism_bulk_data_download_12_2025.zip"
OUTPUT_DIR = DATA_ROOT / "UN_Tourism/extracted"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapping of UN Tourism indicator codes to clean names
INDICATOR_MAPPING = {
    # Inbound arrivals
    "INBD_TRIP_TOTL_TOTL_TRST": "arrivals_total",
    "INBD_TRIP_TOTL_TOTL_OVRNGHT": "arrivals_overnight_visitors",
    "INBD_TRIP_TOTL_TOTL_SAME_DAY": "arrivals_same_day",
    "INBD_TRIP_TOTL_CRUS_EXCR": "arrivals_cruise_exursionists",
    # Inbound expenditure
    "INBD_EXP_TOTL": "expenditure_inbound_total",
    "INBD_EXP_TOTL_CURR_USD": "expenditure_inbound_usd",
    # Outbound departures
    "OUTBD_TRIP_TOTL": "departures_total",
    "OUTBD_TRIP_RESIDENT": "departures_residents",
    # Outbound expenditure
    "OUTBD_EXP_TOTL": "expenditure_outbound_total",
    "OUTBD_EXP_TOTL_CURR_USD": "expenditure_outbound_usd",
    # Domestic
    "DMST_TRIP_TOTL": "trips_domestic_total",
    "DMST_TRIP_OVRNGHT": "trips_domestic_overnight",
    # Macroeconomic
    "TD_GDP_SH": "tourism_gdp_share_direct",
    "TD_GDP": "tourism_gdp_direct",
    # Employment
    "TD_EMP_TOTL": "employment_tourism_total",
    "TD_EMP_SH": "employment_tourism_share",
}


def extract_un_tourism_data():
    """Extract all datasets from UN Tourism ZIP file."""

    if not UN_TOURISM_ZIP.exists():
        print(f"Error: ZIP file not found at {UN_TOURISM_ZIP}")
        return None

    print("=" * 60)
    print("UN TOURISM DATA EXTRACTION")
    print("=" * 60)

    z = zipfile.ZipFile(UN_TOURISM_ZIP)
    excel_files = [n for n in z.namelist() if n.endswith(".xlsx")]

    print(f"\nFound {len(excel_files)} Excel files in ZIP")

    extracted_datasets = {}

    for excel_file in excel_files:
        try:
            print(f"\nProcessing: {excel_file}")

            with z.open(excel_file) as f:
                xl = pd.ExcelFile(f)

                # Prefer 'Data' sheet, otherwise use first sheet
                sheet_name = "Data" if "Data" in xl.sheet_names else xl.sheet_names[0]
                df = xl.parse(sheet_name)

                # Clean the dataframe
                df_clean = clean_un_tourism_dataframe(df, excel_file)

                if df_clean is not None:
                    # Save to CSV
                    filename = excel_file.split("/")[-1].replace(".xlsx", ".csv")
                    filepath = OUTPUT_DIR / filename
                    df_clean.to_csv(filepath, index=False)

                    extracted_datasets[filename] = {
                        "records": len(df_clean),
                        "countries": df_clean["reporter_area_label"].nunique()
                        if "reporter_area_label" in df_clean.columns
                        else 0,
                        "years": f"{df_clean['year'].min()} - {df_clean['year'].max()}"
                        if "year" in df_clean.columns
                        else "N/A",
                    }

                    print(f"  ✓ Saved {len(df_clean):,} records to {filename}")

        except Exception as e:
            print(f"  ✗ Error processing {excel_file}: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    for filename, stats in extracted_datasets.items():
        print(f"\n{filename}")
        print(f"  Records: {stats['records']:,}")
        print(f"  Countries: {stats['countries']}")
        print(f"  Years: {stats['years']}")

    return extracted_datasets


def clean_un_tourism_dataframe(df, source_file):
    """Clean and standardize UN Tourism dataframe."""

    # Check if this is a data sheet (should have indicator_code, year, value columns)
    required_cols = ["indicator_code", "year", "value"]

    if not all(col in df.columns for col in required_cols):
        print(f"  Skipping - not a data sheet (missing required columns)")
        return None

    # Select relevant columns
    keep_cols = [
        "indicator_code",
        "indicator_label",
        "reporter_area_code",
        "reporter_area_label",
        "partner_area_code",
        "partner_area_label",
        "year",
        "value",
        "unit",
    ]

    available_cols = [col for col in keep_cols if col in df.columns]
    df_clean = df[available_cols].copy()

    # Map indicator codes to clean names
    if "indicator_code" in df_clean.columns:
        df_clean["indicator_name"] = df_clean["indicator_code"].map(INDICATOR_MAPPING)
        # For unmapped codes, use the label
        df_clean["indicator_name"] = df_clean["indicator_name"].fillna(
            df_clean["indicator_label"]
        )

    # Convert year to integer
    df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce").astype("Int64")

    # Convert value to numeric
    df_clean["value"] = pd.to_numeric(df_clean["value"], errors="coerce")

    # Remove rows with missing values
    df_clean = df_clean.dropna(subset=["year", "value"])

    # Remove duplicate rows
    df_clean = df_clean.drop_duplicates()

    return df_clean


if __name__ == "__main__":
    datasets = extract_un_tourism_data()

    if datasets:
        print(f"\n✓ Extraction complete!")
        print(f"  Output directory: {OUTPUT_DIR}")
    else:
        print("\n✗ Extraction failed or no data found")
