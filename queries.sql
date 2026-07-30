-- Bluestock Capstone Project I - Mutual Fund Analytics
-- Day 2 - Step 6: 10 Analytical SQL Queries
-- Run against bluestock_mf.db

-- ---------------------------------------------------------------------------
-- 1. Top 5 funds by AUM (most recent date available)
-- ---------------------------------------------------------------------------
SELECT fund_house, aum_value, date_id
FROM fact_aum
WHERE date_id = (SELECT MAX(date_id) FROM fact_aum)
ORDER BY aum_value DESC
LIMIT 5;

-- ---------------------------------------------------------------------------
-- 2. Average NAV per month, per fund
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    d.year,
    d.month,
    ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.scheme_name, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month;

-- ---------------------------------------------------------------------------
-- 3. SIP year-over-year growth (total SIP transaction amount by year)
-- ---------------------------------------------------------------------------
SELECT
    d.year,
    SUM(t.amount) AS total_sip_amount
FROM fact_transactions t
JOIN dim_date d ON t.date_id = d.date_id
WHERE t.transaction_type = 'SIP'
GROUP BY d.year
ORDER BY d.year;

-- ---------------------------------------------------------------------------
-- 4. Transactions by state
-- ---------------------------------------------------------------------------
SELECT
    state,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- ---------------------------------------------------------------------------
-- 5. Funds with expense_ratio < 1%
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    f.expense_ratio_pct
FROM dim_fund f
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;

-- ---------------------------------------------------------------------------
-- 6. Top 5 funds by 1-year return
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    p.return_1yr
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.return_1yr DESC
LIMIT 5;

-- ---------------------------------------------------------------------------
-- 7. Fund count and average risk by category
-- ---------------------------------------------------------------------------
SELECT
    category,
    risk_category,
    COUNT(*) AS fund_count
FROM dim_fund
GROUP BY category, risk_category
ORDER BY category, fund_count DESC;

-- ---------------------------------------------------------------------------
-- 8. Redemption vs SIP vs Lumpsum split (overall transaction mix)
-- ---------------------------------------------------------------------------
SELECT
    transaction_type,
    COUNT(*) AS num_transactions,
    SUM(amount) AS total_amount,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_transactions), 2) AS pct_of_transactions
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;

-- ---------------------------------------------------------------------------
-- 9. KYC status breakdown among investors
-- ---------------------------------------------------------------------------
SELECT
    kyc_status,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY kyc_status
ORDER BY transaction_count DESC;

-- ---------------------------------------------------------------------------
-- 10. Funds where 1yr return beats their own 3yr average annualised return
--     (simple momentum flag: recent performance outperforming longer-term trend)
-- ---------------------------------------------------------------------------
SELECT
    f.scheme_name,
    p.return_1yr,
    p.return_3yr,
    ROUND(p.return_1yr - p.return_3yr, 2) AS momentum_gap
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_1yr > p.return_3yr
ORDER BY momentum_gap DESC;
