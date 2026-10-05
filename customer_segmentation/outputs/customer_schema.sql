-- ============================================================
--  CUSTOMER SEGMENTATION - MySQL Schema & Queries
--  Author  : Bharath V
--  Purpose : Load into MySQL and connect to Power BI
-- ============================================================

CREATE DATABASE IF NOT EXISTS customer_segmentation_db;
USE customer_segmentation_db;

-- ── TABLES ───────────────────────────────────────────────────

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS rfm_segments;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id  VARCHAR(10) PRIMARY KEY,
    gender       VARCHAR(10),
    age_group    VARCHAR(10),
    city         VARCHAR(50),
    signup_date  DATE
);

CREATE TABLE transactions (
    transaction_id   VARCHAR(10) PRIMARY KEY,
    customer_id      VARCHAR(10),
    transaction_date DATE,
    category         VARCHAR(30),
    product_amount   DECIMAL(12,2),
    quantity         INT,
    discount_pct     INT,
    final_amount     DECIMAL(12,2),
    payment_mode     VARCHAR(20),
    returned         TINYINT(1),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE rfm_segments (
    customer_id  VARCHAR(10) PRIMARY KEY,
    recency      INT,
    frequency    INT,
    monetary     DECIMAL(12,2),
    R_score      INT,
    F_score      INT,
    M_score      INT,
    RFM_score    INT,
    cluster      INT,
    segment      VARCHAR(30),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ── LOAD DATA ─────────────────────────────────────────────────
-- Use MySQL Workbench: Right-click table > Table Data Import Wizard
-- Import in order: customers -> transactions -> rfm_segments


-- ============================================================
--  POWER BI READY VIEWS
-- ============================================================

CREATE OR REPLACE VIEW vw_kpi_summary AS
SELECT
    COUNT(DISTINCT c.customer_id)            AS total_customers,
    COUNT(t.transaction_id)                  AS total_transactions,
    ROUND(SUM(t.final_amount), 2)            AS total_revenue,
    ROUND(AVG(t.final_amount), 2)            AS avg_order_value,
    ROUND(AVG(t.returned) * 100, 2)          AS return_rate_pct,
    COUNT(DISTINCT CASE WHEN r.segment = 'Champions'       THEN r.customer_id END) AS champions,
    COUNT(DISTINCT CASE WHEN r.segment = 'Loyal Customers' THEN r.customer_id END) AS loyal_customers,
    COUNT(DISTINCT CASE WHEN r.segment = 'At Risk'         THEN r.customer_id END) AS at_risk,
    COUNT(DISTINCT CASE WHEN r.segment = 'Lost / Inactive' THEN r.customer_id END) AS lost_inactive
FROM customers c
LEFT JOIN transactions t  ON c.customer_id = t.customer_id
LEFT JOIN rfm_segments r  ON c.customer_id = r.customer_id;


CREATE OR REPLACE VIEW vw_rfm_segments AS
SELECT
    r.customer_id, r.segment,
    c.age_group, c.city, c.gender,
    r.recency, r.frequency,
    ROUND(r.monetary, 2)    AS monetary,
    r.R_score, r.F_score, r.M_score, r.RFM_score
FROM rfm_segments r
JOIN customers c ON r.customer_id = c.customer_id;


CREATE OR REPLACE VIEW vw_segment_summary AS
SELECT
    r.segment,
    COUNT(r.customer_id)                     AS customers,
    ROUND(AVG(r.recency), 1)                 AS avg_recency_days,
    ROUND(AVG(r.frequency), 1)               AS avg_orders,
    ROUND(AVG(r.monetary), 2)                AS avg_revenue,
    ROUND(SUM(r.monetary), 2)                AS total_revenue,
    ROUND(SUM(r.monetary) * 100.0
        / SUM(SUM(r.monetary)) OVER (), 2)   AS revenue_pct
FROM rfm_segments r
GROUP BY r.segment;


CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    category,
    COUNT(transaction_id)               AS total_orders,
    ROUND(SUM(final_amount), 2)         AS total_revenue,
    ROUND(AVG(final_amount), 2)         AS avg_order_value,
    ROUND(AVG(returned) * 100, 2)       AS return_rate_pct,
    RANK() OVER (ORDER BY SUM(final_amount) DESC) AS revenue_rank
FROM transactions
GROUP BY category;


CREATE OR REPLACE VIEW vw_monthly_trend AS
SELECT
    DATE_FORMAT(transaction_date, '%Y-%m')  AS month,
    YEAR(transaction_date)                  AS year,
    MONTH(transaction_date)                 AS month_num,
    MONTHNAME(transaction_date)             AS month_name,
    COUNT(transaction_id)                   AS total_orders,
    ROUND(SUM(final_amount), 2)             AS total_revenue,
    ROUND(AVG(final_amount), 2)             AS avg_order_value,
    SUM(returned)                           AS returns
FROM transactions
GROUP BY month, year, month_num, month_name
ORDER BY month;


CREATE OR REPLACE VIEW vw_city_performance AS
SELECT
    c.city,
    COUNT(DISTINCT t.customer_id)          AS customers,
    COUNT(t.transaction_id)                AS orders,
    ROUND(SUM(t.final_amount), 2)          AS total_revenue,
    ROUND(AVG(t.final_amount), 2)          AS avg_order_value
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.city
ORDER BY total_revenue DESC;


CREATE OR REPLACE VIEW vw_segment_x_category AS
SELECT
    r.segment, t.category,
    COUNT(t.transaction_id)                AS orders,
    ROUND(SUM(t.final_amount), 2)          AS revenue,
    ROUND(AVG(t.final_amount), 2)          AS avg_order_value
FROM transactions t
JOIN rfm_segments r ON t.customer_id = r.customer_id
GROUP BY r.segment, t.category
ORDER BY r.segment, revenue DESC;


CREATE OR REPLACE VIEW vw_high_value_customers AS
SELECT
    r.customer_id, r.segment,
    c.age_group, c.city, c.gender,
    r.recency, r.frequency,
    ROUND(r.monetary, 2)                   AS lifetime_value,
    r.RFM_score
FROM rfm_segments r
JOIN customers c ON r.customer_id = c.customer_id
WHERE r.segment IN ('Champions', 'Loyal Customers')
ORDER BY r.monetary DESC;


-- ============================================================
--  ANALYTICAL QUERIES
-- ============================================================

-- Top 20% customers driving 80% revenue
WITH customer_revenue AS (
    SELECT customer_id,
           SUM(final_amount) AS total_spent
    FROM transactions
    GROUP BY customer_id
),
ranked AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY total_spent DESC) AS quintile
    FROM customer_revenue
)
SELECT quintile,
       COUNT(*)                                       AS customers,
       ROUND(SUM(total_spent), 2)                    AS revenue,
       ROUND(SUM(total_spent)*100.0
           / SUM(SUM(total_spent)) OVER (), 2)       AS revenue_pct
