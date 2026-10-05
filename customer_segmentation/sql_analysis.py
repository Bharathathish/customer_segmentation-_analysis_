"""
sql_analysis.py
SQL-based analysis using SQLite (mimics MySQL)
Window Functions · CTEs · Cohort Analysis
Author : Bharath V
"""

import pandas as pd
import sqlite3
import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

customers    = pd.read_csv(os.path.join(BASE_DIR, "data", "customers.csv"))
transactions = pd.read_csv(os.path.join(BASE_DIR, "data", "transactions.csv"))
rfm          = pd.read_csv(os.path.join(OUT_DIR, "rfm_segments.csv"))

conn = sqlite3.connect(":memory:")
customers.to_sql("customers",    conn, index=False, if_exists="replace")
transactions.to_sql("transactions", conn, index=False, if_exists="replace")
rfm.to_sql("rfm_segments",      conn, index=False, if_exists="replace")

print("=" * 55)
print("  SQL ANALYSIS  -  Customer Segmentation")
print("=" * 55)

def run(title, sql):
    result = pd.read_sql_query(sql, conn)
    print("\n-- {} {}".format(title, "-"*(48-len(title))))
    print(result.to_string(index=False))
    return result

# 1. Top 20% customers by revenue (with running total)
run("Top 20 Customers by Revenue (Window Rank)", """
SELECT
    t.customer_id,
    c.age_group, c.city,
    COUNT(t.transaction_id)              AS orders,
    ROUND(SUM(t.final_amount), 2)        AS total_spent,
    RANK() OVER (ORDER BY SUM(t.final_amount) DESC) AS revenue_rank,
    ROUND(SUM(SUM(t.final_amount)) OVER (
        ORDER BY SUM(t.final_amount) DESC
    ), 2)                                AS running_total
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY t.customer_id, c.age_group, c.city
ORDER BY total_spent DESC
LIMIT 20
""")

# 2. Revenue by Segment
run("Revenue Contribution by Segment", """
SELECT
    r.segment,
    COUNT(r.customer_id)                 AS customers,
    ROUND(AVG(r.recency), 1)             AS avg_recency_days,
    ROUND(AVG(r.frequency), 1)           AS avg_orders,
    ROUND(AVG(r.monetary), 2)            AS avg_revenue,
    ROUND(SUM(r.monetary), 2)            AS total_revenue,
    ROUND(SUM(r.monetary) * 100.0
        / SUM(SUM(r.monetary)) OVER (), 2) AS revenue_pct
FROM rfm_segments r
GROUP BY r.segment
ORDER BY total_revenue DESC
""")

# 3. CTE - Cohort Analysis (first purchase month)
run("Cohort Analysis - Revenue by First Purchase Month", """
WITH first_purchase AS (
    SELECT customer_id,
           MIN(SUBSTR(transaction_date,1,7)) AS cohort_month
    FROM transactions
    GROUP BY customer_id
),
cohort_data AS (
    SELECT f.cohort_month,
           SUBSTR(t.transaction_date,1,7) AS txn_month,
           t.customer_id,
           t.final_amount
    FROM transactions t
    JOIN first_purchase f ON t.customer_id = f.customer_id
)
SELECT
    cohort_month,
    COUNT(DISTINCT customer_id)   AS customers,
    ROUND(SUM(final_amount), 2)   AS total_revenue,
    ROUND(AVG(final_amount), 2)   AS avg_order_value
FROM cohort_data
GROUP BY cohort_month
ORDER BY cohort_month
LIMIT 12
""")

# 4. Category revenue with running % (CTE + Window)
run("Category Revenue with Cumulative % (CTE + Window)", """
WITH cat_rev AS (
    SELECT category,
           ROUND(SUM(final_amount), 2)  AS total_revenue,
           COUNT(transaction_id)         AS total_orders,
           ROUND(AVG(final_amount), 2)  AS avg_order_value
    FROM transactions
    GROUP BY category
)
SELECT
    category, total_orders, total_revenue, avg_order_value,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    ROUND(SUM(total_revenue) OVER (
        ORDER BY total_revenue DESC
    ) * 100.0 / SUM(total_revenue) OVER (), 2) AS cumulative_pct
FROM cat_rev
ORDER BY total_revenue DESC
""")

# 5. Monthly revenue with MoM growth (LAG)
run("Month-over-Month Revenue Growth", """
WITH monthly AS (
    SELECT SUBSTR(transaction_date,1,7) AS month,
           ROUND(SUM(final_amount), 2)  AS revenue
    FROM transactions
    GROUP BY month
)
SELECT
    month, revenue,
    LAG(revenue) OVER (ORDER BY month)  AS prev_month,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
        * 100.0
        / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly
ORDER BY month
""")

# 6. RFM segment x category (which segment buys what)
run("Segment x Category Revenue Matrix", """
SELECT
    r.segment,
    t.category,
    COUNT(t.transaction_id)       AS orders,
    ROUND(SUM(t.final_amount),2)  AS total_revenue
FROM transactions t
JOIN rfm_segments r ON t.customer_id = r.customer_id
GROUP BY r.segment, t.category
ORDER BY r.segment, total_revenue DESC
""")

# 7. Return rate by segment
run("Return Rate by Segment", """
SELECT
    r.segment,
    COUNT(t.transaction_id)       AS total_orders,
    SUM(t.returned)               AS returned_orders,
    ROUND(AVG(t.returned)*100,2)  AS return_rate_pct
FROM transactions t
JOIN rfm_segments r ON t.customer_id = r.customer_id
GROUP BY r.segment
ORDER BY return_rate_pct DESC
""")

# Export SQL summary
summary = pd.read_sql_query("""
SELECT
    r.segment, c.age_group, c.city, c.gender,
    COUNT(t.transaction_id)       AS total_orders,
    ROUND(SUM(t.final_amount),2)  AS total_revenue,
    ROUND(AVG(t.final_amount),2)  AS avg_order_value,
    ROUND(AVG(t.returned)*100,2)  AS return_rate_pct
FROM transactions t
JOIN customers c    ON t.customer_id = c.customer_id
JOIN rfm_segments r ON t.customer_id = r.customer_id
GROUP BY r.segment, c.age_group, c.city, c.gender
ORDER BY total_revenue DESC
""", conn)

summary.to_csv(os.path.join(OUT_DIR, "sql_summary.csv"), index=False)
print("\n  SQL summary exported -> outputs/sql_summary.csv")
print("  Run dashboard.py next.\n")
conn.close()
