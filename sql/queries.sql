-- ============================================================================
-- Project 2: Personal Financial Intelligence System
-- Analysis queries against sql/finances.db
-- Each query is labeled with the dashboard question it answers and the SQL
-- technique it demonstrates (aggregation / JOIN / date functions / window
-- functions), per the project's Skills Required list.
-- Run with: sqlite3 finances.db < queries.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Where does most of my money go? (spending by category)
-- Technique: JOIN, WHERE, GROUP BY, aggregation
-- ----------------------------------------------------------------------------
SELECT
    c.category_name,
    COUNT(*)                                   AS transaction_count,
    ROUND(SUM(-t.amount), 2)                   AS total_spent,
    ROUND(100.0 * SUM(-t.amount) /
        (SELECT SUM(-amount) FROM transactions WHERE amount < 0), 1) AS pct_of_spending
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN categories c ON c.category_id = m.category_id
WHERE t.amount < 0
GROUP BY c.category_name
ORDER BY total_spent DESC;


-- ----------------------------------------------------------------------------
-- Q2. Which categories increased the most vs. the previous month?
-- Technique: CTE, date functions (strftime), window function LAG()
-- ----------------------------------------------------------------------------
WITH monthly_category AS (
    SELECT
        strftime('%Y-%m', t.date)  AS month,
        c.category_name,
        SUM(-t.amount)              AS spent
    FROM transactions t
    JOIN merchants m ON m.merchant_id = t.merchant_id
    JOIN categories c ON c.category_id = m.category_id
    WHERE t.amount < 0
    GROUP BY strftime('%Y-%m', t.date), c.category_name
),
with_change AS (
    SELECT
        month,
        category_name,
        ROUND(spent, 2) AS spent,
        ROUND(LAG(spent) OVER (PARTITION BY category_name ORDER BY month), 2) AS prev_month_spent,
        ROUND(spent - LAG(spent) OVER (PARTITION BY category_name ORDER BY month), 2) AS change
    FROM monthly_category
)
SELECT * FROM with_change
WHERE prev_month_spent IS NOT NULL
ORDER BY month DESC, change DESC;


-- ----------------------------------------------------------------------------
-- Q3. Which merchants receive the most money?
-- Technique: JOIN, GROUP BY, ORDER BY, LIMIT
-- ----------------------------------------------------------------------------
SELECT
    m.merchant_name,
    c.category_name,
    COUNT(*)                    AS visits,
    ROUND(SUM(-t.amount), 2)    AS total_spent,
    ROUND(AVG(-t.amount), 2)    AS avg_transaction
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN categories c ON c.category_id = m.category_id
WHERE t.amount < 0
GROUP BY m.merchant_name, c.category_name
ORDER BY total_spent DESC
LIMIT 15;


-- ----------------------------------------------------------------------------
-- Q4. What subscriptions am I paying for, and what do they cost per month?
-- Technique: WHERE, JOIN, GROUP BY, HAVING
-- ----------------------------------------------------------------------------
SELECT
    m.merchant_name,
    COUNT(*)                                AS months_charged,
    ROUND(AVG(-t.amount), 2)                AS monthly_cost,
    ROUND(AVG(-t.amount) * 12, 2)           AS estimated_annual_cost
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN categories c ON c.category_id = m.category_id
WHERE c.category_name = 'Subscriptions'
GROUP BY m.merchant_name
HAVING COUNT(*) >= 2
ORDER BY monthly_cost DESC;


-- ----------------------------------------------------------------------------
-- Q5. Which merchants are recurring bills/subscriptions, detected purely from
--     behavior (charged in most months present in the data, similar amount
--     each time) - not just relying on the category label.
-- Technique: CTE, date functions, aggregation, HAVING
-- ----------------------------------------------------------------------------
WITH months_in_data AS (
    SELECT COUNT(DISTINCT strftime('%Y-%m', date)) AS n FROM transactions
),
merchant_monthly AS (
    SELECT
        m.merchant_name,
        COUNT(DISTINCT strftime('%Y-%m', t.date)) AS months_active,
        ROUND(AVG(-t.amount), 2)                   AS avg_amount,
        ROUND(MAX(-t.amount) - MIN(-t.amount), 2)   AS amount_range
    FROM transactions t
    JOIN merchants m ON m.merchant_id = t.merchant_id
    WHERE t.amount < 0
    GROUP BY m.merchant_name
)
SELECT
    mm.merchant_name,
    mm.months_active,
    mi.n AS total_months_in_data,
    mm.avg_amount,
    mm.amount_range
FROM merchant_monthly mm, months_in_data mi
WHERE mm.months_active >= mi.n - 1        -- charged in nearly every month
  AND mm.amount_range < 5                  -- and the amount barely changes
ORDER BY mm.avg_amount DESC;