FROM ranked
GROUP BY quintile
ORDER BY quintile;


-- Month-over-Month growth
WITH monthly AS (
    SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month,
           ROUND(SUM(final_amount), 2)            AS revenue
    FROM transactions
    GROUP BY month
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month)          AS prev_month_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
           * 100.0
           / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly
ORDER BY month;


-- Cohort retention by first purchase month
WITH first_purchase AS (
    SELECT customer_id,
           MIN(DATE_FORMAT(transaction_date,'%Y-%m')) AS cohort_month
    FROM transactions
    GROUP BY customer_id
)
SELECT f.cohort_month,
       COUNT(DISTINCT t.customer_id)               AS customers,
       ROUND(SUM(t.final_amount), 2)               AS total_revenue,
       ROUND(AVG(t.final_amount), 2)               AS avg_order_value
FROM transactions t
JOIN first_purchase f ON t.customer_id = f.customer_id
GROUP BY f.cohort_month
ORDER BY f.cohort_month;


-- ============================================================
--  HOW TO CONNECT POWER BI TO MYSQL
-- ============================================================
-- 1. Open Power BI Desktop
-- 2. Home > Get Data > MySQL Database
-- 3. Server: localhost   Database: customer_segmentation_db
-- 4. Import these views:
--      vw_kpi_summary           -> Card KPI visuals
--      vw_segment_summary       -> Bar/Donut - segment revenue
--      vw_rfm_segments          -> Scatter plot RFM
--      vw_monthly_trend         -> Line chart - revenue trend
--      vw_category_performance  -> Bar chart - category revenue
--      vw_city_performance      -> Map / bar - city revenue
--      vw_segment_x_category    -> Matrix visual
--      vw_high_value_customers  -> Drill-through table
-- ============================================================
