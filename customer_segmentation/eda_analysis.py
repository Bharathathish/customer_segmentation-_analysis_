"""
eda_analysis.py
Exploratory Data Analysis - Customer Segmentation
Author : Bharath V
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 130, "font.family": "DejaVu Sans"})

customers    = pd.read_csv(os.path.join(BASE_DIR, "data", "customers.csv"))
transactions = pd.read_csv(os.path.join(BASE_DIR, "data", "transactions.csv"))
transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])

merged = transactions.merge(customers, on="customer_id", how="left")

print("=" * 55)
print("  CUSTOMER SEGMENTATION  -  EDA REPORT")
print("=" * 55)
print("\n  Total Customers   : {:,}".format(len(customers)))
print("  Total Transactions: {:,}".format(len(transactions)))
print("  Total Revenue     : Rs.{:,.0f}".format(transactions["final_amount"].sum()))
print("  Avg Order Value   : Rs.{:,.0f}".format(transactions["final_amount"].mean()))
print("  Return Rate       : {:.1f}%".format(transactions["returned"].mean()*100))
print()

# 1. Revenue by Category
fig, ax = plt.subplots(figsize=(11, 5))
cat_rev = transactions.groupby("category")["final_amount"].sum().sort_values(ascending=False)
colors  = sns.color_palette("Blues_d", len(cat_rev))
bars    = ax.bar(cat_rev.index, cat_rev.values / 1e6, color=colors)
ax.bar_label(bars, labels=["Rs.{:.1f}M".format(v/1e6) for v in cat_rev.values], padding=4, fontsize=8)
ax.set_title("Total Revenue by Category", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Category"); ax.set_ylabel("Revenue (Rs. Millions)")
ax.tick_params(axis="x", rotation=35)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "01_revenue_by_category.png"))
plt.close()
print("  [1/7] Saved: revenue by category")

# 2. Transactions by Age Group
fig, ax = plt.subplots(figsize=(8, 4))
age_order = ["18-25", "26-35", "36-45", "46-55", "55+"]
age_rev   = merged.groupby("age_group")["final_amount"].sum().reindex(age_order)
bars = ax.bar(age_rev.index, age_rev.values / 1e6,
              color=sns.color_palette("Oranges_d", len(age_rev)))
ax.bar_label(bars, labels=["Rs.{:.1f}M".format(v/1e6) for v in age_rev.values], padding=4, fontsize=9)
ax.set_title("Total Revenue by Age Group", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Age Group"); ax.set_ylabel("Revenue (Rs. Millions)")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "02_revenue_by_age.png"))
plt.close()
print("  [2/7] Saved: revenue by age group")

# 3. Payment Mode Distribution
fig, ax = plt.subplots(figsize=(7, 5))
pay_cnt = transactions["payment_mode"].value_counts()
ax.pie(pay_cnt.values, labels=pay_cnt.index, autopct="%1.1f%%",
       startangle=140, colors=sns.color_palette("Set2", len(pay_cnt)))
ax.set_title("Payment Mode Distribution", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "03_payment_mode.png"))
plt.close()
print("  [3/7] Saved: payment mode distribution")

# 4. Monthly Revenue Trend
transactions["month"] = transactions["transaction_date"].dt.to_period("M").astype(str)
monthly = transactions.groupby("month")["final_amount"].sum()
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(monthly.index, monthly.values / 1e6, marker="o", linewidth=2,
        color="#1F78B4", markersize=5)
ax.fill_between(monthly.index, monthly.values / 1e6, alpha=0.12, color="#1F78B4")
ax.set_title("Monthly Revenue Trend", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("Revenue (Rs. Millions)"); ax.set_xlabel("Month")
ax.tick_params(axis="x", rotation=50, labelsize=8)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "04_monthly_revenue_trend.png"))
plt.close()
print("  [4/7] Saved: monthly revenue trend")

# 5. Order Value Distribution
fig, ax = plt.subplots(figsize=(9, 4))
ax.hist(transactions["final_amount"], bins=50, color="#2196F3", edgecolor="white", alpha=0.85)
ax.axvline(transactions["final_amount"].mean(), color="red", linestyle="--",
           linewidth=1.5, label="Mean: Rs.{:,.0f}".format(transactions["final_amount"].mean()))
ax.axvline(transactions["final_amount"].median(), color="orange", linestyle="--",
           linewidth=1.5, label="Median: Rs.{:,.0f}".format(transactions["final_amount"].median()))
ax.set_title("Order Value Distribution", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Order Value (Rs.)"); ax.set_ylabel("Frequency")
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: "Rs.{:.0f}K".format(x/1000)))
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "05_order_value_distribution.png"))
plt.close()
print("  [5/7] Saved: order value distribution")

# 6. Revenue by City
fig, ax = plt.subplots(figsize=(10, 4))
city_rev = merged.groupby("city")["final_amount"].sum().sort_values(ascending=True)
ax.barh(city_rev.index, city_rev.values / 1e6,
        color=sns.color_palette("coolwarm", len(city_rev)))
ax.set_title("Total Revenue by City", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Revenue (Rs. Millions)")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "06_revenue_by_city.png"))
plt.close()
print("  [6/7] Saved: revenue by city")

# 7. Discount vs Revenue Heatmap
fig, ax = plt.subplots(figsize=(11, 5))
pivot = merged.pivot_table(values="final_amount", index="category",
                           columns="discount_pct", aggfunc="mean")
sns.heatmap(pivot / 1000, annot=True, fmt=".0f", cmap="YlGn",
            linewidths=0.4, ax=ax, cbar_kws={"label": "Avg Order Value (Rs.K)"})
ax.set_title("Avg Order Value Heatmap - Category x Discount %", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Discount %"); ax.set_ylabel("Category")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "07_category_discount_heatmap.png"))
plt.close()
print("  [7/7] Saved: category x discount heatmap")

print("\n-- Top 5 Revenue Categories --")
for cat, val in cat_rev.head(5).items():
    print("   {:<18} Rs.{:>10,.0f}".format(cat, val))

print("\n-- Revenue by Gender --")
for g, val in merged.groupby("gender")["final_amount"].sum().items():
    print("   {:<10} Rs.{:>10,.0f}".format(g, val))

print("\n  All charts saved to outputs/charts/")
print("  Run rfm_segmentation.py next.\n")
