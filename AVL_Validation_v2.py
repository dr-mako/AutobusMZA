# AVL_Validation_v2.py


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

TARGET_BUS = 1845

MAX_SPEED_KMH = 120

INTERP_STEP_SEC = 1

MOVING_AVG_WINDOW = 5

# =====================================================

# HAVERSINE

# =====================================================

def haversine(lat1, lon1, lat2, lon2):


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

# WCZYTANIE MZA

# =====================================================

base_dir = os.getcwd()

data_dir = os.path.join(
base_dir,
"DANE"
)

pattern = os.path.join(
data_dir,
"MZA_*.csv"
)

files = glob.glob(pattern)

if not files:


    print("Brak plików MZA.")
    exit()


file_path = files[0]

print("Wczytywanie:")
print(file_path)

# =====================================================

# KOLUMNY

# =====================================================

columns = [
"line",
"vehicle_nr",
"brigade",
"lat",
"lon",
"vehicle_time",
"server_time"
]

# =====================================================

# READ CSV

# =====================================================

df = pd.read_csv(
file_path,
sep=";",
header=None,
names=columns,
encoding="utf-8",
low_memory=False
)

# =====================================================

# CZAS

# =====================================================

df["vehicle_time"] = pd.to_datetime(
df["vehicle_time"],
errors="coerce"
)

# =====================================================

# GPS

# =====================================================

df["lat"] = (
df["lat"]
.astype(str)
.str.replace(",", ".", regex=False)
)

df["lon"] = (
df["lon"]
.astype(str)
.str.replace(",", ".", regex=False)
)

df["lat"] = pd.to_numeric(
df["lat"],
errors="coerce"
)

df["lon"] = pd.to_numeric(
df["lon"],
errors="coerce"
)

# =====================================================

# CLEAN

# =====================================================

df = df.dropna(
subset=[
"lat",
"lon",
"vehicle_time"
]
)

# =====================================================

# SORT

# =====================================================

df = df.sort_values(
"vehicle_time"
)

df = df.reset_index(
drop=True
)

# =====================================================

# WYBÓR AUTOBUSU

# =====================================================

df_bus = df[
df["vehicle_nr"] == TARGET_BUS
].copy()

df_bus = df_bus.sort_values(
"vehicle_time"
)

df_bus = df_bus.reset_index(
drop=True
)

print("\n===================================")
print(f"AUTOBUS: {TARGET_BUS}")
print("===================================")

print("Liczba rekordów:")
print(len(df_bus))

# =====================================================

# DISTANCE + SPEED

# =====================================================

distances = [0]

speeds = [0]

for i in range(1, len(df_bus)):


    lat1 = df_bus.iloc[i - 1]["lat"]
    lon1 = df_bus.iloc[i - 1]["lon"]

    lat2 = df_bus.iloc[i]["lat"]
    lon2 = df_bus.iloc[i]["lon"]

    d = haversine(
        lat1,
        lon1,
        lat2,
        lon2
    )

    dt = (
        df_bus.iloc[i]["vehicle_time"]
        -
        df_bus.iloc[i - 1]["vehicle_time"]
    ).total_seconds()

    if dt <= 0:

        speed = 0

    else:

        speed = (d / dt) * 3.6

    distances.append(d)

    speeds.append(speed)


df_bus["distance_m"] = distances

df_bus["speed_kmh"] = speeds

# =====================================================

# FILTR GPS OUTLIERÓW

# =====================================================

before = len(df_bus)

df_bus = df_bus[
df_bus["speed_kmh"]
< MAX_SPEED_KMH
].copy()

after = len(df_bus)

print("\nUsunięto outlierów:")
print(before - after)

# =====================================================

# RESET INDEX

# =====================================================

df_bus = df_bus.reset_index(
drop=True
)

# =====================================================

# CZAS RELATYWNY

# =====================================================

t0 = df_bus["vehicle_time"].iloc[0]

df_bus["time_s"] = (
df_bus["vehicle_time"]
-
t0
).dt.total_seconds()

# =====================================================

# UNIQUE TIME

# =====================================================

df_bus = df_bus.drop_duplicates(
subset="time_s"
)

df_bus = df_bus.reset_index(
drop=True
)

# =====================================================
# SEGMENTACJA AVL
# =====================================================

df_bus["dt"] = (
    df_bus["vehicle_time"]
    .diff()
    .dt.total_seconds()
)