-- ----------------------------------------------------------------------------
-- Q6. Which transactions look unusual? (anomaly detection: amount more than
--     2 standard deviations above that merchant's own average)
-- Technique: CTE, manually-computed standard deviation, JOIN, CASE
-- ----------------------------------------------------------------------------
WITH merchant_stats AS (
    SELECT
        m.merchant_id,
        m.merchant_name,
        AVG(-t.amount) AS avg_amount,
        -- SQLite has no built-in STDEV, so compute variance directly:
        SQRT(AVG((-t.amount - sub.avg_amt) * (-t.amount - sub.avg_amt))) AS std_amount
    FROM transactions t
    JOIN merchants m ON m.merchant_id = t.merchant_id
    JOIN (
        SELECT merchant_id, AVG(-amount) AS avg_amt
        FROM transactions
        WHERE amount < 0
        GROUP BY merchant_id
    ) sub ON sub.merchant_id = t.merchant_id
    WHERE t.amount < 0
    GROUP BY m.merchant_id, m.merchant_name
    HAVING COUNT(*) >= 3   -- need enough history to judge "unusual"
)
SELECT
    t.date,
    m.merchant_name,
    ROUND(-t.amount, 2)          AS amount,
    ROUND(ms.avg_amount, 2)      AS merchant_avg,
    ROUND(ms.std_amount, 2)      AS merchant_stddev,
    ROUND((-t.amount - ms.avg_amount) / NULLIF(ms.std_amount, 0), 1) AS z_score
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN merchant_stats ms ON ms.merchant_id = t.merchant_id
WHERE t.amount < 0
  AND ms.std_amount > 0
  AND (-t.amount - ms.avg_amount) / ms.std_amount > 2
ORDER BY z_score DESC;


-- ----------------------------------------------------------------------------
-- Q7. How much could I potentially save? (total recurring subscription spend,
--     as one concrete, cancelable savings opportunity)
-- Technique: aggregation, subquery
-- ----------------------------------------------------------------------------
SELECT
    ROUND(SUM(monthly_cost), 2)      AS total_monthly_subscriptions,
    ROUND(SUM(monthly_cost) * 12, 2) AS total_annual_subscriptions
FROM (
    SELECT m.merchant_name, AVG(-t.amount) AS monthly_cost
    FROM transactions t
    JOIN merchants m ON m.merchant_id = t.merchant_id
    JOIN categories c ON c.category_id = m.category_id
    WHERE c.category_name = 'Subscriptions'
    GROUP BY m.merchant_name
);


-- ----------------------------------------------------------------------------
-- Q8. Monthly spending trend with a running (cumulative) total.
-- Technique: CTE, date functions, window function SUM() OVER
-- ----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        strftime('%Y-%m', date) AS month,
        SUM(-amount)             AS spent,
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income
    FROM transactions
    GROUP BY strftime('%Y-%m', date)
)
SELECT
    month,
    ROUND(spent, 2)                                        AS spent,
    ROUND(income, 2)                                        AS income,
    ROUND(income - spent, 2)                                AS net,
    ROUND(SUM(spent) OVER (ORDER BY month), 2)              AS cumulative_spent
FROM monthly
ORDER BY month;


-- ----------------------------------------------------------------------------
-- Q9. Rank spending categories by total spend.
-- Technique: window functions RANK() and DENSE_RANK()
-- ----------------------------------------------------------------------------
SELECT
    c.category_name,
    ROUND(SUM(-t.amount), 2)                        AS total_spent,
    RANK()       OVER (ORDER BY SUM(-t.amount) DESC) AS rank_by_spend,
    DENSE_RANK() OVER (ORDER BY SUM(-t.amount) DESC) AS dense_rank_by_spend
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN categories c ON c.category_id = m.category_id
WHERE t.amount < 0
GROUP BY c.category_name
ORDER BY total_spent DESC;


-- ----------------------------------------------------------------------------
-- Q10. Spending pattern by day of week.
-- Technique: date functions (strftime day-of-week), aggregation
-- ----------------------------------------------------------------------------
SELECT
    CASE CAST(strftime('%w', date) AS INTEGER)
        WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_of_week,
    COUNT(*)                  AS transactions,
    ROUND(SUM(-amount), 2)    AS total_spent,
    ROUND(AVG(-amount), 2)    AS avg_transaction
FROM transactions
WHERE amount < 0
GROUP BY strftime('%w', date)
ORDER BY strftime('%w', date);


-- ----------------------------------------------------------------------------
-- Q11. Income vs. expenses by month, with a CASE-based classification of
--      each month as Surplus or Deficit.
-- Technique: CTE, CASE, aggregation
-- ----------------------------------------------------------------------------
WITH monthly_net AS (
    SELECT
        strftime('%Y-%m', date) AS month,
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END)  AS income,
        SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END) AS expenses
    FROM transactions
    GROUP BY strftime('%Y-%m', date)
)
SELECT
    month,
    ROUND(income, 2)             AS income,
    ROUND(expenses, 2)           AS expenses,
    ROUND(income - expenses, 2)  AS net,
    CASE WHEN income - expenses >= 0 THEN 'Surplus' ELSE 'Deficit' END AS status
FROM monthly_net
ORDER BY month;


-- ----------------------------------------------------------------------------
-- Q12. Top 10 single largest transactions in the period (the "what happened
--      here" list a human would want to double-check).
-- Technique: window function PERCENT_RANK, ORDER BY, LIMIT
-- ----------------------------------------------------------------------------
SELECT
    t.date,
    m.merchant_name,
    c.category_name,
    ROUND(-t.amount, 2) AS amount,
    ROUND(PERCENT_RANK() OVER (ORDER BY -t.amount), 3) AS percentile_of_all_spend
FROM transactions t
JOIN merchants m ON m.merchant_id = t.merchant_id
JOIN categories c ON c.category_id = m.category_id
WHERE t.amount < 0
ORDER BY amount DESC
LIMIT 10;
