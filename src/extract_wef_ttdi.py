"""
Extract WEF Travel & Tourism Development Index (TTDI) data from PDF

This script extracts country-level TTDI scores and sub-index scores from:
- WEF_Travel_and_Tourism_Development_Index_2024.pdf
- WEF_Travel_Tourism_Development_2021.pdf (backup/comparison)

Output: CSV files with country scores for simulation calibration
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import re

# Setup paths
PDF_DIR = Path(__file__).parent.parent / "data" / "WEF"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "WEF"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_2024 = PDF_DIR / "WEF_Travel_and_Tourism_Development_Index_2024.pdf"
PDF_2021 = PDF_DIR / "WEF_Travel_Tourism_Development_2021.pdf"

print("=" * 80)
print("WEF TTDI DATA EXTRACTION")
print("=" * 80)


def extract_tables_from_pdf(pdf_path, max_pages=None):
    """Extract all tables from a PDF file"""
    print(f"\nProcessing: {pdf_path.name}")

    if not pdf_path.exists():
        print(f"  ✗ File not found: {pdf_path}")
        return []

    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        pages_to_process = (
            range(total_pages)
            if max_pages is None
            else range(min(max_pages, total_pages))
        )

        print(f"  Total pages: {total_pages}")
        print(
            f"  Processing pages: {min(max_pages, total_pages) if max_pages else total_pages}"
        )

        for page_num in pages_to_process:
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if tables:
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 2:  # Skip tiny tables
                        all_tables.append(
                            {
                                "page": page_num + 1,
                                "table_idx": table_idx,
                                "data": table,
                                "rows": len(table),
                                "cols": max(len(row) for row in table) if table else 0,
                            }
                        )

            # Progress indicator every 10 pages
            if (page_num + 1) % 10 == 0:
                print(f"    Processed page {page_num + 1}/{total_pages}")

    print(f"  ✓ Found {len(all_tables)} tables")
    return all_tables


def identify_ttdi_tables(tables):
    """Identify tables containing TTDI scores"""
    print("\n" + "=" * 80)
    print("IDENTIFYING TTDI TABLES")
    print("=" * 80)

    ttdi_tables = []

    for table in tables:
        # Check if table contains TTDI-related keywords
        table_text = str(table["data"]).lower()

        keywords = [
            "ttdi",
            "travel.*tourism.*development",
            "index.*score",
            "rank.*country",
            "overall.*score",
            "sub-index",
        ]

        matches = sum(1 for keyword in keywords if re.search(keyword, table_text))

        if matches >= 2:  # At least 2 keyword matches
            ttdi_tables.append(table)
            print(f"\n  Potential TTDI table found:")
            print(f"    Page: {table['page']}, Table: {table['table_idx']}")
            print(f"    Dimensions: {table['rows']} rows × {table['cols']} cols")

            # Show first few rows as sample
            print(f"    Sample (first 3 rows):")
            for i, row in enumerate(table["data"][:3]):
                if row:
                    print(
                        f"      Row {i}: {[str(cell)[:40] if cell else 'None' for cell in row]}"
                    )

    return ttdi_tables


def extract_country_scores(table_data):
    """Extract country scores from a table"""
    print("\n" + "=" * 80)
    print("EXTRACTING COUNTRY SCORES")
    print("=" * 80)

    countries = []

    for row_idx, row in enumerate(table_data["data"]):
        if not row:
            continue

        # Clean row data
        cleaned_row = [str(cell).strip() if cell else "" for cell in row]

        # Try to identify country rows (skip headers)
        # Look for rows with country names and numeric scores
        if row_idx < 2:  # Skip first 2 rows (likely headers)
            continue

        # Check if row has numeric score (TTDI score is typically 0-100)
        has_score = False
        score_value = None

        for cell in cleaned_row[1:]:  # Skip first column (likely rank)
            try:
                # Try to parse as float
                value = float(cell.replace(",", "").replace(" ", ""))
                if 0 <= value <= 100:  # TTDI scores are 0-100
                    has_score = True
                    score_value = value
                    break
            except (ValueError, AttributeError):
                continue

        if has_score and cleaned_row[0]:
            countries.append(
                {"row_idx": row_idx, "raw_data": cleaned_row, "score": score_value}
            )

    print(f"  Extracted {len(countries)} potential country records")

    if len(countries) > 0 and len(countries) <= 200:
        print(f"  ✓ Likely valid country list (n={len(countries)})")
        return countries

    return []


def create_ttdi_dataframe(country_records):
    """Create structured DataFrame from extracted records"""
    print("\n" + "=" * 80)
    print("CREATING STRUCTURED DATAFRAME")
    print("=" * 80)

    if not country_records:
        print("  ✗ No country records to process")
        return None

    # Build DataFrame
    data = []

    for record in country_records:
        row = record["raw_data"]

        # Parse row - typical format: [Rank, Country, Score, Sub-index 1, Sub-index 2, ...]
        try:
            rank = (
                int(row[0].replace(".", ""))
                if row[0].isdigit() or (row[0].replace(".", "").isdigit())
                else None
            )
        except (ValueError, IndexError):
            rank = None

        country = row[1] if len(row) > 1 else None

        # Extract all numeric scores
        scores = []
        for cell in row[2:]:
            try:
                value = float(cell.replace(",", "").replace(" ", ""))
                scores.append(value)
            except (ValueError, AttributeError):
                scores.append(None)

        data.append(
            {
                "rank": rank,
                "country": country,
                "ttdi_score": scores[0] if len(scores) > 0 else None,
                "sub_index_1": scores[1] if len(scores) > 1 else None,
                "sub_index_2": scores[2] if len(scores) > 2 else None,
                "sub_index_3": scores[3] if len(scores) > 3 else None,
                "raw_scores": scores,
            }
        )

    df = pd.DataFrame(data)

    # Remove rows without valid country names
    df = df[df["country"].notna() & (df["country"] != "")]
    df = df[df["country"].str.len() > 2]  # Filter out short codes

    print(f"  Final DataFrame: {len(df)} countries")
    print(f"  Columns: {df.columns.tolist()}")

    return df


def save_ttdi_data(df, year, output_path):
    """Save extracted TTDI data to CSV"""
    print("\n" + "=" * 80)
    print("SAVING EXTRACTED DATA")
    print("=" * 80)

    if df is None or len(df) == 0:
        print(f"  ✗ No data to save for {year}")
        return None

    # Save full dataset
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved: {output_path}")

    # Show summary statistics
    print(f"\n  Summary for {year}:")
    print(f"    Countries: {len(df)}")
    print(
        f"    TTDI Score Range: {df['ttdi_score'].min():.1f} - {df['ttdi_score'].max():.1f}"
    )
    print(f"    Mean TTDI Score: {df['ttdi_score'].mean():.1f}")
    print(f"    Median TTDI Score: {df['ttdi_score'].median():.1f}")

    # Show top 10 countries
    print(f"\n  Top 10 Countries ({year}):")
    top_10 = df.nlargest(10, "ttdi_score")[["rank", "country", "ttdi_score"]]
    for _, row in top_10.iterrows():
        print(
            f"    #{int(row['rank']) if row['rank'] else '?':2d}. {row['country']:25s} {row['ttdi_score']:.1f}"
        )

    return df


# ============================================================================
# MAIN EXTRACTION PROCESS
# ============================================================================

print("\n" + "=" * 80)
print("STEP 1: EXTRACT TABLES FROM 2024 PDF")
print("=" * 80)

tables_2024 = extract_tables_from_pdf(PDF_2024, max_pages=50)

print("\n" + "=" * 80)
print("STEP 2: IDENTIFY TTDI TABLES (2024)")
print("=" * 80)

ttdi_tables_2024 = identify_ttdi_tables(tables_2024)

if ttdi_tables_2024:
    # Process the largest/most complete table
    best_table = max(ttdi_tables_2024, key=lambda x: x["rows"])

    print("\n" + "=" * 80)
    print("STEP 3: EXTRACT COUNTRY SCORES (2024)")
    print("=" * 80)

    country_records_2024 = extract_country_scores(best_table)

    print("\n" + "=" * 80)
    print("STEP 4: CREATE DATAFRAME (2024)")
    print("=" * 80)

    df_2024 = create_ttdi_dataframe(country_records_2024)

    if df_2024 is not None:
        output_2024 = OUTPUT_DIR / "ttdi_scores_2024.csv"
        save_ttdi_data(df_2024, 2024, output_2024)

# ============================================================================
# OPTIONAL: PROCESS 2021 PDF FOR COMPARISON
# ============================================================================

print("\n\n" + "=" * 80)
print("BONUS: EXTRACT 2021 DATA FOR COMPARISON")
print("=" * 80)

response = input("\nExtract 2021 data as well? (y/n): ").strip().lower()

if response == "y" and PDF_2021.exists():
    tables_2021 = extract_tables_from_pdf(PDF_2021, max_pages=50)
    ttdi_tables_2021 = identify_ttdi_tables(tables_2021)

    if ttdi_tables_2021:
        best_table_2021 = max(ttdi_tables_2021, key=lambda x: x["rows"])
        country_records_2021 = extract_country_scores(best_table_2021)
        df_2021 = create_ttdi_dataframe(country_records_2021)

        if df_2021 is not None:
            output_2021 = OUTPUT_DIR / "ttdi_scores_2021.csv"
            save_ttdi_data(df_2021, 2021, output_2021)
else:
    print("  Skipping 2021 extraction")

print("\n" + "=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
