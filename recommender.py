"""
Bluestock Capstone Project I - Mutual Fund Analytics
Advanced Analytics + Risk Metrics - Task 5

Simple Fund Recommender
Input: risk appetite (Low / Moderate / High)
Output: top 3 funds by Sharpe ratio within the matching risk_category, printed as a table.

Run directly:
    python recommender.py
"""

import pandas as pd
import numpy as np

PROCESSED_DIR = "data/processed"
TRADING_DAYS = 252
RISK_FREE_RATE_ANNUAL = 0.065

VALID_RISK_LEVELS = ["Low", "Moderate", "High"]


def load_data():
    fund_master = pd.read_csv(f"{PROCESSED_DIR}/01_fund_master.csv")
    nav_history = pd.read_csv(f"{PROCESSED_DIR}/02_nav_history.csv", parse_dates=["date"])
    return fund_master, nav_history


def compute_sharpe_for_all_funds(nav_history: pd.DataFrame) -> pd.DataFrame:
    nav_wide = nav_history.pivot(index="date", columns="amfi_code", values="nav").sort_index()
    daily_returns = nav_wide.pct_change().dropna(how="all")
    rf_daily = RISK_FREE_RATE_ANNUAL / TRADING_DAYS

    rows = []
    for code in daily_returns.columns:
        r = daily_returns[code].dropna()
        if len(r) < 2 or r.std() == 0:
            sharpe = np.nan
        else:
            sharpe = (r.mean() - rf_daily) / r.std() * np.sqrt(TRADING_DAYS)
        rows.append({"amfi_code": code, "sharpe_ratio": sharpe})

    return pd.DataFrame(rows)


def recommend_funds(risk_appetite: str, fund_master: pd.DataFrame, sharpe_table: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    merged = sharpe_table.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "risk_category", "expense_ratio_pct"]],
        on="amfi_code", how="left"
    )

    # Match risk appetite against risk_category. Uses exact match first;
    # if the fund_master risk_category values differ (e.g. "Moderately High"),
    # this still works for exact "Low" / "Moderate" / "High" matches.
    matching = merged[merged["risk_category"].str.strip().str.lower() == risk_appetite.strip().lower()]

    if matching.empty:
        available = sorted(merged["risk_category"].dropna().unique().tolist())
        print(f"\nNo funds found with risk_category exactly matching '{risk_appetite}'.")
        print(f"Available risk_category values in your data: {available}")
        print("Try one of the values listed above.")
        return pd.DataFrame()

    top_funds = matching.sort_values("sharpe_ratio", ascending=False).head(top_n)
    return top_funds[["scheme_name", "fund_house", "risk_category", "sharpe_ratio", "expense_ratio_pct"]]


def main():
    print("=" * 60)
    print("Bluestock Mutual Fund Recommender")
    print("=" * 60)

    fund_master, nav_history = load_data()
    sharpe_table = compute_sharpe_for_all_funds(nav_history)

    print(f"\nAvailable risk levels: {', '.join(VALID_RISK_LEVELS)}")
    risk_appetite = input("Enter your risk appetite (Low / Moderate / High): ").strip()

    recommendations = recommend_funds(risk_appetite, fund_master, sharpe_table)

    if not recommendations.empty:
        print(f"\nTop {len(recommendations)} funds for '{risk_appetite}' risk appetite (ranked by Sharpe ratio):\n")
        recommendations_display = recommendations.copy()
        recommendations_display["sharpe_ratio"] = recommendations_display["sharpe_ratio"].round(3)
        print(recommendations_display.to_string(index=False))


if __name__ == "__main__":
    main()