# nowy segment gdy luka > 30 s
SEGMENT_GAP = 120

df_bus["new_segment"] = (
    df_bus["dt"] > SEGMENT_GAP
)

df_bus["segment_id"] = (
    df_bus["new_segment"]
    .cumsum()
)

print("\n===================================")
print("SEGMENTY AVL")
print("===================================")

print(
    "Liczba segmentów:",
    df_bus["segment_id"].nunique()
)

# =====================================================
# INTERPOLACJA SEGMENTÓW
# =====================================================

interp_all = []

for segment_id, seg_df in df_bus.groupby(
    "segment_id"
):

    # -------------------------------------------------
    # małe segmenty pomijamy
    # -------------------------------------------------

    if len(seg_df) < 5:
        continue

    seg_df = seg_df.sort_values(
        "vehicle_time"
    )

    seg_df = seg_df.reset_index(
        drop=True
    )

    # -------------------------------------------------
    # czas lokalny
    # -------------------------------------------------

    t0 = seg_df["vehicle_time"].iloc[0]

    seg_df["time_s"] = (
        seg_df["vehicle_time"]
        - t0
    ).dt.total_seconds()

    # -------------------------------------------------
    # interpolacja 1 s
    # -------------------------------------------------

    time_interp = np.arange(
        0,
        seg_df["time_s"].max(),
        1
    )

    lat_interp = np.interp(
        time_interp,
        seg_df["time_s"],
        seg_df["lat"]
    )

    lon_interp = np.interp(
        time_interp,
        seg_df["time_s"],
        seg_df["lon"]
    )

    # -------------------------------------------------
    # czas rzeczywisty
    # -------------------------------------------------

    vehicle_time_interp = (
        t0
        +
        pd.to_timedelta(
            time_interp,
            unit="s"
        )
    )

    # -------------------------------------------------
    # dataframe
    # -------------------------------------------------

    # globalny czas od początku dnia
    global_time_s = (
        vehicle_time_interp - df_bus["vehicle_time"].iloc[0]
    ).total_seconds()

    df_interp_seg = pd.DataFrame({

        "segment_id":
        segment_id,

        "time_s":
        global_time_s,

        "vehicle_time":
        vehicle_time_interp,

        "lat":
        lat_interp,

        "lon":
        lon_interp
    })

    interp_all.append(
        df_interp_seg
    )

# =====================================================
# ŁĄCZENIE SEGMENTÓW
# =====================================================

df_interp = pd.concat(
    interp_all,
    ignore_index=True
)

# =====================================================
# SPEED
# =====================================================

interp_speeds = [0]

for i in range(1, len(df_interp)):

    same_segment = (
        df_interp.iloc[i]["segment_id"]
        ==
        df_interp.iloc[i - 1]["segment_id"]
    )

    # nowy segment
    if not same_segment:

        interp_speeds.append(0)
        continue

    lat1 = df_interp.iloc[i - 1]["lat"]
    lon1 = df_interp.iloc[i - 1]["lon"]

    lat2 = df_interp.iloc[i]["lat"]
    lon2 = df_interp.iloc[i]["lon"]

    d = haversine(
        lat1,
        lon1,
        lat2,
        lon2
    )

    dt = (
        df_interp.iloc[i]["vehicle_time"]
        -
        df_interp.iloc[i - 1]["vehicle_time"]
    ).total_seconds()

    if dt <= 0:
        speed = 0
    else:
        speed = (d / dt) * 3.6

    interp_speeds.append(speed)

df_interp["speed_kmh"] = interp_speeds

# =====================================================
# INFO
# =====================================================

print("\n===================================")
print("INTERPOLACJA")
print("===================================")

print("Punkty oryginalne:")
print(len(df_bus))

print("Punkty po interpolacji:")
print(len(df_interp))

# =====================================================
# DETEKCJA POSTOJÓW
# =====================================================

STOP_SPEED = 2

df_interp["is_stop"] = (
    df_interp["speed_kmh"]
    < STOP_SPEED
)

# grupy postoju
df_interp["stop_group"] = (
    df_interp["is_stop"]
    !=
    df_interp["is_stop"].shift()
).cumsum()

# =====================================================
# ANALIZA POSTOJÓW
# =====================================================

print("\n===================================")
print("POSTOJE")
print("===================================")

MIN_STOP_TIME = 60

stop_segments = []

