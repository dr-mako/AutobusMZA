# STEP 7 — GLOBAL VALIDATION ANALYSIS

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# PATHS
# =====================================================

base_dir = os.getcwd()

step6_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP6"
)

output_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP7"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

# =====================================================
# LOAD SUMMARY
# =====================================================

summary_file = os.path.join(
    step6_dir,
    "validation_summary.csv"
)

print()
print("===================================")
print("LOAD VALIDATION SUMMARY")
print("===================================")

summary_df = pd.read_csv(
    summary_file
)

print(summary_df)

# =====================================================
# GLOBAL METRICS
# =====================================================

print()
print("===================================")
print("GLOBAL METRICS")
print("===================================")

global_mae = summary_df["mae"].mean()
global_rmse = summary_df["rmse"].mean()
global_median = summary_df["median"].mean()
global_p95 = summary_df["p95"].mean()
global_max = summary_df["max"].max()

print(f"Global MAE     : {global_mae:.2f} s")
print(f"Global RMSE    : {global_rmse:.2f} s")
print(f"Global Median  : {global_median:.2f} s")
print(f"Global P95     : {global_p95:.2f} s")
print(f"Global Max     : {global_max:.2f} s")

# =====================================================
# SAVE GLOBAL METRICS
# =====================================================

global_metrics_df = pd.DataFrame({

    "metric": [
        "global_mae",
        "global_rmse",
        "global_median",
        "global_p95",
        "global_max"
    ],

    "value": [
        global_mae,
        global_rmse,
        global_median,
        global_p95,
        global_max
    ]
})

metrics_file = os.path.join(
    output_dir,
    "global_metrics.csv"
)

global_metrics_df.to_csv(
    metrics_file,
    index=False
)

print()
print("Zapisano:")
print(metrics_file)

# =====================================================
# RANKING
# =====================================================

print()
print("===================================")
print("TRIP RANKING")
print("===================================")

ranking_df = summary_df.sort_values(
    by="mae"
)

print(ranking_df[[
    "avl_trip",
    "rb_trip",
    "mae",
    "rmse",
    "confidence"
]])

ranking_file = os.path.join(
    output_dir,
    "trip_ranking.csv"
)

ranking_df.to_csv(
    ranking_file,
    index=False
)

print()
print("Zapisano:")
print(ranking_file)

# =====================================================
# BIAS CLASSIFICATION
# =====================================================

print()
print("===================================")
print("BIAS CLASSIFICATION")
print("===================================")

bias_class = []

for _, row in summary_df.iterrows():

    median = row["median"]

    if abs(median) < 5:

        cls = "UNBIASED"

    elif median > 5:

        cls = "POSITIVE_BIAS"

    else:

        cls = "NEGATIVE_BIAS"

    bias_class.append(cls)

summary_df["bias_class"] = bias_class

print(summary_df[[
    "avl_trip",
    "rb_trip",
    "median",
    "bias_class"
]])

bias_file = os.path.join(
    output_dir,
    "bias_classification.csv"
)

summary_df.to_csv(
    bias_file,
    index=False
)

print()
print("Zapisano:")
print(bias_file)

# =====================================================
# BARPLOT MAE
# =====================================================

print()
print("Plot MAE ranking...")

labels = []

for _, row in ranking_df.iterrows():

    label = (
        f"AVL{int(row['avl_trip'])}"
        f"-RB{int(row['rb_trip'])}"
    )

    labels.append(label)

plt.figure(figsize=(12, 6))

plt.bar(
    labels,
    ranking_df["mae"]
)

plt.ylabel("MAE [s]")
plt.xlabel("Matched trip")
plt.title("AVL reconstruction accuracy ranking")

plt.grid(True)

plot1 = os.path.join(
    output_dir,
    "mae_ranking.png"
)

plt.savefig(
    plot1,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print("Zapisano:")
print(plot1)

# =====================================================
# RMSE VS MAE
# =====================================================

print()
print("Plot RMSE vs MAE...")

plt.figure(figsize=(8, 8))

plt.scatter(
    summary_df["mae"],
    summary_df["rmse"]
)

for _, row in summary_df.iterrows():

    label = (
        f"A{int(row['avl_trip'])}"
        f"-R{int(row['rb_trip'])}"
    )

    plt.text(
        row["mae"],
        row["rmse"],
        label
    )

plt.xlabel("MAE [s]")
plt.ylabel("RMSE [s]")
plt.title("RMSE vs MAE")

plt.grid(True)

plot2 = os.path.join(
    output_dir,
    "rmse_vs_mae.png"
)

plt.savefig(
    plot2,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print("Zapisano:")
print(plot2)

# =====================================================
# CONFIDENCE DISTRIBUTION
# =====================================================

print()
print("Plot confidence distribution...")

confidence_counts = summary_df[
    "confidence"
].value_counts()

plt.figure(figsize=(8, 6))

plt.bar(
    confidence_counts.index,
    confidence_counts.values
)

plt.xlabel("Confidence")
plt.ylabel("Count")
plt.title("Matching confidence distribution")

plt.grid(True)

plot3 = os.path.join(
    output_dir,
    "confidence_distribution.png"
)

plt.savefig(
    plot3,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print("Zapisano:")
print(plot3)

# =====================================================
# SUMMARY TABLE
# =====================================================

summary_table = summary_df[[
    "avl_trip",
    "rb_trip",
    "confidence",
    "mae",
    "rmse",
    "median",
    "max",
    "p95",
    "bias_class"
]]

summary_table_file = os.path.join(
    output_dir,
    "summary_table.csv"
)

summary_table.to_csv(
    summary_table_file,
    index=False
)

print()
print("Zapisano:")
print(summary_table_file)

# =====================================================
# DONE
# =====================================================

print()
print("===================================")
print("STEP 7 COMPLETE")
print("===================================")


