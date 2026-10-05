"""
prepare_powerbi.py
Power BI ready Excel + MySQL SQL file
Author : Bharath V
"""

import pandas as pd
import sqlite3
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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

def q(sql): return pd.read_sql_query(sql, conn)

# All sheets
sheets = {
    "Customers":           customers,
    "Transactions":        transactions,
    "RFM_Segments":        rfm,
    "KPI_Summary": pd.DataFrame({
        "KPI": ["Total Customers","Total Transactions","Total Revenue (Rs.)",
                "Avg Order Value (Rs.)","Return Rate (%)","Champions Count",
                "Loyal Customers Count","At Risk Count","Lost/Inactive Count"],
        "Value": [
            len(customers),
            len(transactions),
            round(transactions["final_amount"].sum(), 2),
            round(transactions["final_amount"].mean(), 2),
            round(transactions["returned"].mean()*100, 2),
            len(rfm[rfm["segment"]=="Champions"]),
            len(rfm[rfm["segment"]=="Loyal Customers"]),
            len(rfm[rfm["segment"]=="At Risk"]),
            len(rfm[rfm["segment"]=="Lost / Inactive"]),
        ]
    }),
    "By_Segment":   q("""
        SELECT segment,
               COUNT(customer_id) AS customers,
               ROUND(AVG(recency),1)   AS avg_recency_days,
               ROUND(AVG(frequency),1) AS avg_orders,
               ROUND(AVG(monetary),2)  AS avg_revenue,
               ROUND(SUM(monetary),2)  AS total_revenue,
               ROUND(SUM(monetary)*100.0/SUM(SUM(monetary)) OVER(),2) AS revenue_pct
        FROM rfm_segments GROUP BY segment ORDER BY total_revenue DESC"""),
    "By_Category":  q("""
        SELECT category,
               COUNT(*) AS total_orders,
               ROUND(SUM(final_amount),2) AS total_revenue,
               ROUND(AVG(final_amount),2) AS avg_order_value,
               ROUND(AVG(returned)*100,2) AS return_rate_pct
        FROM transactions GROUP BY category ORDER BY total_revenue DESC"""),
    "By_City":      q("""
        SELECT c.city,
               COUNT(DISTINCT t.customer_id) AS customers,
               COUNT(t.transaction_id)        AS orders,
               ROUND(SUM(t.final_amount),2)   AS total_revenue
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        GROUP BY c.city ORDER BY total_revenue DESC"""),
    "By_Age_Group": q("""
        SELECT c.age_group,
               COUNT(DISTINCT t.customer_id) AS customers,
               ROUND(AVG(t.final_amount),2)  AS avg_order_value,
               ROUND(SUM(t.final_amount),2)  AS total_revenue
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        GROUP BY c.age_group ORDER BY total_revenue DESC"""),
    "Monthly_Trend":q("""
        SELECT SUBSTR(transaction_date,1,7) AS month,
               COUNT(*) AS orders,
               ROUND(SUM(final_amount),2) AS revenue,
               ROUND(AVG(final_amount),2) AS avg_order_value
        FROM transactions GROUP BY month ORDER BY month"""),
    "Segment_x_Category": q("""
        SELECT r.segment, t.category,
               COUNT(*) AS orders,
               ROUND(SUM(t.final_amount),2) AS revenue
        FROM transactions t JOIN rfm_segments r ON t.customer_id=r.customer_id
        GROUP BY r.segment, t.category ORDER BY r.segment, revenue DESC"""),
    "High_Value_Customers": q("""
        SELECT r.customer_id, r.segment, c.age_group, c.city, c.gender,
               r.recency, r.frequency, ROUND(r.monetary,2) AS monetary,
               r.RFM_score
        FROM rfm_segments r JOIN customers c ON r.customer_id=c.customer_id
        WHERE r.segment IN ('Champions','Loyal Customers')
        ORDER BY r.monetary DESC"""),
}

xl_path = os.path.join(OUT_DIR, "CustomerSegmentation_PowerBI.xlsx")
with pd.ExcelWriter(xl_path, engine="openpyxl") as writer:
    for name, data in sheets.items():
        data.to_excel(writer, sheet_name=name, index=False)

# Style
wb = load_workbook(xl_path)
HDR_FILL = PatternFill("solid", fgColor="1B4F72")
ALT_FILL = PatternFill("solid", fgColor="D6EAF8")
HDR_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=10)
DAT_FONT = Font(name="Arial", size=10)
CENTER   = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT     = Alignment(horizontal="left",   vertical="center")
thin     = Side(style="thin", color="BFBFBF")
BORDER   = Border(left=thin, right=thin, top=thin, bottom=thin)

for ws in wb.worksheets:
    for cell in ws[1]:
        cell.fill = HDR_FILL; cell.font = HDR_FONT
        cell.alignment = CENTER; cell.border = BORDER
    for i, row in enumerate(ws.iter_rows(min_row=2), 2):
        fill = ALT_FILL if i % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")
        for cell in row:
            cell.fill = fill; cell.font = DAT_FONT
            cell.alignment = LEFT; cell.border = BORDER
    for col in ws.columns:
        ltr = get_column_letter(col[0].column)
        w   = min(max(len(str(c.value or "")) for c in col) + 4, 30)
        ws.column_dimensions[ltr].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

wb.save(xl_path)
print("Excel saved -> {}".format(xl_path))
conn.close()
