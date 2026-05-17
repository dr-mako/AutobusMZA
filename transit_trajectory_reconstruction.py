# =====================================================
# transit_trajectory_reconstruction.py
#
# ETAP 1
# REFERENCYJNA TOPOLOGIA LINII
# =====================================================

# pipeline
'''
AVL GPS
↓
candidate generation
↓
direction locking
↓
topological graph constraints
↓
monotonic state progression
↓
gap filling
↓
synthetic stop reconstruction
'''


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

from scipy.spatial.distance import cdist

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
# PARAMETRY
# =====================================================

LINE_ID = "146"

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
# WYSZUKIWANIE PLIKÓW
# =====================================================

pattern_1 = os.path.join(
    data_dir,
    f"stoptimes_{LINE_ID}_DW_FAL.xlsx"
)

pattern_2 = os.path.join(
    data_dir,
    f"stoptimes_{LINE_ID}_FAL_DW.xlsx"
)

files_1 = glob.glob(pattern_1)
files_2 = glob.glob(pattern_2)

if not files_1:

    print("Brak pliku DW_FAL")
    exit()

if not files_2:

    print("Brak pliku FAL_DW")
    exit()

file_dw_fal = files_1[0]
file_fal_dw = files_2[0]

# =====================================================
# WCZYTANIE
# =====================================================

print("\n===================================")
print("WCZYTYWANIE TOPOLOGII")
print("===================================")

print(file_dw_fal)
print(file_fal_dw)

df_dw_fal = pd.read_excel(
    file_dw_fal
)

df_fal_dw = pd.read_excel(
    file_fal_dw
)

# =====================================================
# INFO
# =====================================================

print("\n===================================")
print("DW -> FAL")
print("===================================")

print(df_dw_fal.head())

print("\nKolumny:")
print(df_dw_fal.columns.tolist())

print("\nLiczba przystanków:")
print(len(df_dw_fal))

print("\n===================================")
print("FAL -> DW")
print("===================================")

print(df_fal_dw.head())

print("\nKolumny:")
print(df_fal_dw.columns.tolist())

print("\nLiczba przystanków:")
print(len(df_fal_dw))

# =====================================================
# NORMALIZACJA KOLUMN
# =====================================================

rename_dict = {

    "stop_lat": "lat",
    "stop_lon": "lon"

}

df_dw_fal = df_dw_fal.rename(
    columns=rename_dict
)

df_fal_dw = df_fal_dw.rename(
    columns=rename_dict
)

# =====================================================
# PRZECINKI DZIESIĘTNE
# =====================================================

