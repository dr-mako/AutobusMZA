# Race_vs_MZA.py

import os
import glob

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# WCZYTANIE PLIKU
# =====================================================

base_dir = os.getcwd()

data_dir = os.path.join(base_dir, "DANE")

pattern = os.path.join(data_dir, "RaceBox_*.csv")

files = glob.glob(pattern)

file_path = files[0]

print("Wczytywanie:")
print(file_path)

df = pd.read_csv(file_path)

# =====================================================
# CZAS
# =====================================================

df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

df = df.dropna(subset=["Time", "Speed"])

df = df.sort_values("Time")

df = df.reset_index(drop=True)

t0 = df["Time"].iloc[0]

df["Time_s"] = (
    df["Time"] - t0
).dt.total_seconds()

# =====================================================
# WYKRYWANIE NOWYCH KURSÓW
# =====================================================

# różnica czasu między próbkami
df["dt"] = df["Time_s"].diff()

# nowy kurs gdy przerwa > 5 s
threshold = 5

df["new_trip"] = df["dt"] > threshold

# numer kursu
df["trip_id"] = df["new_trip"].cumsum()

# =====================================================
# INFO
# =====================================================

n_trips = df["trip_id"].nunique()

print("\nWykryto kursów:", n_trips)

# =====================================================
# RYSOWANIE
# =====================================================

for trip_id, trip_df in df.groupby("trip_id"):

    # pomijaj bardzo krótkie segmenty
    if len(trip_df) < 50:
        continue

    plt.figure(figsize=(12, 5))

    plt.plot(
        trip_df["Time_s"] - trip_df["Time_s"].iloc[0],
        trip_df["Speed"],
        linewidth=1
    )

    plt.xlabel("Time [s]")
    plt.ylabel("Speed [km/h]")

    plt.title(f"Trip {trip_id}")

    plt.grid(True)

    plt.tight_layout()

    filename = f"trip_{trip_id}.png"

    plt.savefig(filename, dpi=300)

    plt.close()

    print("Zapisano:", filename)

print("\nDONE")


#import os
#import glob

#import pandas as pd

# =====================================================
# MZA
# =====================================================

print("\n===================================")
print("MZA")
print("===================================")

pattern = os.path.join(data_dir, "MZA_*.csv")

files = glob.glob(pattern)

if not files:
    print("Nie znaleziono plików MZA.")
    exit()

file_path = files[0]

print("Wczytywanie:")
print(file_path)

# =====================================================
# POPRAWNE KOLUMNY
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
# WCZYTANIE
# =====================================================

