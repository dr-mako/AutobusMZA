# =====================================================
# AVL TRIP SEGMENTATION
# FULL TOPOLOGY CROSSING
# =====================================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# PATHS
# =====================================================

base_dir = os.getcwd()

input_path = os.path.join(
    base_dir,
    "OUTPUT",
    "candidate_projection.csv"
)

output_dir = os.path.join(
    base_dir,
    "OUTPUT",
    "AVL_TRIPS"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

# =====================================================
# LOAD
# =====================================================

print()
print("===================================")
print("LOAD")
print("===================================")

print(input_path)

df = pd.read_csv(
    input_path
)

# =====================================================
# TIME
# =====================================================

df["vehicle_time"] = pd.to_datetime(
    df["vehicle_time"]
)

# =====================================================
# DETECT TOPOLOGY COLUMN
# =====================================================

possible_columns = [

    "matched_stop_index",
    "topology_index",
    "candidate_1_index",
    "global_stop_index"

]

matched_column = None

for col in possible_columns:

    if col in df.columns:

        matched_column = col
        break

if matched_column is None:

    print()
    print("BRAK KOLUMNY TOPOLOGII")
    exit()

print()
print("TOPOLOGY COLUMN:")
print(matched_column)

# =====================================================
# SIGNAL
# =====================================================

signal_raw = df[
    matched_column
].values.astype(float)

# =====================================================
# SMOOTHING
# =====================================================

signal = pd.Series(
    signal_raw
).rolling(
    window=11,
    center=True,
    min_periods=1
).median().values

# =====================================================
# GLOBAL RANGE
# =====================================================

TOP_MIN = np.nanmin(signal)
TOP_MAX = np.nanmax(signal)

print()
print("TOPOLOGY RANGE:")
print(TOP_MIN, TOP_MAX)

# =====================================================
# THRESHOLDS
# =====================================================

LOW_THRESHOLD = TOP_MIN + 5
HIGH_THRESHOLD = TOP_MAX - 5

MIN_TRIP_SAMPLES = 250

# =====================================================
# STATES
# =====================================================

WAITING = 0
GOING_UP = 1
GOING_DOWN = 2

state = WAITING

trip_id = 0

trip_ids = np.full(
    len(df),
    -1
)

trip_start = 0

# =====================================================
# INITIAL DIRECTION
# =====================================================

if signal[0] <= LOW_THRESHOLD:

    state = GOING_UP

elif signal[0] >= HIGH_THRESHOLD:

    state = GOING_DOWN

# =====================================================
# MAIN LOOP
# =====================================================

for i in range(1, len(signal)):

    current = signal[i]

    trip_ids[i] = trip_id

    # =================================================
    # GOING UP
    # =================================================

    if state == GOING_UP:

        # reached upper terminal
        if current >= HIGH_THRESHOLD:

            # enough samples
            if i - trip_start >= MIN_TRIP_SAMPLES:

                trip_id += 1
                trip_start = i

            state = GOING_DOWN

    # =================================================
    # GOING DOWN
    # =================================================

    elif state == GOING_DOWN:

        # reached lower terminal
        if current <= LOW_THRESHOLD:

            # enough samples
            if i - trip_start >= MIN_TRIP_SAMPLES:

                trip_id += 1
                trip_start = i

            state = GOING_UP

# =====================================================
# SAVE
# =====================================================

df["trip_id"] = trip_ids

# =====================================================
# REMOVE INVALID
# =====================================================

df = df[
    df["trip_id"] >= 0
].copy()

# =====================================================
# SUMMARY
# =====================================================

summary = []

unique_trips = sorted(
    df["trip_id"].unique()
)

# =====================================================
# SAVE TRIPS
# =====================================================

for trip in unique_trips:

    df_trip = df[
        df["trip_id"] == trip
    ].copy()

    # =============================================
    # FILTER
    # =============================================

    if len(df_trip) < MIN_TRIP_SAMPLES:

        continue

    # =============================================
    # SAVE CSV
    # =============================================

    trip_path = os.path.join(
        output_dir,
        f"trip_{trip:03d}.csv"
    )

    df_trip.to_csv(
        trip_path,
        index=False
    )

    print()
    print("Zapisano:")
    print(trip_path)

    # =============================================
    # SUMMARY
    # =============================================

    summary.append({

        "trip_id":
            trip,

        "start_time":
            df_trip["vehicle_time"].iloc[0],

        "end_time":
            df_trip["vehicle_time"].iloc[-1],

        "duration_min":
            (
                df_trip["vehicle_time"].iloc[-1]
                -
                df_trip["vehicle_time"].iloc[0]
            ).total_seconds() / 60,

        "samples":
            len(df_trip),

        "start_topology":
            df_trip[matched_column].iloc[0],

        "end_topology":
            df_trip[matched_column].iloc[-1]

    })

# =====================================================
# SUMMARY DF
# =====================================================

df_summary = pd.DataFrame(
    summary
)

# =====================================================
# PRINT
# =====================================================

print()
print("===================================")
print("TRIP SUMMARY")
print("===================================")

print(df_summary)

# =====================================================
# SAVE SUMMARY
# =====================================================

summary_path = os.path.join(
    base_dir,
    "OUTPUT",
    "trip_summary.csv"
)

df_summary.to_csv(
    summary_path,
    index=False
)

print()
print("Zapisano:")
print(summary_path)

# =====================================================
# PLOT
# =====================================================

plt.figure(
    figsize=(18, 8)
)

for trip in unique_trips:

    df_trip = df[
        df["trip_id"] == trip
    ]

    if len(df_trip) < MIN_TRIP_SAMPLES:

        continue

    plt.plot(
        df_trip.index,
        df_trip[matched_column],
        linewidth=2,
        label=f"Trip {trip}"
    )

# =====================================================
# THRESHOLDS
# =====================================================

plt.axhline(
    LOW_THRESHOLD,
    color="green",
    linestyle="--",
    alpha=0.5
)

plt.axhline(
    HIGH_THRESHOLD,
    color="red",
    linestyle="--",
    alpha=0.5
)

# =====================================================
# FIGURE
# =====================================================

plt.title(
    "Trip segmentation from topological signal"
)

plt.xlabel(
    "AVL sample"
)

plt.ylabel(
    "Topology index"
)

plt.grid(True)

plt.legend()

plot_path = os.path.join(
    base_dir,
    "OUTPUT",
    "trip_segmentation_from_topology.png"
)

plt.savefig(
    plot_path,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Zapisano:")
print(plot_path)

plt.show()

print()
print("DONE")