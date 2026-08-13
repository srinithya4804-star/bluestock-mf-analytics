Bluestock Mutual Fund Analytics

Capstone Project I — an end-to-end mutual fund analytics pipeline built for Bluestock Fintech, covering data ingestion, cleaning, database design, exploratory analysis, fund performance analytics, advanced risk metrics, and an interactive Power BI dashboard.

Team: Srinithya, Dhineshkumar, Aishwarya Ren

Project Overview

This project analyses 40 mutual fund schemes across 10 fund houses (2022-2026), covering:

NAV history, AUM, SIP inflows, category inflows, folio counts
Investor transactions (~32,800 records), portfolio holdings, benchmark indices
Live NAV data fetched from the mfapi.in public API

The pipeline produces a cleaned SQLite database, three analysis notebooks, a fund recommender tool, and a 4-page interactive Power BI dashboard.

Project Structure
bluestock-mf-analytics/
├── data/
│   ├── raw/                     # 10 provided CSVs + live-fetched NAV data
│   └── processed/                # Cleaned versions of all 10 datasets
├── notebooks/
├── sql/
├── dashboard/
├── reports/
│   ├── eda_charts/                # EDA_Analysis.ipynb chart exports
│   ├── performance_charts/        # Performance_Analytics.ipynb chart exports
│   └── advanced_charts/           # Advanced_Analytics.ipynb chart exports
├── data_ingestion.py               # Day 1: load & inspect raw CSVs
├── live_nav_fetch.py               # Day 1: fetch live NAV from mfapi.in
├── clean_data.py                   # Day 2: clean all datasets
├── schema.sql                      # Day 2: star schema DDL
├── load_to_sqlite.py               # Day 2: load cleaned data into SQLite
├── queries.sql                     # Day 2: 10 analytical SQL queries
├── run_queries.py                  # Day 2: convenience script to run queries.sql
├── data_dictionary.md              # Day 2: column-level documentation
├── EDA_Analysis.ipynb              # Exploratory Data Analysis (15+ charts)
├── Performance_Analytics.ipynb     # CAGR, Sharpe, Sortino, Alpha/Beta, drawdown, scorecard
├── fund_scorecard.csv              # Output: composite 0-100 fund ranking
├── alpha_beta.csv                  # Output: Alpha/Beta per fund
├── Advanced_Analytics.ipynb        # VaR/CVaR, rolling Sharpe, cohorts, SIP continuity, HHI
├── var_cvar_report.csv             # Output: 95% VaR/CVaR per fund
├── recommender.py                  # Standalone fund recommender (risk-based)
├── run_pipeline.py                 # Master script: runs the full ETL pipeline end-to-end
├── bluestock_mf.db                 # SQLite database (star schema)
├── bluestock_mf_dashboard.pbix     # Power BI dashboard (4 pages)
├── Final_Report.pdf                # Final written report
├── Bluestock_MF_Presentation.pptx  # Final 12-slide presentation
├── requirements.txt
└── README.md
Setup Instructions
1. Clone the repository
bash
git clone https://github.com/srinithya4804-star/bluestock-mf-analytics.git
cd bluestock-mf-analytics
2. Create and activate a virtual environment
bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash) / macOS / Linux:
source .venv/Scripts/activate
3. Install dependencies
bash
pip install -r requirements.txt
How to Run the ETL Pipeline

Option A — run everything at once:

bash
python run_pipeline.py

This runs, in order: data_ingestion.py → live_nav_fetch.py → clean_data.py → load_to_sqlite.py, and reports success/failure at each stage.

Option B — run each stage individually:

bash
python data_ingestion.py      # Loads and inspects all 10 raw CSVs
python live_nav_fetch.py      # Fetches live NAV data from mfapi.in
python clean_data.py          # Cleans all datasets into data/processed/
python load_to_sqlite.py      # Builds the star schema, loads bluestock_mf.db

Then run the analysis notebooks (in VS Code or Jupyter, in this order):

bash
# Open and "Run All" in each notebook:
EDA_Analysis.ipynb
Performance_Analytics.ipynb
Advanced_Analytics.ipynb

Run the standalone fund recommender:

bash
python recommender.py
# then enter: Low / Moderate / High when prompted

Run the 10 analytical SQL queries against the database:

bash
python run_queries.py
How to Open the Dashboard
Install Power BI Desktop (free, Windows only)
Open bluestock_mf_dashboard.pbix
If prompted about data source paths, point Power BI at your local data/processed/ folder (Home → Transform Data → Data Source Settings)
The dashboard has 4 pages: Industry Overview, Fund Performance, Investor Analytics, and SIP & Market Trends
<!-- If the dashboard is published to Power BI Service or Tableau Public, add the live URL here: -->

Published dashboard URL: [add link here if published — see Task 6 of the Final Report ticket]

Dataset Descriptions
File	Description
01_fund_master.csv	Master list of 40 schemes — AMFI code, fund house, category, sub-category, plan, expense ratio, risk category, fund manager, etc.
02_nav_history.csv	Daily NAV per scheme, 2022-2026.
03_aum_by_fund_house.csv	AUM snapshots per fund house over time.
04_monthly_sip_inflows.csv	Industry-wide monthly SIP inflow totals, Jan 2022-Dec 2025.
05_category_inflows.csv	Net inflow by fund category, by month.
06_industry_folio_count.csv	Total investor folio counts by month, by fund type.
07_scheme_performance.csv	Return, risk, and rating metrics per scheme (1/3/5yr returns, alpha, beta, Sharpe, expense ratio, etc.).
08_investor_transactions.csv	~32,800 individual investor transactions — SIP, Lumpsum, Redemption, with investor demographics.
09_portfolio_holdings.csv	Stock-level holdings and sector weights per scheme.
10_benchmark_indices.csv	Daily close values for market benchmarks (Nifty 50, Nifty 100, and others).

Full column-level definitions are documented in data_dictionary.md.

Database Schema

bluestock_mf.db follows a star schema (see schema.sql):

Dimensions: dim_fund, dim_date
Facts: fact_nav, fact_transactions, fact_performance, fact_aum
Key Findings (Summary)
Total AUM across the 10 fund houses in this dataset grew from ~Rs. 3M crore (2022) to ~Rs. 6.5M crore (2025); SBI Mutual Fund leads AUM growth.
Monthly SIP inflows nearly tripled, reaching an all-time high of Rs. 31,002 crore in December 2025.
Folio count nearly doubled, from 13.26 crore to 26.12 crore.
Small Cap funds carry the highest downside risk (95% VaR), consistent with their "Very High" risk rating.
Risk-adjusted performance (rolling Sharpe) is highly regime-dependent — no fund holds a consistently strong Sharpe ratio over time.

Full findings are documented in Final_Report.pdf and within each notebook's markdown cells.

License / Usage

Built for Bluestock Fintech's Data Analytics Internship capstone project. Sample/synthetic data is used for training purposes and should not be used for real investment decisions.
