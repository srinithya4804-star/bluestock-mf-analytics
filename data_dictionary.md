# Data Dictionary — Bluestock Mutual Fund Analytics

This document describes every table in `bluestock_mf.db`, its columns, data types,
business meaning, and which source CSV it was derived from.

---

## dim_fund
**Source:** `01_fund_master.csv` (cleaned copy in `data/processed/`)
**Grain:** One row per mutual fund scheme.

| Column | Type | Business Definition |
|---|---|---|
| amfi_code | INTEGER (PK) | Unique AMFI scheme code identifying this fund/plan combination. |
| fund_house | TEXT | Asset management company (AMC) that manages the fund, e.g. HDFC, SBI. |
| scheme_name | TEXT | Full name of the mutual fund scheme. |
| category | TEXT | High-level fund category, e.g. Equity, Debt, Hybrid. |
| sub_category | TEXT | More specific classification within category, e.g. Large Cap, Mid Cap. |
| plan | TEXT | Plan type, e.g. Direct or Regular. |
| launch_date | TEXT (date) | Date the scheme was launched. |
| benchmark | TEXT | Market index the fund is benchmarked against. |
| expense_ratio_pct | REAL | Annual fee charged by the fund as a percentage of assets. |
| exit_load_pct | REAL | Penalty percentage charged for early withdrawal. |
| min_sip_amount | REAL | Minimum SIP (Systematic Investment Plan) contribution allowed. |
| min_lumpsum_amount | REAL | Minimum one-time lumpsum investment allowed. |
| fund_manager | TEXT | Name of the fund manager responsible for the scheme. |
| risk_category | TEXT | Risk classification, e.g. Low, Moderate, High. |
| sebi_category_code | TEXT | SEBI's official scheme category code. |

---

## dim_date
**Source:** Generated programmatically from all dates found in fact_nav, fact_transactions, and fact_aum.
**Grain:** One row per unique calendar date referenced anywhere in the fact tables.

| Column | Type | Business Definition |
|---|---|---|
| date_id | INTEGER (PK) | Date key in YYYYMMDD integer format, e.g. 20240105. |
| full_date | TEXT (date) | Full calendar date in YYYY-MM-DD format. |
| year | INTEGER | Calendar year. |
| month | INTEGER | Calendar month (1-12). |
| day | INTEGER | Day of month. |
| quarter | INTEGER | Calendar quarter (1-4). |
| month_name | TEXT | Full month name, e.g. January. |
| day_name | TEXT | Full day-of-week name, e.g. Monday. |
| is_weekend | INTEGER | 1 if Saturday/Sunday, else 0. |

---

## fact_nav
**Source:** `02_nav_history.csv` (cleaned: dates parsed, sorted, deduplicated, NAV validated >0,
calendar gaps forward-filled).
**Grain:** One row per fund per calendar day.

| Column | Type | Business Definition |
|---|---|---|
| nav_id | INTEGER (PK) | Auto-incrementing surrogate key. |
| amfi_code | INTEGER (FK -> dim_fund) | Fund this NAV value belongs to. |
| date_id | INTEGER (FK -> dim_date) | Date this NAV value applies to. |
| nav | REAL | Net Asset Value per unit on this date. Forward-filled on weekends/holidays from the last available trading-day NAV. |

---

## fact_transactions
**Source:** `08_investor_transactions.csv` (cleaned: transaction_type standardised to
SIP/Lumpsum/Redemption, amount validated >0, dates parsed, KYC status checked against expected values).
**Grain:** One row per individual investor transaction.

| Column | Type | Business Definition |
|---|---|---|
| transaction_id | INTEGER (PK) | Auto-incrementing surrogate key. |
| amfi_code | INTEGER (FK -> dim_fund) | Fund the transaction was made in. |
| date_id | INTEGER (FK -> dim_date) | Date the transaction occurred. |
| transaction_type | TEXT | Standardised as SIP, Lumpsum, or Redemption. |
| amount | REAL | Transaction amount in INR. Always > 0. |
| kyc_status | TEXT | Investor's KYC verification status, e.g. Verified, Pending, Rejected. |
| state | TEXT | Indian state the investor is located in. |
| investor_id | TEXT | Unique identifier for the investor. |

---

## fact_performance
**Source:** `07_scheme_performance.csv` (cleaned: return columns validated as numeric,
anomalies flagged, expense_ratio checked against 0.1%-2.5% expected range).
**Grain:** One row per fund (latest reported performance snapshot).

| Column | Type | Business Definition |
|---|---|---|
| performance_id | INTEGER (PK) | Auto-incrementing surrogate key. |
| amfi_code | INTEGER (FK -> dim_fund) | Fund this performance record belongs to. |
| return_1yr | REAL | Trailing 1-year return, percentage. |
| return_3yr | REAL | Trailing 3-year annualised return, percentage. |
| return_5yr | REAL | Trailing 5-year annualised return, percentage. |
| expense_ratio_pct | REAL | Expense ratio at time of this performance snapshot. |

---

## fact_aum
**Source:** `03_aum_by_fund_house.csv` (cleaned: generic pass — deduplicated, dates parsed).
**Grain:** One row per fund house per reporting date.

| Column | Type | Business Definition |
|---|---|---|
| aum_id | INTEGER (PK) | Auto-incrementing surrogate key. |
| fund_house | TEXT | Asset management company. Not a foreign key to dim_fund since AUM is reported at the fund-house level, not per individual scheme. |
| date_id | INTEGER (FK -> dim_date) | Reporting date for this AUM figure. |
| aum_value | REAL | Assets Under Management, in the currency/unit used by the source file (confirm INR crore/lakh convention with source). |

---

## Notes on remaining source files

The following raw datasets were cleaned generically (deduplicated, whitespace-trimmed,
date columns parsed) and saved to `data/processed/`, but were not loaded into the star
schema above since they weren't part of the defined fact/dimension tables for Day 2:

- `04_monthly_sip_inflows.csv`
- `05_category_inflows.csv`
- `06_industry_folio_count.csv`
- `09_portfolio_holdings.csv`
- `10_benchmark_indices.csv`

These remain available as cleaned CSVs for future analysis or additional schema
extensions in later project phases.

---

## Known follow-ups

Some column names in `fact_transactions`, `fact_performance`, and `fact_aum` were
configured based on assumed naming conventions and confirmed against the actual
source files during setup. If any mismatches were found, `load_to_sqlite.py` prints
a note listing missing/unmapped columns — update the corresponding config variables
at the top of the script and re-run if that occurred.