for col in [
    "lat",
    "lon",
    "shape_dist_traveled"
]:

    df_dw_fal[col] = (
        df_dw_fal[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    df_fal_dw[col] = (
        df_fal_dw[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    df_dw_fal[col] = pd.to_numeric(
        df_dw_fal[col],
        errors="coerce"
    )

    df_fal_dw[col] = pd.to_numeric(
        df_fal_dw[col],
        errors="coerce"
    )

# =====================================================
# BASE STOP NAME
# =====================================================

df_dw_fal["base_stop_name"] = (
    df_dw_fal["stop_name"]
    .str.replace(
        r"\s+\d+$",
        "",
        regex=True
    )
)

df_fal_dw["base_stop_name"] = (
    df_fal_dw["stop_name"]
    .str.replace(
        r"\s+\d+$",
        "",
        regex=True
    )
)

# =====================================================
# DIRECTION ID
# =====================================================

df_dw_fal["direction"] = "DW_FAL"

df_fal_dw["direction"] = "FAL_DW"

df_dw_fal["direction_id"] = 0

df_fal_dw["direction_id"] = 1

# =====================================================
# GLOBAL INDEX
# =====================================================

df_dw_fal = df_dw_fal.reset_index(
    drop=True
)

df_fal_dw = df_fal_dw.reset_index(
    drop=True
)

df_dw_fal["global_stop_index"] = np.arange(
    0,
    len(df_dw_fal)
)

df_fal_dw["global_stop_index"] = np.arange(
    len(df_dw_fal),
    len(df_dw_fal) + len(df_fal_dw)
)

# =====================================================
# ŁĄCZENIE
# =====================================================

df_topology = pd.concat(
    [
        df_dw_fal,
        df_fal_dw
    ],
    ignore_index=True
)

# =====================================================
# INFO TOPOLOGII
# =====================================================

print("\n===================================")
print("TOPOLOGIA REFERENCYJNA")
print("===================================")

print("\nŁączna liczba punktów:")
print(len(df_topology))

print("\nZakres latitude:")

print(
    df_topology["lat"].min(),
    "->",
    df_topology["lat"].max()
)

print("\nZakres longitude:")

print(
    df_topology["lon"].min(),
    "->",
    df_topology["lon"].max()
)

# =====================================================
# DUPLIKATY STOP_ID
# =====================================================

duplicates = (
    df_topology["stop_id"]
    .duplicated()
    .sum()
)

print("\nDuplikaty stop_id:")
print(duplicates)

# =====================================================
# WALIDACJA TOPOLOGII
# =====================================================

print("\n===================================")
print("WALIDACJA TOPOLOGII")
print("===================================")

# =====================================================
# DUPLIKATY STOP_ID
# =====================================================

duplicates_df = df_topology[
    df_topology["stop_id"]
    .duplicated(keep=False)
]

if len(duplicates_df) > 0:

    print("\nDuplikaty stop_id:")

    print(
        duplicates_df[
            [
                "direction",
                "stop_sequence",
                "stop_id",
                "stop_name"
            ]
        ]
    )

else:

    print("\nBrak duplikatów stop_id")

# =====================================================
# FUNKCJA ANALIZY KIERUNKU
# =====================================================

def topology_validation(
    df_direction,
    direction_name
):

    print("\n-----------------------------------")
    print(direction_name)
    print("-----------------------------------")

    gps_distances = []

    shape_distances = []

    ratios = []

    rows = []

    for i in range(
        1,
        len(df_direction)
    ):

        # ---------------------------------------------
        # punkt poprzedni
        # ---------------------------------------------

        lat1 = df_direction.iloc[i - 1]["lat"]
        lon1 = df_direction.iloc[i - 1]["lon"]

        # ---------------------------------------------
        # punkt następny
        # ---------------------------------------------

        lat2 = df_direction.iloc[i]["lat"]
        lon2 = df_direction.iloc[i]["lon"]

        # ---------------------------------------------
        # dystans GPS
        # ---------------------------------------------

        gps_d = haversine(
            lat1,
            lon1,
            lat2,
            lon2
        )

        # ---------------------------------------------
        # shape distance
        # ---------------------------------------------

        shape1 = df_direction.iloc[i - 1][
            "shape_dist_traveled"
        ]

        shape2 = df_direction.iloc[i][
            "shape_dist_traveled"
        ]

        shape_d = (
            shape2 - shape1
        ) * 1000

        # ---------------------------------------------
        # ratio
        # ---------------------------------------------

        if shape_d > 0:

            ratio = gps_d / shape_d

        else:

            ratio = np.nan

        gps_distances.append(gps_d)

        shape_distances.append(shape_d)

        ratios.append(ratio)

        rows.append({

            "seq_A":
            df_direction.iloc[i - 1][
                "stop_sequence"
            ],

            "seq_B":
            df_direction.iloc[i][
                "stop_sequence"
            ],

            "stop_A":
            df_direction.iloc[i - 1][
                "stop_name"
            ],

            "stop_B":
            df_direction.iloc[i][
                "stop_name"
            ],

            "gps_distance_m":
            gps_d,

            "shape_distance_m":
            shape_d,

            "ratio":
            ratio
        })

    # =================================================
    # DATAFRAME
    # =================================================

    df_validation = pd.DataFrame(rows)

    # =================================================
    # STATYSTYKI
    # =================================================

    print("\nGPS distance mean [m]:")

    print(
        round(
            np.mean(gps_distances),
            1
        )
    )

    print("\nShape distance mean [m]:")

    print(
        round(
            np.mean(shape_distances),
            1
        )
    )

    print("\nGPS/Shape ratio mean:")

    print(
        round(
            np.nanmean(ratios),
            3
        )
    )

    # =================================================
    # ANOMALIE
    # =================================================

    anomalies = df_validation[
        (
            df_validation["ratio"]
            > 1.2
        )
        |
        (
            df_validation["ratio"]
            < 0.1
        )
    ]

    print("\nLiczba anomalii:")

    print(len(anomalies))

    if len(anomalies) > 0:

        print("\nAnomalie:")

        print(
            anomalies[
                [
                    "seq_A",
                    "seq_B",
                    "stop_A",
                    "stop_B",
                    "gps_distance_m",
                    "shape_distance_m",
                    "ratio"
                ]
            ]
        )

    # =================================================
    # HISTOGRAM
    # =================================================

    plt.figure(figsize=(10, 5))

    plt.hist(
        ratios,
        bins=20
    )

    plt.xlabel(
        "GPS / Shape ratio"
    )

    plt.ylabel(
        "Count"
    )

    plt.title(
        f"Topology validation | {direction_name}"
    )

    plt.grid(True)

    plt.tight_layout()

    filename = os.path.join(
        output_dir,
        f"topology_validation_{direction_name}.png"
    )

    plt.savefig(
        filename,
        dpi=300
    )

    plt.close()

    print("\nZapisano:")
    print(filename)

    # =================================================
    # CSV
    # =================================================

    csv_filename = os.path.join(
        output_dir,
        f"topology_validation_{direction_name}.csv"
    )

    df_validation.to_csv(
        csv_filename,
        index=False
    )

    print("\nZapisano:")
    print(csv_filename)

# =====================================================
# ANALIZA DW -> FAL
# =====================================================

topology_validation(
    df_dw_fal,
    "DW_FAL"
)

# =====================================================
# ANALIZA FAL -> DW
# =====================================================

topology_validation(
    df_fal_dw,
    "FAL_DW"
)

# =====================================================
# MAPA TOPOLOGII
# =====================================================

plt.figure(figsize=(12, 12))

# =====================================================
# DW -> FAL
# =====================================================

plt.plot(
    df_dw_fal["lon"],
    df_dw_fal["lat"],
    linewidth=2,
    marker="o",
    label="DW -> FAL"
)

# numeracja
for i in range(len(df_dw_fal)):

    plt.text(
        df_dw_fal.iloc[i]["lon"],
        df_dw_fal.iloc[i]["lat"],
        str(
            df_dw_fal.iloc[i]["stop_sequence"]
        ),
        fontsize=7
    )

# =====================================================
# FAL -> DW
# =====================================================

plt.plot(
    df_fal_dw["lon"],
    df_fal_dw["lat"],
    linewidth=2,
    marker="o",
    label="FAL -> DW"
)

# numeracja
for i in range(len(df_fal_dw)):

    plt.text(
        df_fal_dw.iloc[i]["lon"],
        df_fal_dw.iloc[i]["lat"],
        str(
            df_fal_dw.iloc[i]["stop_sequence"]
        ),
        fontsize=7
    )

# =====================================================
# OPIS
# =====================================================

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.title(
    f"Reference topology | Line {LINE_ID}"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

filename = os.path.join(
    output_dir,
    f"topology_map_line_{LINE_ID}.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("\nZapisano:")
print(filename)

# =====================================================
# ZAPIS CSV
# =====================================================

csv_filename = os.path.join(
    output_dir,
    f"reference_topology_line_{LINE_ID}.csv"
)

df_topology.to_csv(
    csv_filename,
    index=False
)

print("\nZapisano:")
print(csv_filename)

# =====================================================
# PODGLĄD
# =====================================================

print("\n===================================")
print("PODGLĄD TOPOLOGII")
print("===================================")

print(
    df_topology[
        [
            "global_stop_index",
            "direction",
            "stop_sequence",
            "stop_id",
            "stop_name",
            "base_stop_name"
        ]
    ].head(20)
)

print("\nDONE")


# =====================================================
# ETAP 1.5
# WCZYTANIE AVL
# =====================================================

pattern = os.path.join(
    data_dir,
    "MZA_*.csv"
)

files = glob.glob(pattern)

if not files:

    print("Brak plików AVL.")
    exit()

file_path = files[0]

print("\n===================================")
print("WCZYTYWANIE AVL")
print("===================================")

print(file_path)

columns = [
    "line",
    "vehicle_nr",
    "brigade",
    "lat",
    "lon",
    "vehicle_time",
    "server_time"
]

df_avl = pd.read_csv(
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

df_avl["vehicle_time"] = pd.to_datetime(
    df_avl["vehicle_time"],
    errors="coerce"
)

# =====================================================
# GPS
# =====================================================

df_avl["lat"] = (
    df_avl["lat"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

df_avl["lon"] = (
    df_avl["lon"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

df_avl["lat"] = pd.to_numeric(
    df_avl["lat"],
    errors="coerce"
)

df_avl["lon"] = pd.to_numeric(
    df_avl["lon"],
    errors="coerce"
)

# =====================================================
# CLEAN
# =====================================================

df_avl = df_avl.dropna(
    subset=[
        "lat",
        "lon",
        "vehicle_time"
    ]
)

# =====================================================
# SORT
# =====================================================

df_avl = df_avl.sort_values(
    "vehicle_time"
)

df_avl = df_avl.reset_index(
    drop=True
)

# =====================================================
# WYBÓR AUTOBUSU
# =====================================================

TARGET_BUS = 1845

df_bus = df_avl[
    df_avl["vehicle_nr"]
    == TARGET_BUS
].copy()

df_bus = df_bus.reset_index(
    drop=True
)

print("\n===================================")
print("AVL")
print("===================================")

print("Liczba rekordów:")
print(len(df_bus))

# =====================================================
# SPEED
# =====================================================

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

    speeds.append(speed)

df_bus["speed_kmh"] = speeds

# =====================================================
# TYMCZASOWE df_interp
# =====================================================

df_interp = df_bus.copy()


# =====================================================
# ETAP 2A
# HIDDEN MARKOV STYLE RECONSTRUCTION
# =====================================================



# =====================================================
# PARAMETRY HMM
# =====================================================

N_CANDIDATES = 3

GPS_SIGMA_M = 60

MAX_TRANSITION_JUMP = 3

# =====================================================
# TOPOLOGY ARRAY
# =====================================================

stop_coords = df_topology[
    [
        "lat",
        "lon"
    ]
].values

stop_indices = df_topology[
    "global_stop_index"
].values

stop_names = df_topology[
    "stop_name"
].values

stop_directions = df_topology[
    "direction"
].values

stop_progress = df_topology[
    "shape_dist_traveled"
].values


# =====================================================
# TYMCZASOWO:
# użyj oryginalnego AVL zamiast df_interp
# =====================================================

df_interp = df_bus.copy()

# =====================================================
# AVL ARRAY
# =====================================================

avl_coords = df_interp[
    [
        "lat",
        "lon"
    ]
].values

# =====================================================
# DISTANCE MATRIX
# =====================================================

print("\n===================================")
print("DISTANCE MATRIX")
print("===================================")

n_avl = len(avl_coords)

n_stop = len(stop_coords)

D = np.zeros(
    (
        n_avl,
        n_stop
    )
)

for i in range(n_avl):

    lat1 = avl_coords[i, 0]

    lon1 = avl_coords[i, 1]

    for j in range(n_stop):

        lat2 = stop_coords[j, 0]

        lon2 = stop_coords[j, 1]

        D[i, j] = haversine(
            lat1,
            lon1,
            lat2,
            lon2
        )

print("Macierz odległości:")
print(D.shape)

# =====================================================
# CANDIDATE STOPS
# =====================================================

candidate_rows = []

for i in range(n_avl):

    distances = D[i]

    candidate_idx = np.argsort(
        distances
    )[:N_CANDIDATES]

    row = {

        "vehicle_time":
        df_interp.iloc[i]["vehicle_time"],

        "lat":
        df_interp.iloc[i]["lat"],

        "lon":
        df_interp.iloc[i]["lon"],

        "speed_kmh":
        df_interp.iloc[i]["speed_kmh"]
    }

    # -------------------------------------------------
    # kandydaci
    # -------------------------------------------------

    for k, idx in enumerate(candidate_idx):

        row[
            f"candidate_{k+1}_index"
        ] = stop_indices[idx]

        row[
            f"candidate_{k+1}_name"
        ] = stop_names[idx]

        row[
            f"candidate_{k+1}_direction"
        ] = stop_directions[idx]

        row[
            f"candidate_{k+1}_dist_m"
        ] = distances[idx]

        row[
            f"candidate_{k+1}_progress"
        ] = stop_progress[idx]

    candidate_rows.append(row)

# =====================================================
# DATAFRAME
# =====================================================

df_candidates = pd.DataFrame(
    candidate_rows
)

# =====================================================
# EMISSION PROBABILITY
# =====================================================

print("\n===================================")
print("EMISSION PROBABILITIES")
print("===================================")

for k in range(N_CANDIDATES):

    d_col = (
        f"candidate_{k+1}_dist_m"
    )

    p_col = (
        f"candidate_{k+1}_emission"
    )

    d = df_candidates[d_col]

    p = np.exp(
        -(d ** 2)
        /
        (2 * GPS_SIGMA_M ** 2)
    )

    df_candidates[p_col] = p

print(df_candidates.head())

# =====================================================
# KIERUNEK CHWILOWY
# =====================================================

direction_sequence = []

for i in range(len(df_candidates)):

    c1 = df_candidates.iloc[i][
        "candidate_1_index"
    ]

    if i == 0:

        direction_sequence.append(
            "UNKNOWN"
        )

        continue

    prev = df_candidates.iloc[i - 1][
        "candidate_1_index"
    ]

    if c1 > prev:

        direction_sequence.append(
            "FORWARD"
        )

    elif c1 < prev:

        direction_sequence.append(
            "BACKWARD"
        )

    else:

        direction_sequence.append(
            "STOP"
        )

df_candidates[
    "topology_direction"
] = direction_sequence

# =====================================================
# TOPOLOGY PROGRESS
# =====================================================

df_candidates[
    "topology_progress"
] = df_candidates[
    "candidate_1_progress"
]

# =====================================================
# WIZUALIZACJA TOPOLOGY PROGRESS
# =====================================================

plt.figure(figsize=(14, 5))

plt.plot(
    df_candidates[
        "topology_progress"
    ],
    linewidth=1
)

plt.xlabel("AVL sample")

plt.ylabel(
    "Topology progress [km]"
)

plt.title(
    "Topology Progress Reconstruction"
)

plt.grid(True)

plt.tight_layout()

filename = os.path.join(
    output_dir,
    "topology_progress_reconstruction.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("\nZapisano:")
print(filename)

# =====================================================
# MAPA CANDIDATE MATCHING
# =====================================================

plt.figure(figsize=(10, 10))

# AVL

plt.plot(
    df_interp["lon"],
    df_interp["lat"],
    linewidth=1,
    alpha=0.5,
    label="AVL"
)

# topology

plt.scatter(
    df_topology["lon"],
    df_topology["lat"],
    s=40,
    c="red",
    label="Topology"
)

# candidate matches

step = 100

for i in range(
    0,
    len(df_candidates),
    step
):

    stop_idx = int(
        df_candidates.iloc[i][
            "candidate_1_index"
        ]
    )

    stop_lon = df_topology.iloc[
        stop_idx
    ]["lon"]

    stop_lat = df_topology.iloc[
        stop_idx
    ]["lat"]

    plt.plot(
        [
            df_candidates.iloc[i]["lon"],
            stop_lon
        ],
        [
            df_candidates.iloc[i]["lat"],
            stop_lat
        ],
        linewidth=0.5,
        alpha=0.3
    )

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.title(
    "AVL → Topology Candidate Projection"
)

plt.grid(True)

plt.legend()

plt.tight_layout()

filename = os.path.join(
    output_dir,
    "candidate_projection_map.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("Zapisano:")
print(filename)

# =====================================================
# CSV EXPORT
# =====================================================

filename = os.path.join(
    output_dir,
    "candidate_projection.csv"
)

df_candidates.to_csv(
    filename,
    index=False
)

print("Zapisano:")
print(filename)

print("\nDONE")

# =====================================================
# SPRAWDZENIE KOLUMN
# =====================================================

print("\n===================================")
print("DF CANDIDATES COLUMNS")
print("===================================")

print(df_candidates.columns.tolist())

# =====================================================
# HMM / TOPOLOGICAL TRANSITION MODEL
# =====================================================

print("\n===================================")
print("TOPOLOGICAL TRANSITION MODEL")
print("===================================")

# -----------------------------------------------------
# PARAMETRY
# -----------------------------------------------------

MAX_INDEX_JUMP = 3

BACKWARD_PENALTY = 1000

DISTANCE_WEIGHT = 1.0

TRANSITION_WEIGHT = 2.0

# -----------------------------------------------------
# START
# -----------------------------------------------------

best_path = []

# pierwszy punkt
current_index = int(
    df_candidates.iloc[0][
        "candidate_1_index"
    ]
)

best_path.append(current_index)

# -----------------------------------------------------
# ITERACJA
# -----------------------------------------------------

for i in range(1, len(df_candidates)):

    prev_index = best_path[-1]

    candidate_indices = [

        int(
            df_candidates.iloc[i][
                "candidate_1_index"
            ]
        ),

        int(
            df_candidates.iloc[i][
                "candidate_2_index"
            ]
        ),

        int(
            df_candidates.iloc[i][
                "candidate_3_index"
            ]
        )
    ]

    candidate_distances = [

    df_candidates.iloc[i][
            "candidate_1_dist_m"
        ],

        df_candidates.iloc[i][
            "candidate_2_dist_m"
        ],

        df_candidates.iloc[i][
            "candidate_3_dist_m"
        ]
    ]

    costs = []

    # -------------------------------------------------
    # OCENA KANDYDATÓW
    # -------------------------------------------------

    for cand_idx, cand_dist in zip(
        candidate_indices,
        candidate_distances
    ):

        # różnica indeksów
        delta = cand_idx - prev_index

        # koszt odległości
        distance_cost = (
            cand_dist
            * DISTANCE_WEIGHT
        )

        # koszt przejścia
        transition_cost = 0

        # cofanie
        if delta < 0:

            transition_cost += (
                BACKWARD_PENALTY
            )

        # zbyt duży skok
        if abs(delta) > MAX_INDEX_JUMP:

            transition_cost += (
                abs(delta)
                * 100
            )

        total_cost = (
            distance_cost
            +
            transition_cost
        )

        costs.append(total_cost)

    # -------------------------------------------------
    # WYBÓR
    # -------------------------------------------------

    best_candidate = np.argmin(costs)

    best_index = candidate_indices[
        best_candidate
    ]

    best_path.append(best_index)

# =====================================================
# ZAPIS ŚCIEŻKI
# =====================================================

df_candidates[
    "matched_stop_index"
] = best_path

# =====================================================
# MATCHED TOPOLOGY
# =====================================================

matched_stop_names = []

matched_directions = []

matched_stop_ids = []

for idx in best_path:

    row = df_topology.iloc[idx]

    matched_stop_names.append(
        row["stop_name"]
    )

    matched_directions.append(
        row["direction"]
    )

    matched_stop_ids.append(
        row["stop_id"]
    )

df_candidates[
    "matched_stop_name"
] = matched_stop_names

df_candidates[
    "matched_direction"
] = matched_directions

df_candidates[
    "matched_stop_id"
] = matched_stop_ids

# =====================================================
# PODGLĄD
# =====================================================

print(df_candidates[[

    "vehicle_time",

    "matched_stop_index",

    "matched_stop_name",

    "matched_direction"

]].head(20))

# =====================================================
# WYKRES INDEKSU TOPOLOGICZNEGO
# =====================================================

plt.figure(figsize=(16, 6))

plt.plot(

    df_candidates.index,

    df_candidates[
        "matched_stop_index"
    ],

    linewidth=1
)

plt.xlabel("AVL sample")

plt.ylabel("Matched stop index")

plt.title(
    "Topological trajectory reconstruction"
)

plt.grid(True)

plt.tight_layout()

filename = os.path.join(

    output_dir,

    "topological_reconstruction.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("\nZapisano:")
print(filename)

# =====================================================
# MAP MATCHING
# =====================================================

plt.figure(figsize=(10, 10))

# AVL
plt.scatter(

    df_candidates["lon"],
    df_candidates["lat"],

    s=5,

    alpha=0.3,

    label="AVL"
)

# topology
plt.plot(

    df_topology["lon"],
    df_topology["lat"],

    linewidth=2,

    alpha=0.7,

    label="Topology"
)

# matched
matched_lon = []
matched_lat = []

for idx in best_path:

    matched_lon.append(
        df_topology.iloc[idx]["lon"]
    )

    matched_lat.append(
        df_topology.iloc[idx]["lat"]
    )

plt.plot(

    matched_lon,
    matched_lat,

    linewidth=1,

    label="Matched path"
)

plt.legend()

plt.xlabel("Longitude")

plt.ylabel("Latitude")

plt.title(
    "Transit trajectory reconstruction"
)

plt.grid(True)

plt.tight_layout()

filename = os.path.join(

    output_dir,

    "matched_trajectory.png"
)

plt.savefig(
    filename,
    dpi=300
)

plt.close()

print("Zapisano:")
print(filename)

print("\nDONE")

# =====================================================
# GRAPH CONSTRAINED TOPOLOGICAL RECONSTRUCTION
# =====================================================

print()
print("===================================")
print("GRAPH CONSTRAINED RECONSTRUCTION")
print("===================================")

# =====================================================
# BUILD TOPOLOGY GRAPH
# =====================================================

topology_graph = {}

# -------------------------------------------------
# DW -> FAL
# -------------------------------------------------

df_dir_1 = df_topology[
    df_topology["direction"] == "DW_FAL"
]

dir1_indices = df_dir_1.index.tolist()

for i in range(len(dir1_indices)):

    current_idx = dir1_indices[i]

    allowed_states = [current_idx]

    if i + 1 < len(dir1_indices):
        allowed_states.append(
            dir1_indices[i + 1]
        )

    if i + 2 < len(dir1_indices):
        allowed_states.append(
            dir1_indices[i + 2]
        )

    topology_graph[current_idx] = allowed_states

# -------------------------------------------------
# FAL -> DW
# -------------------------------------------------

df_dir_2 = df_topology[
    df_topology["direction"] == "FAL_DW"
]

dir2_indices = df_dir_2.index.tolist()

for i in range(len(dir2_indices)):

    current_idx = dir2_indices[i]

    allowed_states = [current_idx]

    if i + 1 < len(dir2_indices):
        allowed_states.append(
            dir2_indices[i + 1]
        )

    if i + 2 < len(dir2_indices):
        allowed_states.append(
            dir2_indices[i + 2]
        )

    topology_graph[current_idx] = allowed_states

# -------------------------------------------------
# LOOP CONNECTIONS
# -------------------------------------------------

if 39 in topology_graph:
    topology_graph[39].append(40)

if 79 in topology_graph:
    topology_graph[79].append(0)

print()
print("Topology graph created")

print()
print("Example transitions:")

for k in list(topology_graph.keys())[:10]:

    print(
        k,
        "->",
        topology_graph[k]
    )

# =====================================================
# DETECT INITIAL DIRECTION
# =====================================================

direction_votes = []

for i_init in range(30):

    idx_test = int(
        df_candidates.iloc[i_init][
            "candidate_1_index"
        ]
    )

    direction_test = df_topology.iloc[
        idx_test
    ]["direction"]

    if direction_test in [
        "DW_FAL",
        "FAL_DW"
    ]:

        direction_votes.append(
            direction_test
        )

# =====================================================
# MAJORITY VOTE
# =====================================================

initial_direction = max(
    set(direction_votes),
    key=direction_votes.count
)

print()
print("LOCKED DIRECTION:")
print(initial_direction)

# =====================================================
# DETECT INITIAL STATE
# =====================================================

initial_candidates = []

for i_init in range(30):

    candidate_idx = int(
        df_candidates.iloc[i_init][
            "candidate_1_index"
        ]
    )

    candidate_direction = df_topology.iloc[
        candidate_idx
    ]["direction"]

    if candidate_direction == initial_direction:

        initial_candidates.append(
            candidate_idx
        )

initial_state = int(
    np.median(initial_candidates)
)

print()
print("INITIAL STATE:")
print(initial_state)

# =====================================================
# GRAPH CONSTRAINED MATCHING
# =====================================================

matched_indices_graph = []

prev_state = initial_state

for i in range(len(df_candidates)):

    candidates = []

    for c in [1, 2, 3]:

        idx_col = f"candidate_{c}_index"

        dist_col = f"candidate_{c}_dist_m"

        candidate_idx = int(
            df_candidates.iloc[i][idx_col]
        )

        candidate_dist = float(
            df_candidates.iloc[i][dist_col]
        )

        candidate_direction = df_topology.iloc[
            candidate_idx
        ]["direction"]

        # =============================================
        # HARD DIRECTION LOCK
        # =============================================

        if candidate_direction != initial_direction:

            continue

        candidates.append(
            (
                candidate_idx,
                candidate_dist
            )
        )

    # -------------------------------------------------
    # brak kandydatów
    # -------------------------------------------------

    if len(candidates) == 0:

        continue

    # -------------------------------------------------
    # FIRST SAMPLE
    # -------------------------------------------------

    if prev_state is None:

        best_candidate = min(
            candidates,
            key=lambda x: x[1]
        )

        best_state = best_candidate[0]

    # -------------------------------------------------
    # CONSTRAINED TRANSITIONS
    # -------------------------------------------------

    else:

        allowed_states = topology_graph.get(
            prev_state,
            [prev_state]
        )

        valid_candidates = []

        for candidate_idx, candidate_dist in candidates:

            # =============================================
            # TOPOLOGICAL TRANSITION
            # =============================================

            if candidate_idx not in allowed_states:

                continue

            # =============================================
            # MONOTONIC PROGRESSION
            # =============================================

            if initial_direction == "FAL_DW":

                if candidate_idx < prev_state:

                    continue

            elif initial_direction == "DW_FAL":

                if candidate_idx > prev_state:

                    continue

            valid_candidates.append(
                (
                    candidate_idx,
                    candidate_dist
                )
            )

        # fallback
        if len(valid_candidates) == 0:

            valid_candidates = [
                (
                    prev_state,
                    0
                )
            ]

        best_candidate = min(
            valid_candidates,
            key=lambda x: x[1]
        )

        candidate_state = best_candidate[0]

        # =================================================
        # MINIMUM HOLD LOGIC
        # =================================================

        MIN_HOLD_SAMPLES = 4

        if len(matched_indices_graph) < MIN_HOLD_SAMPLES:

            best_state = candidate_state

        else:

            recent_states = matched_indices_graph[
                -MIN_HOLD_SAMPLES:
            ]

            dominant_state = max(
                set(recent_states),
                key=recent_states.count
            )

            # ---------------------------------------------
            # zbyt szybka zmiana
            # ---------------------------------------------

            if abs(candidate_state - dominant_state) > 1:

                best_state = dominant_state

            else:

                best_state = candidate_state

    matched_indices_graph.append(
        best_state
    )

    prev_state = best_state

    
# =====================================================
# SAVE RESULTS
# =====================================================

df_candidates[
    "matched_graph_index"
] = matched_indices_graph

df_candidates[
    "matched_graph_name"
] = df_topology.iloc[
    matched_indices_graph
]["stop_name"].values

df_candidates[
    "matched_graph_direction"
] = df_topology.iloc[
    matched_indices_graph
]["direction"].values

df_candidates[
    "matched_graph_progress"
] = df_topology.iloc[
    matched_indices_graph
]["shape_dist_traveled"].values

print()
print(
    df_candidates[
        [
            "vehicle_time",
            "matched_graph_index",
            "matched_graph_name",
            "matched_graph_direction"
        ]
    ].head(20)
)

# =====================================================
# PLOT MATCHED TRAJECTORY
# =====================================================

plt.figure(figsize=(12, 12))

# AVL
plt.plot(
    df_interp["lon"],
    df_interp["lat"],
    alpha=0.3,
    linewidth=1,
    label="AVL"
)

# topology
plt.plot(
    df_topology["lon"],
    df_topology["lat"],
    linewidth=2,
    label="Topology"
)

# matched graph path
matched_lon = df_topology.iloc[
    matched_indices_graph
]["lon"].values

matched_lat = df_topology.iloc[
    matched_indices_graph
]["lat"].values

plt.plot(
    matched_lon,
    matched_lat,
    linewidth=2,
    label="Graph constrained path"
)

plt.legend()

plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.title(
    "Graph constrained transit reconstruction"
)

plt.grid(True)

output_path = os.path.join(
    output_dir,
    "graph_constrained_reconstruction.png"
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Zapisano:")
print(output_path)

plt.close()

# =====================================================
# PROGRESS PLOT
# =====================================================

plt.figure(figsize=(18, 6))

plt.plot(
    df_candidates[
        "matched_graph_progress"
    ]
)

plt.xlabel("AVL sample")
plt.ylabel("Topology progress [km]")

plt.title(
    "Graph constrained topology progress"
)

plt.grid(True)

output_path = os.path.join(
    output_dir,
    "graph_constrained_progress.png"
)

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Zapisano:")
print(output_path)

plt.close()

# =====================================================
# TOPOLOGICAL GAP FILLING
# =====================================================

print()
print("===================================")
print("TOPOLOGICAL GAP FILLING")
print("===================================")

filled_path = []

for i in range(len(matched_indices_graph) - 1):

    current_idx = matched_indices_graph[i]

    next_idx = matched_indices_graph[i + 1]

    # ================================================
    # append current
    # ================================================

    filled_path.append(current_idx)

    delta = next_idx - current_idx

    # ================================================
    # FORWARD
    # ================================================

    if delta > 1:

        missing_states = list(
            range(
                current_idx + 1,
                next_idx
            )
        )

        filled_path.extend(
            missing_states
        )

    # ================================================
    # BACKWARD
    # ================================================

    elif delta < -1:

        missing_states = list(
            range(
                current_idx - 1,
                next_idx,
                -1
            )
        )

        filled_path.extend(
            missing_states
        )

# =====================================================
# LAST STATE
# =====================================================

filled_path.append(
    matched_indices_graph[-1]
)

# =====================================================
# CREATE DATAFRAME
# =====================================================

df_filled = pd.DataFrame({

    "topology_index":
    filled_path

})

# =====================================================
# TOPOLOGY ATTRIBUTES
# =====================================================

df_filled["direction"] = df_filled[
    "topology_index"
].map(

    df_topology.set_index(
        "global_stop_index"
    )["direction"]

)

df_filled["stop_name"] = df_filled[
    "topology_index"
].map(

    df_topology.set_index(
        "global_stop_index"
    )["stop_name"]

)

df_filled["stop_sequence"] = df_filled[
    "topology_index"
].map(

    df_topology.set_index(
        "global_stop_index"
    )["stop_sequence"]

)

df_filled["lat"] = df_filled[
    "topology_index"
].map(

    df_topology.set_index(
        "global_stop_index"
    )["lat"]

)

df_filled["lon"] = df_filled[
    "topology_index"
].map(

    df_topology.set_index(
        "global_stop_index"
    )["lon"]

)

# =====================================================
# REMOVE DUPLICATES
# =====================================================

df_filled = df_filled.loc[
    df_filled[
        "topology_index"
    ].shift() != df_filled[
        "topology_index"
    ]
].reset_index(drop=True)

# =====================================================
# DISPLAY
# =====================================================

print()
print(df_filled.head(30))

print()
print("Filled path length:")
print(len(df_filled))

# =====================================================
# SAVE
# =====================================================

output_path = os.path.join(
    output_dir,
    "filled_topological_path.csv"
)

df_filled.to_csv(
    output_path,
    index=False
)

print()
print("Saved:")
print(output_path)

# =====================================================
# VISUALIZATION
# =====================================================

plt.figure(figsize=(14, 10))

# -----------------------------------------------------
# AVL
# -----------------------------------------------------

plt.plot(
    df_avl["lon"],
    df_avl["lat"],
    ".",
    alpha=0.3,
    label="AVL"
)

# -----------------------------------------------------
# REFERENCE TOPOLOGY
# -----------------------------------------------------

plt.plot(
    df_topology["lon"],
    df_topology["lat"],
    "-",
    linewidth=2,
    label="Full route topology"
)

# -----------------------------------------------------
# FILLED PATH
# -----------------------------------------------------

plt.plot(
    df_filled["lon"],
    df_filled["lat"],
    "-",
    linewidth=3,
    label="Reconstructed vehicle trip"
)

# -----------------------------------------------------
# STOP LABELS
# -----------------------------------------------------

for i in range(len(df_filled)):

    plt.text(
        df_filled.iloc[i]["lon"],
        df_filled.iloc[i]["lat"],
        str(
            df_filled.iloc[i][
                "stop_sequence"
            ]
        ),
        fontsize=8
    )

# -----------------------------------------------------
# STYLE
# -----------------------------------------------------

plt.title(
    "Topological gap filling"
)

plt.xlabel(
    "Longitude"
)

plt.ylabel(
    "Latitude"
)

plt.legend()

plt.grid(True)

# =====================================================
# SAVE FIGURE
# =====================================================

fig_path = os.path.join(
    output_dir,
    "topological_gap_filling.png"
)

plt.savefig(
    fig_path,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Saved:")
print(fig_path)

#plt.show()

# =====================================================
# VISUALIZATION
# =====================================================

fig, axes = plt.subplots(
    1,
    2,
    figsize=(22, 10)
)

# =====================================================
# PANEL 1
# FULL ROUTE TOPOLOGY
# =====================================================

ax = axes[0]

# -----------------------------------------------------
# AVL GPS
# -----------------------------------------------------

ax.plot(
    df_avl["lon"],
    df_avl["lat"],
    ".",
    alpha=0.25,
    label="AVL GPS observations"
)

# -----------------------------------------------------
# FULL ROUTE TOPOLOGY
# -----------------------------------------------------

ax.plot(
    df_topology["lon"],
    df_topology["lat"],
    "-",
    linewidth=2,
    label="Full route topology"
)

# -----------------------------------------------------
# STYLE
# -----------------------------------------------------

ax.set_title(
    "AVL observations and full route topology"
)

ax.set_xlabel(
    "Longitude"
)

ax.set_ylabel(
    "Latitude"
)

ax.grid(True)

ax.legend()

# =====================================================
# PANEL 2
# RECONSTRUCTED VEHICLE TRIP
# =====================================================

ax = axes[1]

# -----------------------------------------------------
# AVL GPS
# -----------------------------------------------------

ax.plot(
    df_avl["lon"],
    df_avl["lat"],
    ".",
    alpha=0.25,
    label="AVL GPS observations"
)

# -----------------------------------------------------
# FULL ROUTE TOPOLOGY
# -----------------------------------------------------

ax.plot(
    df_topology["lon"],
    df_topology["lat"],
    "--",
    linewidth=1.5,
    alpha=0.5,
    label="Full route topology"
)

# -----------------------------------------------------
# RECONSTRUCTED VEHICLE TRIP
# -----------------------------------------------------

ax.plot(
    df_filled["lon"],
    df_filled["lat"],
    "-",
    linewidth=3,
    label="Reconstructed vehicle trip"
)

# -----------------------------------------------------
# STOP LABELS
# -----------------------------------------------------

for i in range(len(df_filled)):

    ax.text(
        df_filled.iloc[i]["lon"],
        df_filled.iloc[i]["lat"],
        str(
            df_filled.iloc[i][
                "stop_sequence"
            ]
        ),
        fontsize=8
    )

# -----------------------------------------------------
# STYLE
# -----------------------------------------------------

ax.set_title(
    "Topological reconstruction of vehicle trip"
)

ax.set_xlabel(
    "Longitude"
)

ax.set_ylabel(
    "Latitude"
)

ax.grid(True)

ax.legend()

# =====================================================
# SAVE FIGURE
# =====================================================

plt.tight_layout()

fig_path = os.path.join(
    output_dir,
    "topological_reconstruction_panels.png"
)

plt.savefig(
    fig_path,
    dpi=300,
    bbox_inches="tight"
)

print()
print("Saved:")
print(fig_path)

plt.show()