for group_id, group_df in df_interp.groupby(
    "stop_group"
):

    is_stop = group_df["is_stop"].iloc[0]

    if not is_stop:
        continue

    start_time = (
        group_df["vehicle_time"]
        .iloc[0]
    )

    end_time = (
        group_df["vehicle_time"]
        .iloc[-1]
    )

    duration = (
        end_time - start_time
    ).total_seconds()

    if duration >= MIN_STOP_TIME:

        lat_mean = (
            group_df["lat"]
            .mean()
        )

        lon_mean = (
            group_df["lon"]
            .mean()
        )

        stop_segments.append([
            start_time,
            end_time,
            duration,
            lat_mean,
            lon_mean
        ])

        print("-----------------------------------")
        print("START:", start_time)
        print("END:", end_time)
        print(
            "Duration [min]:",
            round(duration / 60, 1)
        )

# =====================================================
# DATAFRAME POSTOJÓW
# =====================================================

df_stops = pd.DataFrame(
    stop_segments,
    columns=[
        "start_time",
        "end_time",
        "duration_s",
        "lat",
        "lon"
    ]
)

print("\nWykryto postojów:")
print(len(df_stops))

# =====================================================
# SEGMENTACJA PO DŁUGIM POSTOJU
# =====================================================

MIN_TERMINAL_STOP = 600  # 10 min

df_interp["new_trip"] = False

for i in range(1, len(df_interp)):

    prev_speed = df_interp.iloc[i - 1]["speed_kmh"]
    curr_speed = df_interp.iloc[i]["speed_kmh"]

    prev_time = df_interp.iloc[i - 1]["vehicle_time"]
    curr_time = df_interp.iloc[i]["vehicle_time"]

    dt = (
        curr_time - prev_time
    ).total_seconds()

    # ciągły postój
    if (
        prev_speed < STOP_SPEED
        and
        curr_speed < STOP_SPEED
    ):

        if dt >= MIN_TERMINAL_STOP:

            df_interp.loc[
                df_interp.index[i],
                "new_trip"
            ] = True

# ID kursu
df_interp["trip_id"] = (
    df_interp["new_trip"]
    .cumsum()
)

# =====================================================
# MAPA POSTOJÓW
# =====================================================

plt.figure(figsize=(10, 10))

# trajektoria
plt.plot(
    df_interp["lon"],
    df_interp["lat"],
    linewidth=1,
    alpha=0.5
)

# postoje
plt.scatter(
    df_stops["lon"],
    df_stops["lat"],
    s=120,
    c="red",
    label="Stops"
)

for i in range(len(df_stops)):

    plt.text(
        df_stops.iloc[i]["lon"],
        df_stops.iloc[i]["lat"],
        str(i),
        fontsize=8
    )

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    f"Detected Stops | Bus {TARGET_BUS}"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.savefig(
    f"detected_stops_bus_{TARGET_BUS}.png",
    dpi=300
)

plt.close()

print("\nZapisano:")
print(
    f"detected_stops_bus_{TARGET_BUS}.png"
)


# =====================================================

# WYKRES TRAJEKTORII

# =====================================================

plt.figure(figsize=(10, 10))

# oryginalne AVL

plt.scatter(
df_bus["lon"],
df_bus["lat"],
s=10,
label="AVL Original"
)

# interpolacja

plt.plot(
df_interp["lon"],
df_interp["lat"],
linewidth=1,
label="AVL Interpolated"
)

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.title(
f"AVL Interpolation | Bus {TARGET_BUS}"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

filename = (
f"avl_interpolation_bus_{TARGET_BUS}.png"
)

plt.savefig(
filename,
dpi=300
)

plt.close()

print("\nZapisano:")
print(filename)

# =====================================================

# WYKRES PRĘDKOŚCI

# =====================================================

plt.figure(figsize=(14, 5))

plt.plot(
df_interp["time_s"] / 60,
df_interp["speed_kmh"],
linewidth=1
)

plt.xlabel("Time [min]")

plt.ylabel("Speed [km/h]")

plt.title(
f"Interpolated Speed | Bus {TARGET_BUS}"
)

plt.grid(True)

plt.tight_layout()

filename = (
f"speed_interpolation_bus_{TARGET_BUS}.png"
)

plt.savefig(
filename,
dpi=300
)

plt.close()

print("Zapisano:")
print(filename)

print("\nDONE")
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

