# =====================================================
# step1_avl_trip_separator.py
#
# AVL ONLY
#
# MATLAB -> PYTHON
#
# 1:1 IMPLEMENTATION
#
# =====================================================

import os
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2

# =====================================================
# PARAMETRY
# =====================================================

BUS_NUMBER = "146"

MAX_STOP_DISTANCE = 120

MIN_TRIP_SAMPLES = 30

TRIM_SAMPLES = 8

# =====================================================
# ŚCIEŻKI
# =====================================================

base_dir = os.getcwd()

data_dir = os.path.join(
    base_dir,
    "DANE"
)

output_dir = os.path.join(
    base_dir,
    "OUTPUT"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

# =====================================================
# HAVERSINE
# =====================================================

def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c

# =====================================================
# TOPOLOGIA
# =====================================================

print()
print("===================================")
print("TOPOLOGIA")
print("===================================")

file_topology = os.path.join(
    data_dir,
    "stoptimes_146_DW_FAL.xlsx"
)

df_topology = pd.read_excel(
    file_topology
)

lat_stop = df_topology[
    "stop_lat"
].values

lon_stop = df_topology[
    "stop_lon"
].values

stop_sequence = df_topology[
    "stop_sequence"
].values

N_stops = len(stop_sequence)

print("Liczba przystanków:")
print(N_stops)

# =====================================================
# AVL
# =====================================================

print()
print("===================================")
print("AVL")
print("===================================")

pattern = os.path.join(
    data_dir,
    "MZA_*.csv"
)

file_path = glob.glob(pattern)[0]

print(file_path)

columns = [

    "line",
    "vehicle_nr",
    "brigade",
    "lat_raw",
    "lon_raw",
    "vehicle_time",
    "server_time"
]

df = pd.read_csv(

    file_path,

    sep=";",
    header=None,
    names=columns,

    encoding="utf-8",
    low_memory=False
)

# =====================================================
# GPS FIX
# =====================================================

def fix_coord(x):

    s = str(x)

    s = s.replace(".", "")
    s = s.replace(",", "")

    s = "".join(
        c for c in s
        if c.isdigit()
    )

    if len(s) < 6:

        return np.nan

    return float(
        s[:2] + "." + s[2:]
    )

df["lat"] = df["lat_raw"].apply(
    fix_coord
)

df["lon"] = df["lon_raw"].apply(
    fix_coord
)

# =====================================================
# CZAS
# =====================================================

df["vehicle_time"] = pd.to_datetime(

    df["vehicle_time"],

    errors="coerce"
)

# =====================================================
# FILTR
# =====================================================

df = df.dropna(

    subset=[

        "lat",
        "lon",
        "vehicle_time"
    ]
)

df = df[
    df["line"].astype(str) == BUS_NUMBER
]

# =====================================================
# AUTOBUSY REFERENCYJNE
# =====================================================

hour = df["vehicle_time"].dt.hour

idx_1845 = (

    (df["vehicle_nr"] == 1845)

    &

    (hour >= 15)

    &

    (hour < 19)
)

idx_7734 = (

    (df["vehicle_nr"] == 7734)

    &

    (
        (hour >= 19)
        |
        (hour <= 1)
    )
)

df = df[
    idx_1845 | idx_7734
]

# =====================================================
# SORTOWANIE
# =====================================================

df = df.sort_values(
    "vehicle_time"
)

df = df.reset_index(
    drop=True
)

# =====================================================
# SPEED
# =====================================================

N = len(df)

speed_kmh = np.zeros(N)

distance_m = np.zeros(N)

time_s = np.zeros(N)

for i in range(1, N):

    d = haversine(

        df.iloc[i-1]["lat"],
        df.iloc[i-1]["lon"],

        df.iloc[i]["lat"],
        df.iloc[i]["lon"]
    )

    distance_m[i] = d

    dt = (

        df.iloc[i]["vehicle_time"]
        -
        df.iloc[i-1]["vehicle_time"]

    ).total_seconds()

    time_s[i] = dt

    if dt > 0:

        speed_kmh[i] = (
            d / dt
        ) * 3.6

df["speed_kmh"] = speed_kmh

# =====================================================
# NEAREST STOP
# =====================================================

print()
print("Nearest stop assignment...")

nearest_stop_id = []

nearest_distance = []

for i in range(N):

    lat_bus = df.iloc[i]["lat"]

    lon_bus = df.iloc[i]["lon"]

    dist_all = []

    for j in range(N_stops):

        d = haversine(

            lat_bus,
            lon_bus,

            lat_stop[j],
            lon_stop[j]
        )

        dist_all.append(d)

    dist_all = np.array(dist_all)

    idx_min = np.argmin(dist_all)

    nearest_stop_id.append(
        stop_sequence[idx_min]
    )

    nearest_distance.append(
        dist_all[idx_min]
    )

df["nearest_stop_id"] = nearest_stop_id

df["nearest_distance_m"] = nearest_distance

# =====================================================
# FILTR ODLĘGŁOŚCI
# =====================================================

df.loc[
    df["nearest_distance_m"]
    >
    MAX_STOP_DISTANCE,

    "nearest_stop_id"

] = np.nan

# =====================================================
# DIRECTION
# =====================================================

dstop = df[
    "nearest_stop_id"
].diff()

direction = np.zeros(N)

for i in range(1, N):

    if dstop.iloc[i] > 0:

        direction[i] = 1

    elif dstop.iloc[i] < 0:

        direction[i] = -1

    else:

        direction[i] = direction[i-1]

df["direction"] = direction

# =====================================================
# SEGMENTACJA
# =====================================================

course_id = np.zeros(N)

course = 1

course_id[0] = course

for i in range(1, N):

    # -------------------------------------------------
    # ZMIANA KIERUNKU
    # -------------------------------------------------

    direction_change = (

        direction[i]
        !=
        direction[i-1]

    )

    valid_direction = (

        direction[i] != 0
        and
        direction[i-1] != 0
    )

    # -------------------------------------------------
    # ZMIANA AUTOBUSU
    # -------------------------------------------------

    vehicle_change = (

        df.iloc[i]["vehicle_nr"]

        !=

        df.iloc[i-1]["vehicle_nr"]
    )

    # -------------------------------------------------
    # NOWY KURS
    # -------------------------------------------------

    if (

        (direction_change and valid_direction)

        or

        vehicle_change
    ):

        course += 1

    course_id[i] = course

df["course_id"] = course_id

# =====================================================
# TRIM POSTOJÓW
# =====================================================

print()
print("Trim terminal dwell...")

cleaned = []

for course in sorted(
    df["course_id"].unique()
):

    trip_df = df[
        df["course_id"] == course
    ].copy()

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    first_stop = trip_df[
        "nearest_stop_id"
    ].iloc[0]

    start_idx = 0

    for i in range(len(trip_df)):

        s = trip_df[
            "nearest_stop_id"
        ].iloc[i]

        if s != first_stop:

            start_idx = max(
                0,
                i - TRIM_SAMPLES
            )

            break

    # -------------------------------------------------
    # END
    # -------------------------------------------------

    last_stop = trip_df[
        "nearest_stop_id"
    ].iloc[-1]

    end_idx = len(trip_df)

    for i in range(
        len(trip_df)-1,
        -1,
        -1
    ):

        s = trip_df[
            "nearest_stop_id"
        ].iloc[i]

        if s != last_stop:

            end_idx = min(
                len(trip_df),
                i + TRIM_SAMPLES
            )

            break

    trip_df = trip_df.iloc[
        start_idx:end_idx
    ]

    cleaned.append(trip_df)

df = pd.concat(
    cleaned,
    ignore_index=True
)

# =====================================================
# EXPORT CSV
# =====================================================

print()
print("Export CSV...")

summary_rows = []

for course in sorted(
    df["course_id"].unique()
):

    trip_df = df[
        df["course_id"] == course
    ]

    filename = (
        f"trip_{int(course):03d}.csv"
    )

    path = os.path.join(
        output_dir,
        filename
    )

    trip_df.to_csv(
        path,
        index=False
    )

    print("Zapisano:")
    print(path)

    summary_rows.append({

        "course_id":
        int(course),

        "start_time":
        trip_df[
            "vehicle_time"
        ].iloc[0],

        "end_time":
        trip_df[
            "vehicle_time"
        ].iloc[-1],

        "n_samples":
        len(trip_df),

        "start_stop":
        trip_df[
            "nearest_stop_id"
        ].iloc[0],

        "end_stop":
        trip_df[
            "nearest_stop_id"
        ].iloc[-1]
    })
    
# =====================================================
# SUMMARY
# =====================================================

df_summary = pd.DataFrame(
    summary_rows
)

summary_path = os.path.join(
    output_dir,
    "trip_summary.csv"
)

df_summary.to_csv(
    summary_path,
    index=False
)

print()
print(df_summary)

# =====================================================
# CONTROL PLOT
# =====================================================

print()
print("Control plot...")

plt.figure(figsize=(14, 6))

colors = plt.cm.tab10(
    np.linspace(
        0,
        1,
        int(df["course_id"].max())
    )
)

for i, course in enumerate(

    sorted(
        df["course_id"].unique()
    )
):

    trip_df = df[
        df["course_id"] == course
    ]

    plt.scatter(

        trip_df["vehicle_time"],

        trip_df["nearest_stop_id"],

        s=8,

        color=colors[i],

        label=f"Trip {int(course)}"
    )

plt.xlabel("Time")

plt.ylabel("Stop sequence")

plt.title(
    f"AVL trip segmentation | line {BUS_NUMBER}"
)

plt.grid(True)

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

plot_path = os.path.join(
    output_dir,
    "trip_segmentation.png"
)

plt.savefig(
    plot_path,
    dpi=300
)

plt.close()

print()
print("Zapisano:")
print(plot_path)

print()
print("DONE")