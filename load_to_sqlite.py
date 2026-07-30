"""
Bluestock Capstone Project I - Mutual Fund Analytics
Day 2 - Load cleaned datasets into SQLite (bluestock_mf.db)

Step 4 - runs schema.sql to create the star schema tables
Step 5 - loads cleaned CSVs into those tables via SQLAlchemy, verifies row counts
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

PROCESSED_DIR = "data/processed"
DB_PATH = "bluestock_mf.db"
SCHEMA_PATH = "schema.sql"

FUND_MASTER_FILE = "01_fund_master.csv"
NAV_HISTORY_FILE = "02_nav_history.csv"
AUM_BY_FUND_HOUSE_FILE = "03_aum_by_fund_house.csv"
SCHEME_PERFORMANCE_FILE = "07_scheme_performance.csv"
INVESTOR_TRANSACTIONS_FILE = "08_investor_transactions.csv"

AMFI_CODE_COL = "amfi_code"

# Column names confirmed from aum_by_fund_house.csv
AUM_FUND_HOUSE_COL = "fund_house"
AUM_DATE_COL = "date"
AUM_VALUE_COL = "aum_crore"

# Column names confirmed from investor_transactions.csv
TXN_TYPE_COL = "transaction_type"
TXN_AMOUNT_COL = "amount_inr"
TXN_DATE_COL = "transaction_date"
KYC_STATUS_COL = "kyc_status"
STATE_COL = "state"
INVESTOR_ID_COL = "investor_id"

# Column names confirmed from scheme_performance.csv (source names -> schema names)
RETURN_COLS = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]
RETURN_COLS_SCHEMA = ["return_1yr", "return_3yr", "return_5yr"]
EXPENSE_RATIO_COL = "expense_ratio_pct"


def make_date_id(date_series: pd.Series) -> pd.Series:
    """Convert a datetime series to YYYYMMDD integer date_id."""
    return date_series.dt.strftime("%Y%m%d").astype(int)


def build_dim_date(all_dates: pd.Series) -> pd.DataFrame:
    """Build dim_date rows from a series of unique dates."""
    dates = pd.to_datetime(all_dates.dropna().unique())
    dim = pd.DataFrame({"full_date": dates})
    dim["date_id"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["full_date"].dt.year
    dim["month"] = dim["full_date"].dt.month
    dim["day"] = dim["full_date"].dt.day
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["month_name"] = dim["full_date"].dt.month_name()
    dim["day_name"] = dim["full_date"].dt.day_name()
    dim["is_weekend"] = dim["full_date"].dt.dayofweek.isin([5, 6]).astype(int)
    dim["full_date"] = dim["full_date"].dt.strftime("%Y-%m-%d")
    dim = dim[["date_id", "full_date", "year", "month", "day", "quarter",
               "month_name", "day_name", "is_weekend"]]
    return dim.drop_duplicates(subset="date_id").reset_index(drop=True)


def verify_count(engine, table_name: str, expected_len: int):
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    status = "OK" if result == expected_len else "MISMATCH"
    print(f"  {table_name}: source rows = {expected_len}, table rows = {result}  [{status}]")


def main():
    # Remove any existing DB so this script can be re-run cleanly
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # --- Step 4: create schema from schema.sql ---
    print("Creating star schema from schema.sql ...")
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    with engine.begin() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print("Schema created.\n")

    # --- Load cleaned CSVs ---
    fund_master = pd.read_csv(os.path.join(PROCESSED_DIR, FUND_MASTER_FILE))
    nav_history = pd.read_csv(os.path.join(PROCESSED_DIR, NAV_HISTORY_FILE), parse_dates=["date"])
    aum = pd.read_csv(os.path.join(PROCESSED_DIR, AUM_BY_FUND_HOUSE_FILE))
    performance = pd.read_csv(os.path.join(PROCESSED_DIR, SCHEME_PERFORMANCE_FILE))
    transactions = pd.read_csv(os.path.join(PROCESSED_DIR, INVESTOR_TRANSACTIONS_FILE))

    # --- Build dim_date from every date across nav_history, transactions, aum ---
    date_pool = [nav_history["date"]]
    if AUM_DATE_COL in aum.columns:
        aum[AUM_DATE_COL] = pd.to_datetime(aum[AUM_DATE_COL], errors="coerce")
        date_pool.append(aum[AUM_DATE_COL])
    if TXN_DATE_COL in transactions.columns:
        transactions[TXN_DATE_COL] = pd.to_datetime(transactions[TXN_DATE_COL], errors="coerce")
        date_pool.append(transactions[TXN_DATE_COL])

    all_dates = pd.concat(date_pool, ignore_index=True)
    dim_date = build_dim_date(all_dates)

    # --- Prepare dim_fund ---
    dim_fund = fund_master.copy()

    # --- Prepare fact_nav ---
    fact_nav = nav_history.copy()
    fact_nav["date_id"] = make_date_id(fact_nav["date"])
    fact_nav = fact_nav[[AMFI_CODE_COL, "date_id", "nav"]]

    # --- Prepare fact_transactions ---
    fact_transactions = transactions.copy()
    if TXN_DATE_COL in fact_transactions.columns:
        fact_transactions["date_id"] = make_date_id(fact_transactions[TXN_DATE_COL])
    cols = [AMFI_CODE_COL, "date_id", TXN_TYPE_COL, TXN_AMOUNT_COL, KYC_STATUS_COL, STATE_COL, INVESTOR_ID_COL]
    available_cols = [c for c in cols if c in fact_transactions.columns]
    missing_cols = [c for c in cols if c not in fact_transactions.columns]
    if missing_cols:
        print(f"Note: fact_transactions missing expected columns {missing_cols} - "
              f"check investor_transactions.csv columns and update load_to_sqlite.py if needed.")
    fact_transactions = fact_transactions[available_cols].rename(columns={
        TXN_TYPE_COL: "transaction_type",
        TXN_AMOUNT_COL: "amount",
        KYC_STATUS_COL: "kyc_status",
        STATE_COL: "state",
        INVESTOR_ID_COL: "investor_id",
    })

    # --- Prepare fact_performance ---
    fact_performance = performance.copy()
    perf_cols = [AMFI_CODE_COL] + RETURN_COLS + [EXPENSE_RATIO_COL]
    available_perf_cols = [c for c in perf_cols if c in fact_performance.columns]
    missing_perf_cols = [c for c in perf_cols if c not in fact_performance.columns]
    if missing_perf_cols:
        print(f"Note: fact_performance missing expected columns {missing_perf_cols} - "
              f"check scheme_performance.csv columns and update load_to_sqlite.py if needed.")
    fact_performance = fact_performance[available_perf_cols]
    fact_performance = fact_performance.rename(columns=dict(zip(RETURN_COLS, RETURN_COLS_SCHEMA)))

    # --- Prepare fact_aum ---
    fact_aum = aum.copy()
    if AUM_DATE_COL in fact_aum.columns:
        fact_aum["date_id"] = make_date_id(fact_aum[AUM_DATE_COL])
    aum_cols = [AUM_FUND_HOUSE_COL, "date_id", AUM_VALUE_COL]
    available_aum_cols = [c for c in aum_cols if c in fact_aum.columns]
    missing_aum_cols = [c for c in aum_cols if c not in fact_aum.columns]
    if missing_aum_cols:
        print(f"Note: fact_aum missing expected columns {missing_aum_cols} - "
              f"check aum_by_fund_house.csv columns and update load_to_sqlite.py if needed.")
    fact_aum = fact_aum[available_aum_cols].rename(columns={
        AUM_FUND_HOUSE_COL: "fund_house",
        AUM_VALUE_COL: "aum_value",
    })

    # --- Load everything into SQLite ---
    print("\nLoading tables into SQLite ...")
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    dim_fund.to_sql("dim_fund", engine, if_exists="append", index=False)
    fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False)
    fact_performance.to_sql("fact_performance", engine, if_exists="append", index=False)
    fact_aum.to_sql("fact_aum", engine, if_exists="append", index=False)

    print("\nVerifying row counts (source dataframe vs SQLite table) ...")
    verify_count(engine, "dim_date", len(dim_date))
    verify_count(engine, "dim_fund", len(dim_fund))
    verify_count(engine, "fact_nav", len(fact_nav))
    verify_count(engine, "fact_transactions", len(fact_transactions))
    verify_count(engine, "fact_performance", len(fact_performance))
    verify_count(engine, "fact_aum", len(fact_aum))

    print(f"\nDone. Database saved to {DB_PATH}")


if __name__ == "__main__":
    main()