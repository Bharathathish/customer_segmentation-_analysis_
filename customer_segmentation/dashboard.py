"""
dashboard.py
Multi-panel summary dashboard - Customer Segmentation
Author : Bharath V
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.dpi": 130, "font.family": "DejaVu Sans"})

transactions = pd.read_csv(os.path.join(BASE_DIR, "data", "transactions.csv"))
rfm          = pd.read_csv(os.path.join(OUT_DIR, "rfm_segments.csv"))
transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
transactions["month"] = transactions["transaction_date"].dt.to_period("M").astype(str)

seg_pal = {"Champions": "#27AE60", "Loyal Customers": "#2980B9",
           "At Risk": "#E67E22", "Lost / Inactive": "#E74C3C"}
seg_order = ["Champions", "Loyal Customers", "At Risk", "Lost / Inactive"]

fig = plt.figure(figsize=(18, 13))
fig.suptitle("Customer Segmentation Dashboard - Bharath V",
             fontsize=17, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.52, wspace=0.38)

# KPI tiles
kpis = [
    ("Total Customers",   "{:,}".format(rfm["customer_id"].nunique())),
    ("Total Revenue",     "Rs.{:.1f}M".format(rfm["monetary"].sum()/1e6)),
    ("Avg Order Value",   "Rs.{:,.0f}".format(transactions["final_amount"].mean())),
]
for idx, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, idx])
    ax.set_facecolor("#EAF4FB")
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=20,
            fontweight="bold", color="#1A5276", transform=ax.transAxes)
    ax.text(0.5, 0.28, label, ha="center", va="center", fontsize=10,
            color="#555", transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#AED6F1"); spine.set_linewidth(1.5)

# Segment Revenue Bar
ax1 = fig.add_subplot(gs[1, :2])
seg_rev = rfm.groupby("segment")["monetary"].sum().reindex(seg_order)
bars = ax1.bar(seg_rev.index, seg_rev.values / 1e6,
               color=[seg_pal[s] for s in seg_rev.index])
total = seg_rev.sum()
ax1.bar_label(bars, labels=["{:.1f}%".format(v/total*100) for v in seg_rev.values],
              padding=4, fontsize=10, fontweight="bold")
ax1.set_title("Revenue Contribution by Segment", fontweight="bold")
ax1.set_ylabel("Revenue (Rs. Millions)")
ax1.tick_params(axis="x", rotation=15)

# Customer Count Pie
ax2 = fig.add_subplot(gs[1, 2])
seg_cnt = rfm["segment"].value_counts().reindex(seg_order)
ax2.pie(seg_cnt.values, labels=seg_cnt.index, autopct="%1.0f%%",
        startangle=140, colors=[seg_pal[s] for s in seg_order])
ax2.set_title("Customer Count by Segment", fontweight="bold")

# Monthly Revenue Trend
ax3 = fig.add_subplot(gs[2, :2])
monthly = transactions.groupby("month")["final_amount"].sum() / 1e6
ax3.plot(monthly.index, monthly.values, marker="o", linewidth=2,
         color="#2980B9", markersize=5)
ax3.fill_between(monthly.index, monthly.values, alpha=0.1, color="#2980B9")
ax3.set_title("Monthly Revenue Trend", fontweight="bold")
ax3.set_ylabel("Revenue (Rs. Millions)")
ax3.tick_params(axis="x", rotation=55, labelsize=7)

# Avg Monetary by Segment
ax4 = fig.add_subplot(gs[2, 2])
seg_avg = rfm.groupby("segment")["monetary"].mean().reindex(seg_order)
bars2 = ax4.bar(seg_avg.index, seg_avg.values / 1000,
                color=[seg_pal[s] for s in seg_order])
ax4.bar_label(bars2, labels=["Rs.{:.1f}K".format(v/1000) for v in seg_avg.values],
              padding=3, fontsize=8)
ax4.set_title("Avg Revenue per Customer by Segment", fontweight="bold")
ax4.set_ylabel("Avg Revenue (Rs. Thousands)")
ax4.tick_params(axis="x", rotation=20, labelsize=8)

out_path = os.path.join(OUT_DIR, "customer_dashboard.png")
plt.savefig(out_path, bbox_inches="tight")
plt.close()
print("Dashboard saved -> {}".format(out_path))