df_mza = pd.read_csv(
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

df_mza["vehicle_time"] = pd.to_datetime(
    df_mza["vehicle_time"],
    errors="coerce"
)

df_mza["server_time"] = pd.to_datetime(
    df_mza["server_time"],
    errors="coerce"
)

# =====================================================
# GPS
# =====================================================

df_mza["lat"] = (
    df_mza["lat"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

df_mza["lon"] = (
    df_mza["lon"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

df_mza["lat"] = pd.to_numeric(
    df_mza["lat"],
    errors="coerce"
)

df_mza["lon"] = pd.to_numeric(
    df_mza["lon"],
    errors="coerce"
)

# =====================================================
# CZYSZCZENIE
# =====================================================

df_mza = df_mza.dropna(
    subset=[
        "lat",
        "lon",
        "vehicle_time"
    ]
)

# =====================================================
# SORTOWANIE
# =====================================================

df_mza = df_mza.sort_values(
    "vehicle_time"
)

df_mza = df_mza.reset_index(
    drop=True
)

# =====================================================
# INFO
# =====================================================

print("\nLiczba rekordów:")
print(len(df_mza))

print("\nLinie:")
print(sorted(df_mza["line"].unique()))

print("\nLiczba autobusów:")
print(df_mza["vehicle_nr"].nunique())

print("\nAutobusy:")
print(sorted(df_mza["vehicle_nr"].unique()))

print("\nBrygady:")
print(sorted(df_mza["brigade"].unique()))

# =====================================================
# TYLKO AUTOBUSY REFERENCYJNE
# =====================================================

reference_buses = [
    1845,
    7734
]

df_ref = df_mza[
    df_mza["vehicle_nr"].isin(reference_buses)
].copy()

print("\n===================================")
print("AUTOBUSY REFERENCYJNE")
print("===================================")

print(
    sorted(
        df_ref["vehicle_nr"].unique()
    )
)

print("\nLiczba rekordów:")
print(len(df_ref))

# =====================================================
# BRYGADY
# =====================================================

brigades = sorted(
    df_ref["brigade"].unique()
)

print("\nBrygady referencyjne:")
print(brigades)

# =====================================================
# ANALIZA BRYGAD
# =====================================================

# =====================================================
# ANALIZA BRYGAD + AUTOBUSÓW
# =====================================================

groups = df_ref.groupby(
    ["vehicle_nr", "brigade"]
)

for (vehicle_nr, brigade), df_brigade in groups:

    print("\n===================================")
    print(f"AUTOBUS: {vehicle_nr}")
    print(f"BRYGADA: {brigade}")
    print("===================================")

    # kopia
    df_brigade = df_brigade.copy()

    # sortowanie czasu
    df_brigade = df_brigade.sort_values(
        "vehicle_time"
    )

    # reset indeksu
    df_brigade = df_brigade.reset_index(
        drop=True
    )
    # =================================================
    # WYKRES GPS
    # =================================================

    plt.figure(figsize=(8, 8))

    plt.plot(
        df_brigade["lon"],
        df_brigade["lat"],
        linewidth=1
    )

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    vehicle_nr = (
        df_brigade["vehicle_nr"]
        .iloc[0]
    )

    plt.title(
        f"Bus {vehicle_nr} | Brigade {brigade}"
    )

    plt.grid(True)

    plt.tight_layout()

    filename = (
        f"bus_{vehicle_nr}_brigade_{brigade}.png"
    )

    plt.savefig(filename, dpi=300)

    plt.close()

    print("Zapisano:", filename)

print("\nDONE")

 # =====================================================
# OVERLAY RaceBox vs MZA
# =====================================================

# ZAŁOŻENIA:
# RaceBox -> df_race
# MZA      -> df_ref
#
# autobus:
# 1845 lub 7734
#
# przykładowo:
TARGET_BUS = 1845

# =====================================================
# WYBÓR AUTOBUSU MZA
# =====================================================

df_bus = df_ref[
    df_ref["vehicle_nr"] == TARGET_BUS
].copy()

df_bus = df_bus.sort_values(
    "vehicle_time"
)

df_bus = df_bus.reset_index(
    drop=True
)

print("\n===================================")
print(f"MZA BUS: {TARGET_BUS}")
print("===================================")

print("Liczba rekordów:",
      len(df_bus))

# =====================================================
# FILTR GPS OUTLIERÓW
# =====================================================

from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2

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
# FILTR ABSURDALNYCH SKOKÓW
# =====================================================

MAX_SPEED = 120

before = len(df_bus)

df_bus = df_bus[
    df_bus["speed_kmh"] < MAX_SPEED
].copy()

after = len(df_bus)

print("\nUsunięto outlierów:",
      before - after)

# =====================================================
# WYKRYWANIE KURSÓW AVL
# POSTÓJ > 5 MIN
# =====================================================

# różnica czasu
df_bus["dt"] = (
    df_bus["vehicle_time"]
    .diff()
    .dt.total_seconds()
)

# mały ruch GPS
STOP_SPEED = 2

# postój
df_bus["is_stop"] = (
    df_bus["speed_kmh"]
    < STOP_SPEED
)

# czas ciągłego postoju
stop_groups = (
    df_bus["is_stop"]
    !=
    df_bus["is_stop"].shift()
).cumsum()

df_bus["stop_group"] = stop_groups

# =====================================================
# NOWE KURSY
# =====================================================

df_bus["new_trip"] = False

MIN_STOP_TIME = 300  # 5 min

for group_id, group_df in df_bus.groupby(
    "stop_group"
):

    is_stop = (
        group_df["is_stop"]
        .iloc[0]
    )

    if not is_stop:
        continue

    duration = (
        group_df["vehicle_time"].iloc[-1]
        -
        group_df["vehicle_time"].iloc[0]
    ).total_seconds()

    if duration >= MIN_STOP_TIME:

        idx = group_df.index[-1]

        df_bus.loc[
            idx,
            "new_trip"
        ] = True

# =====================================================
# NUMER KURSU
# =====================================================

df_bus["trip_id_avl"] = (
    df_bus["new_trip"]
    .cumsum()
)

# =====================================================
# INFO
# =====================================================

n_avl_trips = (
    df_bus["trip_id_avl"]
    .nunique()
)

print("\nWykryto kursów AVL:",
      n_avl_trips)

print("\nAVL TRIPS")

for trip_id, trip_df in df_bus.groupby(
    "trip_id_avl"
):

    start_time = (
        trip_df["vehicle_time"]
        .min()
    )

    end_time = (
        trip_df["vehicle_time"]
        .max()
    )

    duration_min = (
        end_time - start_time
    ).total_seconds() / 60

    print(
        f"\nTrip {trip_id}"
    )

    print(
        "START:",
        start_time
    )

    print(
        "END:",
        end_time
    )

    print(
        "Duration [min]:",
        round(duration_min, 1)
    )

    print(
        "Points:",
        len(trip_df)
    )

# =====================================================
# INFO
# =====================================================

n_avl_trips = (
    df_bus["trip_id_avl"]
    .nunique()
)

print("\nWykryto kursów AVL:",
      n_avl_trips)

print("\nLiczba punktów w kursach:")

for trip_id, trip_df in df_bus.groupby(
    "trip_id_avl"
):

    print(
        f"Trip {trip_id}:",
        len(trip_df)
    )

# =====================================================
# RACEBOX
# =====================================================

# UWAGA:
# tutaj zakładamy że:
# df = RaceBox dataframe

df_race = df.copy()

# =====================================================
# OVERLAY
# =====================================================

plt.figure(figsize=(10, 10))

# RaceBox
plt.plot(
    df_race["Longitude"],
    df_race["Latitude"],
    linewidth=1,
    label="RaceBox"
)

# MZA
plt.scatter(
    df_bus["lon"],
    df_bus["lat"],
    s=10,
    label="MZA AVL"
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    f"Trajectory Overlay | Bus {TARGET_BUS}"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.savefig(
    f"overlay_bus_{TARGET_BUS}.png",
    dpi=300
)

plt.close()

print("\nZapisano:")
print(f"overlay_bus_{TARGET_BUS}.png")

# =====================================================
# OVERLAY RaceBox TRIP vs MZA AVL TRIP
# =====================================================

# -----------------------------------------------------
# WYBÓR KURSÓW
# -----------------------------------------------------

TARGET_TRIP = 0
TARGET_BUS = 1845
TARGET_AVL_TRIP = 7

# =====================================================
# RACEBOX TRIP
# =====================================================

df_race_trip = df[
    df["trip_id"] == TARGET_TRIP
].copy()

df_race_trip = df_race_trip.sort_values(
    "Time"
)

df_race_trip = df_race_trip.reset_index(
    drop=True
)

print("\n===================================")
print(f"RACEBOX TRIP: {TARGET_TRIP}")
print("===================================")

print("Liczba punktów:",
      len(df_race_trip))

# =====================================================
# MZA AVL TRIP
# =====================================================

df_bus_trip = df_bus[
    df_bus["trip_id_avl"]
    == TARGET_AVL_TRIP
].copy()

df_bus_trip = df_bus_trip.sort_values(
    "vehicle_time"
)

df_bus_trip = df_bus_trip.reset_index(
    drop=True
)

print("\n===================================")
print(f"MZA BUS: {TARGET_BUS}")
print(f"AVL TRIP: {TARGET_AVL_TRIP}")
print("===================================")

print("Liczba punktów:",
      len(df_bus_trip))

# =====================================================
# OVERLAY
# =====================================================

plt.figure(figsize=(10, 10))

# -----------------------------------------------------
# RaceBox
# -----------------------------------------------------

plt.plot(
    df_race_trip["Longitude"],
    df_race_trip["Latitude"],
    linewidth=2,
    label=f"RaceBox Trip {TARGET_TRIP}"
)

# START RaceBox
plt.scatter(
    df_race_trip["Longitude"].iloc[0],
    df_race_trip["Latitude"].iloc[0],
    s=120,
    marker="o",
    label="RaceBox START"
)

# END RaceBox
plt.scatter(
    df_race_trip["Longitude"].iloc[-1],
    df_race_trip["Latitude"].iloc[-1],
    s=120,
    marker="x",
    label="RaceBox END"
)

# -----------------------------------------------------
# MZA AVL
# -----------------------------------------------------

plt.scatter(
    df_bus_trip["lon"],
    df_bus_trip["lat"],
    s=15,
    label=f"MZA AVL Trip {TARGET_AVL_TRIP}"
)

# START AVL
plt.scatter(
    df_bus_trip["lon"].iloc[0],
    df_bus_trip["lat"].iloc[0],
    s=120,
    marker="o",
    label="MZA START"
)

# END AVL
plt.scatter(
    df_bus_trip["lon"].iloc[-1],
    df_bus_trip["lat"].iloc[-1],
    s=120,
    marker="x",
    label="MZA END"
)

# =====================================================
# OPIS
# =====================================================

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    f"Overlay | RaceBox Trip {TARGET_TRIP} vs AVL Trip {TARGET_AVL_TRIP}"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

filename = (
    f"overlay_trip_{TARGET_TRIP}_avl_{TARGET_AVL_TRIP}.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("\nZapisano:")
print(filename)

# =====================================================
# PORÓWNANIE CZASU
# =====================================================

print("\n===================================")
print("RACEBOX CZAS")
print("===================================")

print(
    df_race_trip["Time"].min()
)

print(
    df_race_trip["Time"].max()
)

print("\n===================================")
print("MZA AVL CZAS")
print("===================================")

print(
    df_bus_trip["vehicle_time"].min()
)

print(
    df_bus_trip["vehicle_time"].max()
)

# =====================================================
# USUNIĘCIE STREFY CZASOWEJ Z RACEBOX
# =====================================================

df_race_trip["Time"] = (
    df_race_trip["Time"]
    .dt.tz_localize(None)
)

# =====================================================
# SHIFT CZASU
# =====================================================

time_shift = (
    df_bus_trip["vehicle_time"].iloc[0]
    -
    df_race_trip["Time"].iloc[0]
)

print("\n===================================")
print("SHIFT CZASU")
print("===================================")

print(time_shift)

# =====================================================
# CZASY WSZYSTKICH AVL TRIPÓW
# =====================================================

print("\n===================================")
print("AVL TRIPS")
print("===================================")

for trip_id, trip_df in df_bus.groupby(
    "trip_id_avl"
):

    start_time = (
        trip_df["vehicle_time"]
        .min()
    )

    end_time = (
        trip_df["vehicle_time"]
        .max()
    )

    duration_min = (
        end_time - start_time
    ).total_seconds() / 60

    print(
        f"Trip {trip_id}"
    )

    print(
        "START:",
        start_time
    )

    print(
        "END:",
        end_time
    )

    print(
        "Duration [min]:",
        round(duration_min, 1)
    )

    print(
        "Points:",
        len(trip_df)
    )

    print("-----------------------------------")

# =====================================================
# SYNCHRONIZACJA CZASU
# =====================================================

# RaceBox bez timezone
race_start = (
    df_race_trip["Time"]
    .iloc[0]
    .tz_localize(None)
)

# AVL start
avl_start = (
    df_bus_trip["vehicle_time"]
    .iloc[0]
)

# shift
time_shift = (
    avl_start - race_start
)

print("\n===================================")
print("TIME SHIFT")
print("===================================")

print(time_shift)

# =====================================================
# NOWY CZAS RaceBox
# =====================================================

df_race_trip["Time_sync"] = (
    df_race_trip["Time"]
    .dt.tz_localize(None)
    +
    time_shift
)

# =====================================================
# PODGLĄD
# =====================================================

print("\n===================================")
print("SYNC CHECK")
print("===================================")

print(
    "RaceBox START:",
    df_race_trip["Time_sync"].min()
)

print(
    "RaceBox END:",
    df_race_trip["Time_sync"].max()
)

print()

print(
    "AVL START:",
    df_bus_trip["vehicle_time"].min()
)

print(
    "AVL END:",
    df_bus_trip["vehicle_time"].max()
)

# =====================================================
# WSPÓLNY ZAKRES CZASU
# =====================================================

start_time = max(
    df_race_trip["Time_sync"].min(),
    df_bus_trip["vehicle_time"].min()
)

end_time = min(
    df_race_trip["Time_sync"].max(),
    df_bus_trip["vehicle_time"].max()
)

print("\n===================================")
print("COMMON TIME WINDOW")
print("===================================")

print(start_time)
print(end_time)

# =====================================================
# FILTR CZASU
# =====================================================

df_race_common = df_race_trip[
    (
        df_race_trip["Time_sync"]
        >= start_time
    )
    &
    (
        df_race_trip["Time_sync"]
        <= end_time
    )
].copy()

df_bus_common = df_bus_trip[
    (
        df_bus_trip["vehicle_time"]
        >= start_time
    )
    &
    (
        df_bus_trip["vehicle_time"]
        <= end_time
    )
].copy()

print("\nRaceBox common:",
      len(df_race_common))

print("AVL common:",
      len(df_bus_common))

# =====================================================
# NEAREST TIME MATCHING
# =====================================================

matched_distances = []

# =====================================================
# ITERACJA AVL
# =====================================================

for i in range(len(df_bus_common)):

    avl_time = (
        df_bus_common.iloc[i]["vehicle_time"]
    )

    # różnice czasu
    time_diff = (
        df_race_common["Time_sync"]
        -
        avl_time
    ).abs()

    # najbliższy punkt RaceBox
    idx = time_diff.idxmin()

    race_point = df_race_common.loc[idx]

    # =================================================
    # AVL
    # =================================================

    lat_avl = (
        df_bus_common.iloc[i]["lat"]
    )

    lon_avl = (
        df_bus_common.iloc[i]["lon"]
    )

    # =================================================
    # RaceBox
    # =================================================

    lat_race = (
        race_point["Latitude"]
    )

    lon_race = (
        race_point["Longitude"]
    )

    # =================================================
    # DYSTANS
    # =================================================

    d = haversine(
        lat_avl,
        lon_avl,
        lat_race,
        lon_race
    )

    matched_distances.append(d)

# =====================================================
# WYNIKI
# =====================================================

matched_distances = np.array(
    matched_distances
)

print("\n===================================")
print("AVL vs RACEBOX")
print("===================================")

print(
    "Mean error [m]:",
    round(
        matched_distances.mean(),
        2
    )
)

print(
    "Median error [m]:",
    round(
        np.median(
            matched_distances
        ),
        2
    )
)

print(
    "95 percentile [m]:",
    round(
        np.percentile(
            matched_distances,
            95
        ),
        2
    )
)

print(
    "Max error [m]:",
    round(
        matched_distances.max(),
        2
    )
)

# =====================================================
# SPATIAL NEAREST MATCHING
# =====================================================

spatial_distances = []

# =====================================================
# ITERACJA AVL
# =====================================================

for i in range(len(df_bus_common)):

    lat_avl = (
        df_bus_common.iloc[i]["lat"]
    )

    lon_avl = (
        df_bus_common.iloc[i]["lon"]
    )

    distances = []

    # -------------------------------------------------
    # wszystkie punkty RaceBox
    # -------------------------------------------------

    for j in range(len(df_race_common)):

        lat_race = (
            df_race_common.iloc[j]["Latitude"]
        )

        lon_race = (
            df_race_common.iloc[j]["Longitude"]
        )

        d = haversine(
            lat_avl,
            lon_avl,
            lat_race,
            lon_race
        )

        distances.append(d)

    # najbliższy punkt
    min_d = min(distances)

    spatial_distances.append(min_d)

# =====================================================
# WYNIKI
# =====================================================

spatial_distances = np.array(
    spatial_distances
)

print("\n===================================")
print("SPATIAL AVL vs RACEBOX")
print("===================================")

print(
    "Mean spatial error [m]:",
    round(
        spatial_distances.mean(),
        2
    )
)

print(
    "Median spatial error [m]:",
    round(
        np.median(
            spatial_distances
        ),
        2
    )
)

print(
    "95 percentile [m]:",
    round(
        np.percentile(
            spatial_distances,
            95
        ),
        2
    )
)

print(
    "Max spatial error [m]:",
    round(
        spatial_distances.max(),
        2
    )
)