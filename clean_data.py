"""
Bluestock Capstone Project I - Mutual Fund Analytics
Day 2 - Data Cleaning

Covers:
  Step 1 - Clean nav_history.csv
  Step 2 - Clean investor_transactions.csv
  Step 3 - Clean scheme_performance.csv
  (plus light generic cleaning for the remaining 7 CSVs so all 10 land in data/processed/)

Reads from data/raw/, writes cleaned versions to data/processed/.
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

# ---------------------------------------------------------------------------
# CONFIG - filenames confirmed from Day 1
# ---------------------------------------------------------------------------
FUND_MASTER_FILE = "01_fund_master.csv"
NAV_HISTORY_FILE = "02_nav_history.csv"
AUM_BY_FUND_HOUSE_FILE = "03_aum_by_fund_house.csv"
MONTHLY_SIP_INFLOWS_FILE = "04_monthly_sip_inflows.csv"
CATEGORY_INFLOWS_FILE = "05_category_inflows.csv"
INDUSTRY_FOLIO_COUNT_FILE = "06_industry_folio_count.csv"
SCHEME_PERFORMANCE_FILE = "07_scheme_performance.csv"
INVESTOR_TRANSACTIONS_FILE = "08_investor_transactions.csv"
PORTFOLIO_HOLDINGS_FILE = "09_portfolio_holdings.csv"
BENCHMARK_INDICES_FILE = "10_benchmark_indices.csv"

AMFI_CODE_COL = "amfi_code"

# --- Columns confirmed from investor_transactions.csv ---
TXN_TYPE_COL = "transaction_type"
TXN_AMOUNT_COL = "amount_inr"
TXN_DATE_COL = "transaction_date"
KYC_STATUS_COL = "kyc_status"

# --- Columns confirmed from scheme_performance.csv ---
EXPENSE_RATIO_COL = "expense_ratio_pct"
RETURN_COLS = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]

# Expected KYC enum values - adjust to match what your data actually uses
EXPECTED_KYC_VALUES = {"Verified", "Pending", "Rejected"}

# Standardisation map for transaction_type - lowercased key -> clean label
TXN_TYPE_MAP = {
    "sip": "SIP",
    "systematic investment plan": "SIP",
    "lumpsum": "Lumpsum",
    "lump sum": "Lumpsum",
    "one time": "Lumpsum",
    "redemption": "Redemption",
    "redeem": "Redemption",
    "withdrawal": "Redemption",
}


def load_raw(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    return pd.read_csv(path)


def save_processed(df: pd.DataFrame, filename: str):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    out_path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df)} rows -> {out_path}")


# ---------------------------------------------------------------------------
# Step 1: Clean nav_history.csv
# ---------------------------------------------------------------------------
def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    print("\nCleaning nav_history.csv ...")
    original_len = len(df)

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        print(f"  Dropping {bad_dates} row(s) with unparseable dates.")
        df = df.dropna(subset=["date"])

    # Sort by amfi_code + date
    df = df.sort_values([AMFI_CODE_COL, "date"]).reset_index(drop=True)

    # Remove exact duplicates (same fund + date)
    dup_count = df.duplicated(subset=[AMFI_CODE_COL, "date"]).sum()
    if dup_count:
        print(f"  Removing {dup_count} duplicate (amfi_code, date) row(s).")
        df = df.drop_duplicates(subset=[AMFI_CODE_COL, "date"], keep="last")

    # Validate NAV > 0
    invalid_nav = (df["nav"] <= 0) | df["nav"].isna()
    if invalid_nav.sum():
        print(f"  Dropping {invalid_nav.sum()} row(s) with NAV <= 0 or missing NAV.")
        df = df[~invalid_nav]

    # Forward-fill missing NAV for holidays/weekends:
    # reindex each fund to a continuous daily calendar between its min and max date,
    # then forward-fill NAV so every calendar day has a value.
    filled_groups = []
    for code, group in df.groupby(AMFI_CODE_COL):
        group = group.set_index("date").sort_index()
        full_range = pd.date_range(group.index.min(), group.index.max(), freq="D")
        group = group.reindex(full_range)
        group[AMFI_CODE_COL] = code
        group["nav"] = group["nav"].ffill()
        group = group.reset_index().rename(columns={"index": "date"})
        filled_groups.append(group)

    df = pd.concat(filled_groups, ignore_index=True)
    df = df[["date", AMFI_CODE_COL, "nav"]]

    print(f"  Rows before: {original_len}, rows after cleaning + calendar fill: {len(df)}")
    return df


# ---------------------------------------------------------------------------
# Step 2: Clean investor_transactions.csv
# ---------------------------------------------------------------------------
def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    print("\nCleaning investor_transactions.csv ...")

    if TXN_TYPE_COL not in df.columns:
        print(f"  Column '{TXN_TYPE_COL}' not found - available columns: {list(df.columns)}")
        print("  Update TXN_TYPE_COL at top of script and re-run.")
        return df

    # Standardise transaction_type
    df[TXN_TYPE_COL] = (
        df[TXN_TYPE_COL]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(TXN_TYPE_MAP)
        .fillna(df[TXN_TYPE_COL])  # keep original if no mapping matched
    )
    unmapped = set(df[TXN_TYPE_COL].unique()) - set(TXN_TYPE_MAP.values())
    if unmapped:
        print(f"  Warning: transaction_type values not in standard set {{'SIP','Lumpsum','Redemption'}}: {unmapped}")
        print("  Add these to TXN_TYPE_MAP at the top of the script if they should be standardised.")

    # Validate amount > 0
    if TXN_AMOUNT_COL in df.columns:
        invalid_amt = (df[TXN_AMOUNT_COL] <= 0) | df[TXN_AMOUNT_COL].isna()
        if invalid_amt.sum():
            print(f"  Dropping {invalid_amt.sum()} row(s) with {TXN_AMOUNT_COL} <= 0 or missing.")
            df = df[~invalid_amt]
    else:
        print(f"  Column '{TXN_AMOUNT_COL}' not found - available columns: {list(df.columns)}")

    # Fix date formats
    if TXN_DATE_COL in df.columns:
        df[TXN_DATE_COL] = pd.to_datetime(df[TXN_DATE_COL], errors="coerce")
        bad_dates = df[TXN_DATE_COL].isna().sum()
        if bad_dates:
            print(f"  Dropping {bad_dates} row(s) with unparseable {TXN_DATE_COL}.")
            df = df.dropna(subset=[TXN_DATE_COL])
    else:
        print(f"  Column '{TXN_DATE_COL}' not found - available columns: {list(df.columns)}")

    # Check KYC status enum values
    if KYC_STATUS_COL in df.columns:
        actual_values = set(df[KYC_STATUS_COL].dropna().unique())
        unexpected = actual_values - EXPECTED_KYC_VALUES
        print(f"  KYC status values found: {actual_values}")
        if unexpected:
            print(f"  Unexpected KYC values not in {EXPECTED_KYC_VALUES}: {unexpected}")
    else:
        print(f"  Column '{KYC_STATUS_COL}' not found - available columns: {list(df.columns)}")

    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Step 3: Clean scheme_performance.csv
# ---------------------------------------------------------------------------
def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    print("\nCleaning scheme_performance.csv ...")

    # Validate return columns are numeric, flag anomalies
    for col in RETURN_COLS:
        if col not in df.columns:
            print(f"  Column '{col}' not found - available columns: {list(df.columns)}")
            continue
        before_non_numeric = df[col].apply(lambda x: not str(x).replace(".", "", 1).replace("-", "", 1).isdigit()
                                            if pd.notna(x) else False).sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if before_non_numeric:
            print(f"  '{col}': {before_non_numeric} non-numeric value(s) coerced to NaN.")

        # Flag anomalies: returns below -100% or above 100% (>100% annual return is rare/suspicious)
        anomalies = df[(df[col] < -100) | (df[col] > 100)]
        if len(anomalies):
            print(f"  '{col}': {len(anomalies)} anomalous value(s) outside [-100, 100] range - flagged, not removed.")
            print(f"    Affected AMFI codes: {anomalies[AMFI_CODE_COL].tolist() if AMFI_CODE_COL in df.columns else 'n/a'}")

    # Check expense_ratio range 0.1% - 2.5%
    if EXPENSE_RATIO_COL in df.columns:
        df[EXPENSE_RATIO_COL] = pd.to_numeric(df[EXPENSE_RATIO_COL], errors="coerce")
        out_of_range = df[(df[EXPENSE_RATIO_COL] < 0.1) | (df[EXPENSE_RATIO_COL] > 2.5)]
        if len(out_of_range):
            print(f"  {len(out_of_range)} row(s) with expense_ratio outside 0.1%-2.5% range - flagged, not removed.")
            print(f"    Affected AMFI codes: {out_of_range[AMFI_CODE_COL].tolist() if AMFI_CODE_COL in df.columns else 'n/a'}")
    else:
        print(f"  Column '{EXPENSE_RATIO_COL}' not found - available columns: {list(df.columns)}")

    return df


# ---------------------------------------------------------------------------
# Generic cleaning for the remaining files (light touch: dedup, trim, parse dates)
# ---------------------------------------------------------------------------
def generic_clean(df: pd.DataFrame, label: str) -> pd.DataFrame:
    print(f"\nCleaning {label} (generic pass) ...")
    original_len = len(df)

    # Strip whitespace on text columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Parse any column with "date" in its name
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Drop exact duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count:
        print(f"  Removing {dup_count} duplicate row(s).")
        df = df.drop_duplicates()

    print(f"  Rows before: {original_len}, rows after: {len(df)}")
    return df.reset_index(drop=True)


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Step 1
    nav_history = load_raw(NAV_HISTORY_FILE)
    nav_history_clean = clean_nav_history(nav_history)
    save_processed(nav_history_clean, NAV_HISTORY_FILE)

    # Step 2
    investor_transactions = load_raw(INVESTOR_TRANSACTIONS_FILE)
    investor_transactions_clean = clean_investor_transactions(investor_transactions)
    save_processed(investor_transactions_clean, INVESTOR_TRANSACTIONS_FILE)

    # Step 3
    scheme_performance = load_raw(SCHEME_PERFORMANCE_FILE)
    scheme_performance_clean = clean_scheme_performance(scheme_performance)
    save_processed(scheme_performance_clean, SCHEME_PERFORMANCE_FILE)

    # Generic cleaning for the remaining 7 files
    remaining_files = [
        FUND_MASTER_FILE,
        AUM_BY_FUND_HOUSE_FILE,
        MONTHLY_SIP_INFLOWS_FILE,
        CATEGORY_INFLOWS_FILE,
        INDUSTRY_FOLIO_COUNT_FILE,
        PORTFOLIO_HOLDINGS_FILE,
        BENCHMARK_INDICES_FILE,
    ]
    for filename in remaining_files:
        df = load_raw(filename)
        df_clean = generic_clean(df, filename)
        save_processed(df_clean, filename)

    print("\nAll 10 datasets cleaned and saved to data/processed/.")


if __name__ == "__main__":
    main()