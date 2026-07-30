-- Bluestock Capstone Project I - Mutual Fund Analytics
-- Day 2 - Star Schema for bluestock_mf.db
--
-- dim_fund and dim_date are dimension tables.
-- fact_nav, fact_transactions, fact_performance, fact_aum are fact tables.

-- ---------------------------------------------------------------------------
-- DIMENSION: dim_fund
-- One row per mutual fund scheme (from fund_master.csv)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT,
    scheme_name         TEXT,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ---------------------------------------------------------------------------
-- DIMENSION: dim_date
-- One row per calendar date referenced anywhere in the fact tables.
-- date_id uses YYYYMMDD integer format (e.g. 2024-01-05 -> 20240105).
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_id      INTEGER PRIMARY KEY,
    full_date    TEXT NOT NULL,
    year         INTEGER,
    month        INTEGER,
    day          INTEGER,
    quarter      INTEGER,
    month_name   TEXT,
    day_name     TEXT,
    is_weekend   INTEGER
);

-- ---------------------------------------------------------------------------
-- FACT: fact_nav
-- Daily NAV per scheme (from nav_history.csv, cleaned).
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    nav_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER NOT NULL,
    date_id     INTEGER NOT NULL,
    nav         REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_transactions
-- Investor-level transactions (from investor_transactions.csv, cleaned).
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    transaction_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code         INTEGER,
    date_id           INTEGER,
    transaction_type  TEXT,
    amount            REAL,
    kyc_status        TEXT,
    state             TEXT,
    investor_id       TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_performance
-- Return metrics per scheme (from scheme_performance.csv, cleaned).
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    performance_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code          INTEGER,
    return_1yr         REAL,
    return_3yr         REAL,
    return_5yr         REAL,
    expense_ratio_pct  REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- ---------------------------------------------------------------------------
-- FACT: fact_aum
-- AUM by fund house over time (from aum_by_fund_house.csv, cleaned).
-- fund_house is plain text here (not FK) since AUM is reported at the
-- fund-house level, not per individual scheme.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    aum_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house  TEXT,
    date_id     INTEGER,
    aum_value   REAL,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);
