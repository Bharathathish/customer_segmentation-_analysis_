"""
rfm_segmentation.py
RFM Scoring + K-Means Clustering - Customer Segmentation
Author : Bharath V
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
OUT_DIR    = os.path.join(BASE_DIR, "outputs")
os.makedirs(CHARTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.dpi": 130, "font.family": "DejaVu Sans"})

transactions = pd.read_csv(os.path.join(BASE_DIR, "data", "transactions.csv"))
transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])

SNAPSHOT = transactions["transaction_date"].max() + pd.Timedelta(days=1)

print("=" * 55)
print("  RFM SEGMENTATION + K-MEANS CLUSTERING")
print("=" * 55)

# ── RFM Calculation ───────────────────────────────────────────
rfm = transactions.groupby("customer_id").agg(
    recency   = ("transaction_date", lambda x: (SNAPSHOT - x.max()).days),
    frequency = ("transaction_id",   "count"),
    monetary  = ("final_amount",     "sum")
).reset_index()
rfm["monetary"] = rfm["monetary"].round(2)

# ── RFM Scoring (1-5) ─────────────────────────────────────────
rfm["R_score"] = pd.qcut(rfm["recency"],   q=5, labels=[5,4,3,2,1]).astype(int)
rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1,2,3,4,5]).astype(int)
rfm["M_score"] = pd.qcut(rfm["monetary"],  q=5, labels=[1,2,3,4,5]).astype(int)
rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

print("\n  RFM Table (top 10):")
print(rfm.head(10).to_string(index=False))

# ── K-Means Clustering ────────────────────────────────────────
features = rfm[["recency", "frequency", "monetary"]].copy()
scaler   = StandardScaler()
scaled   = scaler.fit_transform(features)

# Elbow method
inertias = []
sil_scores = []
K_range = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(scaled)
    inertias.append(km.inertia_)
    sil_scores.append(silhouette_score(scaled, km.labels_))

# Elbow chart
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(K_range, inertias, marker="o", linewidth=2, color="#2196F3")
axes[0].set_title("Elbow Method - Optimal K", fontweight="bold")
axes[0].set_xlabel("Number of Clusters (K)"); axes[0].set_ylabel("Inertia")
axes[1].plot(K_range, sil_scores, marker="s", linewidth=2, color="#E74C3C")
axes[1].set_title("Silhouette Score by K", fontweight="bold")
axes[1].set_xlabel("Number of Clusters (K)"); axes[1].set_ylabel("Silhouette Score")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "08_elbow_silhouette.png"))
plt.close()
print("\n  [1/5] Saved: elbow + silhouette chart")

# Final model with K=4
K = 4
km_final = KMeans(n_clusters=K, random_state=42, n_init=10)
rfm["cluster"] = km_final.fit_predict(scaled)

# Label clusters based on RFM mean
cluster_summary = rfm.groupby("cluster").agg(
    avg_recency   = ("recency",   "mean"),
    avg_frequency = ("frequency", "mean"),
    avg_monetary  = ("monetary",  "mean"),
    customer_count= ("customer_id","count")
).round(2)

# Auto-label clusters
labels_map = {}
sorted_by_monetary = cluster_summary["avg_monetary"].sort_values(ascending=False)
tier_labels = ["Champions", "Loyal Customers", "At Risk", "Lost / Inactive"]
for i, (cluster_id, _) in enumerate(sorted_by_monetary.items()):
    labels_map[cluster_id] = tier_labels[i]

rfm["segment"] = rfm["cluster"].map(labels_map)
cluster_summary["segment"] = cluster_summary.index.map(labels_map)

print("\n  Cluster Summary:")
print(cluster_summary.to_string())

# ── Segment distribution pie ──────────────────────────────────
seg_counts = rfm["segment"].value_counts()
seg_colors = ["#27AE60", "#2980B9", "#E67E22", "#E74C3C"]
fig, ax = plt.subplots(figsize=(7, 5))
wedges, texts, autotexts = ax.pie(
    seg_counts.values, labels=seg_counts.index,
    autopct="%1.1f%%", startangle=140,
    colors=seg_colors, pctdistance=0.82
)
for t in autotexts: t.set_fontsize(10)
ax.set_title("Customer Segment Distribution", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "09_segment_distribution.png"))
plt.close()
print("  [2/5] Saved: segment distribution pie")

# ── RFM box plots by segment ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
seg_order = ["Champions", "Loyal Customers", "At Risk", "Lost / Inactive"]
metrics   = ["recency", "frequency", "monetary"]
titles    = ["Recency (Days)", "Frequency (Orders)", "Monetary (Rs.)"]
pal       = {"Champions": "#27AE60", "Loyal Customers": "#2980B9",
             "At Risk": "#E67E22", "Lost / Inactive": "#E74C3C"}

for ax, metric, title in zip(axes, metrics, titles):
    sns.boxplot(data=rfm, x="segment", y=metric, order=seg_order,
                hue="segment", palette=pal, ax=ax, legend=False)
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(""); ax.tick_params(axis="x", rotation=20)
plt.suptitle("RFM Distribution by Segment", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "10_rfm_boxplots.png"), bbox_inches="tight")
plt.close()
print("  [3/5] Saved: RFM boxplots by segment")

# ── Scatter: Frequency vs Monetary colored by segment ────────
fig, ax = plt.subplots(figsize=(9, 6))
for seg, color in pal.items():
    sub = rfm[rfm["segment"] == seg]
    ax.scatter(sub["frequency"], sub["monetary"] / 1000,
               label=seg, alpha=0.65, s=40, color=color)
ax.set_title("Frequency vs Monetary by Segment", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Frequency (Orders)"); ax.set_ylabel("Monetary (Rs. Thousands)")
ax.legend(title="Segment")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "11_freq_vs_monetary.png"))
plt.close()
print("  [4/5] Saved: frequency vs monetary scatter")

# ── Revenue contribution by segment (80/20) ──────────────────
seg_rev = rfm.groupby("segment")["monetary"].sum().sort_values(ascending=False)
total   = seg_rev.sum()
seg_rev_pct = (seg_rev / total * 100).round(1)

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.barh(seg_rev.index, seg_rev.values / 1e6,
               color=[pal[s] for s in seg_rev.index])
ax.bar_label(bars, labels=["{:.1f}% of revenue".format(p) for p in seg_rev_pct.values],
             padding=5, fontsize=9)
ax.set_title("Revenue Contribution by Segment", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Total Revenue (Rs. Millions)")
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "12_revenue_by_segment.png"))
plt.close()
print("  [5/5] Saved: revenue contribution by segment")

# ── Export RFM table ──────────────────────────────────────────
rfm.to_csv(os.path.join(OUT_DIR, "rfm_segments.csv"), index=False)
print("\n  RFM segments exported -> outputs/rfm_segments.csv")

print("\n-- Revenue by Segment --")
for seg in seg_order:
    cnt = len(rfm[rfm["segment"] == seg])
    rev = rfm[rfm["segment"] == seg]["monetary"].sum()
    pct = rev / total * 100
    print("   {:<20} {:>4} customers   Rs.{:>10,.0f}  ({:.1f}%)".format(seg, cnt, rev, pct))

print("\n  Run sql_analysis.py next.\n")
