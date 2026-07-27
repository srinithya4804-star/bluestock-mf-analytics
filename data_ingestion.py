"""
Bluestock Capstone Project I - Mutual Fund Analytics
Day 1 - Data Ingestion

Covers:
  Step 3 - Load all provided CSV datasets, print shape/dtypes/head, note anomalies
  Step 6 - Explore fund master (fund houses, categories, sub-categories, risk grades, AMFI codes)
  Step 7 - Validate AMFI codes across fund_master vs nav_history + data quality summary
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG - adjust these two to match your actual filenames in data/raw/
# ---------------------------------------------------------------------------
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
REPORTS_DIR = "reports"

FUND_MASTER_FILE = "01_fund_master.csv"
NAV_HISTORY_FILE = "02_nav_history.csv"

AMFI_CODE_COL = "amfi_code"            # <-- change to match the actual column name


def load_all_csvs(raw_dir: str) -> dict:
    """
    Step 3: Load every CSV in raw_dir, print shape/dtypes/head, flag anomalies.
    Returns a dict of {filename: dataframe}.
    """
    dataframes = {}
    csv_files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".csv"))

    if not csv_files:
        print(f"No CSV files found in {raw_dir}. Check the path / make sure files are copied in.")
        return dataframes

    print(f"Found {len(csv_files)} CSV file(s) in {raw_dir}\n")

    for filename in csv_files:
        path = os.path.join(raw_dir, filename)
        print("=" * 80)
        print(f"FILE: {filename}")
        print("=" * 80)

        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"  Could not read {filename}: {e}\n")
            continue

        dataframes[filename] = df

        print(f"Shape: {df.shape}")
        print("\nDtypes:")
        print(df.dtypes)
        print("\nHead:")
        print(df.head())

        # --- anomaly checks ---
        print("\nAnomaly checks:")
        null_counts = df.isnull().sum()
        nulls = null_counts[null_counts > 0]
        if not nulls.empty:
            print(f"  Null values found in columns:\n{nulls}")
        else:
            print("  No null values.")

        dup_count = df.duplicated().sum()
        if dup_count > 0:
            print(f"  {dup_count} duplicate row(s) found.")
        else:
            print("  No duplicate rows.")

        # flag columns that look numeric but were read as object (common CSV issue)
        for col in df.select_dtypes(include="object").columns:
            sample = df[col].dropna().astype(str).head(20)
            numeric_like = sample.str.replace(".", "", regex=False).str.replace("-", "", regex=False).str.isnumeric()
            if len(sample) > 0 and numeric_like.mean() > 0.8:
                print(f"  Column '{col}' looks numeric but is stored as object/text - may need cleaning.")

        print()

    return dataframes


def explore_fund_master(dataframes: dict):
    """
    Step 6: Explore fund master - unique fund houses, categories, sub-categories,
    risk grades, and AMFI scheme code structure.
    """
    if FUND_MASTER_FILE not in dataframes:
        print(f"'{FUND_MASTER_FILE}' not found among loaded files - skipping fund master exploration. "
              f"Update FUND_MASTER_FILE at the top of this script to match your actual filename.")
        return

    df = dataframes[FUND_MASTER_FILE]
    print("=" * 80)
    print("FUND MASTER EXPLORATION (Step 6)")
    print("=" * 80)

    for col in ["fund_house", "category", "sub_category", "risk_grade"]:
        if col in df.columns:
            uniques = df[col].dropna().unique()
            print(f"\nUnique {col} ({len(uniques)}):")
            print(sorted(uniques.tolist()))
        else:
            print(f"\nColumn '{col}' not found in fund master - check actual column names: {list(df.columns)}")

    if AMFI_CODE_COL in df.columns:
        codes = df[AMFI_CODE_COL].dropna()
        print(f"\nAMFI code column: '{AMFI_CODE_COL}'")
        print(f"  Total codes: {len(codes)}")
        print(f"  Unique codes: {codes.nunique()}")
        print(f"  Sample codes: {codes.head(10).tolist()}")
        print(f"  Dtype: {codes.dtype}")
        print("  Note: AMFI scheme codes are unique numeric identifiers assigned to each mutual fund "
              "scheme/plan (e.g. growth vs dividend, direct vs regular are separate codes).")
    else:
        print(f"\nColumn '{AMFI_CODE_COL}' not found in fund master - check actual column names: {list(df.columns)}")


def validate_amfi_codes(dataframes: dict):
    """
    Step 7: Confirm every AMFI code in fund_master exists in nav_history.
    Writes a short data quality summary to reports/day1_data_quality_summary.txt
    """
    if FUND_MASTER_FILE not in dataframes or NAV_HISTORY_FILE not in dataframes:
        print("\nCannot validate AMFI codes - fund_master or nav_history not loaded. "
              "Check FUND_MASTER_FILE / NAV_HISTORY_FILE at the top of this script.")
        return

    fund_master = dataframes[FUND_MASTER_FILE]
    nav_history = dataframes[NAV_HISTORY_FILE]

    if AMFI_CODE_COL not in fund_master.columns or AMFI_CODE_COL not in nav_history.columns:
        print(f"\nColumn '{AMFI_CODE_COL}' missing from one of the files - "
              f"fund_master columns: {list(fund_master.columns)}, "
              f"nav_history columns: {list(nav_history.columns)}")
        return

    master_codes = set(fund_master[AMFI_CODE_COL].dropna().unique())
    nav_codes = set(nav_history[AMFI_CODE_COL].dropna().unique())

    missing_in_nav = master_codes - nav_codes
    extra_in_nav = nav_codes - master_codes

    print("\n" + "=" * 80)
    print("AMFI CODE VALIDATION (Step 7)")
    print("=" * 80)
    print(f"Fund master unique codes: {len(master_codes)}")
    print(f"NAV history unique codes: {len(nav_codes)}")
    print(f"Codes in fund_master but missing from nav_history: {len(missing_in_nav)}")
    print(f"Codes in nav_history but not in fund_master: {len(extra_in_nav)}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    summary_path = os.path.join(REPORTS_DIR, "day1_data_quality_summary.txt")

    with open(summary_path, "w") as f:
        f.write("Day 1 Data Quality Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Fund master unique AMFI codes: {len(master_codes)}\n")
        f.write(f"NAV history unique AMFI codes: {len(nav_codes)}\n")
        f.write(f"Codes in fund_master missing from nav_history: {len(missing_in_nav)}\n")
        if missing_in_nav:
            f.write(f"  Missing codes: {sorted(missing_in_nav)}\n")
        f.write(f"Codes in nav_history not present in fund_master: {len(extra_in_nav)}\n")
        if extra_in_nav:
            f.write(f"  Extra codes: {sorted(extra_in_nav)}\n")
        f.write("\nOverall assessment: ")
        if not missing_in_nav:
            f.write("All fund_master AMFI codes have corresponding NAV history. Data is consistent.\n")
        else:
            f.write(f"{len(missing_in_nav)} scheme(s) in fund_master have no NAV history and "
                    f"will need follow-up (either fetch missing NAV data or exclude from analysis).\n")

    print(f"\nData quality summary written to {summary_path}")


def main():
    dataframes = load_all_csvs(RAW_DIR)
    explore_fund_master(dataframes)
    validate_amfi_codes(dataframes)


if __name__ == "__main__":
    main()