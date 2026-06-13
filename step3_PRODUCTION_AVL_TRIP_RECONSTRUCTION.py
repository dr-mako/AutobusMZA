# =========================================================
# STEP 3
# PRODUCTION TRIP AVL RECONSTRUCTION SYSTEM
# =========================================================
#
# python step3_PRODUCTION_AVL_TRIP_RECONSTRUCTION.py 
#
# =========================================================
# STEP3 AVL RECONSTRUCTION SYSTEM
# =========================================================
#
# ETAP 2
#
# DOJŚCIE DO DANYCH ŹRÓDŁOWYCH
#
# FILOZOFIA:
#
# Katalog.xlsx steruje pipeline
#
# Program:
#
# 1. przechodzi po przypadkach
# 2. sprawdza komplet danych
# 3. jeśli YES:
#       ładuje dane źródłowe
# 4. jeśli NO:
#       pomija przypadek
#
# BEZ REKONSTRUKCJI
#
# =========================================================

import os
import warnings

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2

# =========================================================
# PARAMETRY
# =========================================================

PATH_CATALOG = r"DANE/Katalog.xlsx"

PATH_DATA = r"DANE"

PATH_OUTPUT = r"OUTPUT"

PATH_STEP3 = r"OUTPUT_STEP3"

# =========================================================
# CREATE OUTPUT
# =========================================================

os.makedirs(

    PATH_STEP3,

    exist_ok=True
)

# =========================================================
# BUILD PATHS
# =========================================================

def build_case_paths(row):

    # =====================================================
    # PARAMS
    # =====================================================

    katalog = str(
        row["KATALOG"]
    )

    mza_csv = str(
        row["MZA.csv"]
    )

    stoptime_1 = str(
        row["stoptimes_1.xlsx"]
    )

    stoptime_2 = str(
        row["stoptimes_2.xlsx"]
    )

    vehicle = int(
        row["vehicle"]
    )

    line = str(
        row["line"]
    )

    # =====================================================
    # AVL
    # =====================================================

    path_avl = os.path.join(

        PATH_DATA,

        katalog,

        mza_csv + ".csv"
    )

    # =====================================================
    # TOPOLOGY
    # =====================================================

    path_topology_1 = os.path.join(

        PATH_DATA,

        katalog,

        stoptime_1 + ".xlsx"
    )

    path_topology_2 = os.path.join(
        PATH_DATA,
        katalog,
        stoptime_2 + ".xlsx"
    )

    # =====================================================
    # OUTPUT STEP1
    # =====================================================

    output_vehicle_dir = os.path.join(

        PATH_OUTPUT,

        f"{katalog}_line_{line}",

        f"vehicle_{vehicle}"
    )

    # =====================================================
    # TRIP SUMMARY
    # =====================================================

    path_trip_summary = os.path.join(

        output_vehicle_dir,

        "trip_summary.csv"
    )

    # =====================================================
    # STEP3 OUTPUT
    # =====================================================

    step3_output_dir = os.path.join(

        PATH_STEP3,

        f"{katalog}_line_{line}",

        f"vehicle_{vehicle}"
    )

    # =====================================================
    # RESULT
    # =====================================================

    result = {

        "katalog":
            katalog,

        "line":
            line,

        "vehicle":
            vehicle,

        "path_avl":
            path_avl,

        "path_topology_1":
            path_topology_1,

        "path_topology_2":
            path_topology_2,

        "path_trip_summary":
            path_trip_summary,

        "output_vehicle_dir":
            output_vehicle_dir,

        "step3_output_dir":
            step3_output_dir
    }

    return result

# =========================================================
# CHECK FILES
# =========================================================

def check_case_files(case_paths):

    result = {}

    # =====================================================
    # AVL
    # =====================================================

    result["avl_exists"] = os.path.exists(

        case_paths["path_avl"]
    )

    # =====================================================
    # TOPOLOGY
    # =====================================================

    result["topology_exists"] = (

        os.path.exists(
            case_paths["path_topology_1"]
        )

        and

        os.path.exists(
            case_paths["path_topology_2"]
        )

    )

    # =====================================================
    # TRIP SUMMARY
    # =====================================================

    result["trip_summary_exists"] = os.path.exists(

        case_paths["path_trip_summary"]
    )

    # =====================================================
    # OUTPUT DIR
    # =====================================================

    result["output_dir_exists"] = os.path.exists(

        case_paths["output_vehicle_dir"]
    )

    # =====================================================
    # COMPLETE
    # =====================================================

    result["complete_case"] = (

        result["avl_exists"]

        and

        result["topology_exists"]

        and

        result["trip_summary_exists"]
    )

    return result

# =========================================================
# CREATE STEP3 OUTPUT
# =========================================================

def create_step3_output(case_paths):

    os.makedirs(

        case_paths["step3_output_dir"],

        exist_ok=True
    )

# =========================================================
# LOAD AVL
# =========================================================

def load_avl(path_avl):

    print()
    print("Loading AVL...")

    df = pd.read_csv(

        path_avl,

        sep=";",

        header=None,

        engine="python"
    )

    # =====================================================
    # MATLAB-COMPATIBLE
    # =====================================================

    df.columns = [

        "line",
        "vehicle_nr",
        "brigade",

        "lat_raw",
        "lon_raw",

        "vehicle_time",
        "server_time"
    ]

    print()
    print("AVL loaded")

    print("Samples:")
    print(len(df))

    return df

# =========================================================
# GPS PARSER
# =========================================================

def parse_coordinate(x):

    """
    Obsługa:
    - float
    - string
    - przecinki
    - stare formaty MZA
    """

    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    s = s.replace(",", ".")

    # =====================================================
    # NORMAL FLOAT
    # =====================================================

    try:
        return float(s)

    except:
        pass

    # =====================================================
    # STARY FORMAT:
    # 52248743 -> 52.248743
    # =====================================================

    s = s.replace(".", "")

    if len(s) >= 6:

        try:

            return float(
                s[:2] + "." + s[2:]
            )

        except:

            return np.nan

    return np.nan

def compute_orientation_dot(

    idx,
    df_trip,
    stop_lat,
    stop_lon

):

    if idx <= 0 or idx >= len(df_trip) - 1:

        return np.nan

    x_prev = df_trip.iloc[idx - 1]["lon"]
    y_prev = df_trip.iloc[idx - 1]["lat"]

    x_next = df_trip.iloc[idx + 1]["lon"]
    y_next = df_trip.iloc[idx + 1]["lat"]

    bus_dx = x_next - x_prev
    bus_dy = y_next - y_prev

    vehicle_lon = df_trip.iloc[idx]["lon"]
    vehicle_lat = df_trip.iloc[idx]["lat"]

    stop_dx = stop_lon - vehicle_lon
    stop_dy = stop_lat - vehicle_lat

    return (

        bus_dx * stop_dx

        +

        bus_dy * stop_dy

    )

# =========================================================
# TIME PARSER
# =========================================================

def parse_datetime_column(series):

    """
    Obsługa wielu formatów AVL.
    """

    # =====================================================
    # STRING
    # =====================================================

    s = series.astype(str).str.strip()

    # =====================================================
    # FORMAT ISO
    # 2026-05-11 00:00:06
    # =====================================================

    dt1 = pd.to_datetime(

        s,

        format="%Y-%m-%d %H:%M:%S",

        errors="coerce"
    )

    # =====================================================
    # FORMAT EUROPEJSKI
    # 12.05.2026 23:59
    # =====================================================

    dt2 = pd.to_datetime(

        s,

        format="%d.%m.%Y %H:%M",

        errors="coerce"
    )

    # =====================================================
    # FORMAT EUROPEJSKI + SEKUNDY
    # 12.05.2026 23:59:01
    # =====================================================

    dt3 = pd.to_datetime(

        s,

        format="%d.%m.%Y %H:%M:%S",

        errors="coerce"
    )

    # =====================================================
    # ŁĄCZENIE
    # =====================================================

    dt = dt1.fillna(dt2)

    dt = dt.fillna(dt3)

    return dt

# =========================================================
# READ CATALOG
# =========================================================

def read_catalog(path_catalog):

    print()
    print("Reading catalog...")

    df = pd.read_excel(path_catalog)

    required_columns = [

        "KATALOG",
        "MZA.csv",
        "RaceBox.csv",
        "stoptimes_1.xlsx",
        "stoptimes_2.xlsx",
        "vehicle",
        "od_dnia",
        "od_godz",
        "do_dnia",
        "do_godz",
        "line"
    ]

    for col in required_columns:

        if col not in df.columns:

            raise Exception(
                f"Missing column: {col}"
            )

    return df

# =========================================================
# BUILD ARRIVAL TABLE
# =========================================================

def build_arrival_table(
    df_trip,
    df_topology,
    direction_id
):
    arrival_records = []

    for stop_sequence in np.unique(
        df_trip["reconstructed_stop_sequence"]
    ):
        
        stop_rows = df_trip[

            df_trip[
                "reconstructed_stop_sequence"
            ]

            ==

            stop_sequence

        ].copy()

        stop_topology = df_topology[

            df_topology[
                "stop_sequence"
            ]

            ==

            stop_sequence

        ]

        if len(stop_topology) == 0:

            continue

        stop_lat = stop_topology.iloc[0][
            "stop_lat"
        ]

        stop_lon = stop_topology.iloc[0][
            "stop_lon"
        ]

        distance_list = []

        for _, row in stop_rows.iterrows():

            d = haversine_m(

                row["lat"],
                row["lon"],

                stop_lat,
                stop_lon

            )

            distance_list.append(d)

        # FILTR PRZYPADKÓW        
        if stop_sequence in [3, 7]:

            print()
            print(
                f"STOP {stop_sequence}"
            )

            print(
                f"MIN DISTANCE: "
                f"{np.min(distance_list):.1f}"
            )

            print(
                f"MAX DISTANCE: "
                f"{np.max(distance_list):.1f}"
            )        

        stop_rows[
            "distance_to_stop_m"
        ] = distance_list

        best_idx = stop_rows[
            "distance_to_stop_m"
        ].idxmin()

        best_row = stop_rows.loc[
            best_idx
        ]

        arrival_records.append({

            "stop_sequence":
                int(stop_sequence),

            "arrival_time":
                best_row["time"],

            "distance_to_stop_m":
                best_row["distance_to_stop_m"],

            "avl_idx":
                int(best_idx),

            "vehicle_lat":
                best_row["lat"],

            "vehicle_lon":
                best_row["lon"],

            "stop_lat":
                stop_lat,

            "stop_lon":
                stop_lon

        })


    arrival_df = pd.DataFrame(
        arrival_records
    )

    arrival_df["direction"] = (
        direction_id
    )

    arrival_df = arrival_df.sort_values(
        "stop_sequence"
    )

    arrival_df["travel_time_s"] = (

        arrival_df[
            "arrival_time"
        ]

        .diff()

        .dt.total_seconds()

    )

    print()
    print("QUALITY SUMMARY")

    print(
        f"Stops: {len(arrival_df)}"
    )

    print(
        f"Mean distance: "
        f"{arrival_df['distance_to_stop_m'].mean():.1f} m"
    )

    print(
        f"Median distance: "
        f"{arrival_df['distance_to_stop_m'].median():.1f} m"
    )

    print(
        f"Max distance: "
        f"{arrival_df['distance_to_stop_m'].max():.1f} m"
    )

    orientation_dot = []

    for _, row in arrival_df.iterrows():

        idx = int(
            row["avl_idx"]
        )

        dot = compute_orientation_dot(

            idx,

            df_trip,

            row["stop_lat"],

            row["stop_lon"]

        )

        orientation_dot.append(
            dot
        )

    arrival_df[
        "orientation_dot"
    ] = orientation_dot


    arrival_df[
        "orientation_sign"
    ] = np.where(

        arrival_df[
            "orientation_dot"
        ] > 0,

        1,

        -1

    )


    neighbor_sign = []

    for _, row in arrival_df.iterrows():

        idx = int(
            row["avl_idx"]
        )

        sign = row[
            "orientation_sign"
        ]

        if sign > 0:

            test_idx = idx + 1

        else:

            test_idx = idx - 1

        if (
            test_idx < 0
            or
            test_idx >= len(df_trip)
        ):

            neighbor_sign.append(
                np.nan
            )

            continue

        dot = compute_orientation_dot(

            test_idx,

            df_trip,

            row["stop_lat"],

            row["stop_lon"]

        )

        if np.isnan(dot):

            neighbor_sign.append(
                np.nan
            )

        elif dot > 0:

            neighbor_sign.append(
                1
            )

        else:

            neighbor_sign.append(
                -1
            )

    arrival_df[
        "neighbor_sign"
    ] = neighbor_sign


    print()

    print(

        arrival_df[
            [
                "stop_sequence",
                "distance_to_stop_m",
                "orientation_sign",
                "neighbor_sign"
            ]
        ]

    )

    arrival_df[
        "arrival_time_corrected"
    ] = arrival_df[
        "arrival_time"
    ]

    arrival_df[
        "correction_applied"
    ] = 0

    min_stop = arrival_df[
        "stop_sequence"
    ].min()

    max_stop = arrival_df[
        "stop_sequence"
    ].max()

    for idx_row, row in arrival_df.iterrows():

        if (

            row["stop_sequence"] == min_stop

            or

            row["stop_sequence"] == max_stop

        ):

            continue

        distance = row[
            "distance_to_stop_m"
        ]

        if distance <= 50:

            continue

        sign0 = row[
            "orientation_sign"
        ]

        sign1 = row[
            "neighbor_sign"
        ]

        if sign0 == sign1:

            continue

        avl_idx = int(
            row["avl_idx"]
        )

        if sign0 > 0:

            idx_neighbor = avl_idx + 1

        else:

            idx_neighbor = avl_idx - 1

        t0 = row[
            "arrival_time"
        ]

        t1 = df_trip.iloc[
            idx_neighbor
        ]["time"]

        if t0 == t1:
            continue

        dt_abs = abs(
            (t1 - t0).total_seconds()
        )

        if dt_abs > 60:

            continue

        lat1 = df_trip.iloc[
            idx_neighbor
        ]["lat"]

        lon1 = df_trip.iloc[
            idx_neighbor
        ]["lon"]

        stop_lat = row[
            "stop_lat"
        ]

        stop_lon = row[
            "stop_lon"
        ]

        d1 = haversine_m(
            lat1,
            lon1,
            stop_lat,
            stop_lon
        )

        d0 = distance

        # waga

        w = d0 / (
            d0 + d1
        )

        # interpolacja

        dt = (
            t1 - t0
        ).total_seconds()

        t_corrected = pd.Timestamp(

            t0

            +

            pd.Timedelta(
                milliseconds=int(
                    1000 * w * dt
                )
            )

        )        

        arrival_df.loc[
            idx_row,
            "arrival_time_corrected"
        ] = t_corrected

        arrival_df.loc[
            idx_row,
            "correction_applied"
        ] = 1
    
    return arrival_df

# =========================================================
# FILL MISSING STOPS
# =========================================================

def fill_missing_stops(

    arrival_df,
    df_topology

):

    filled_records = []

    arrival_df = arrival_df.sort_values(
        "stop_sequence"
    )

    arrival_df = arrival_df.reset_index(
        drop=True
    )

    for i in range(len(arrival_df)-1):

        row1 = arrival_df.iloc[i]
        row2 = arrival_df.iloc[i+1]

        stop1 = int(
            row1["stop_sequence"]
        )

        stop2 = int(
            row2["stop_sequence"]
        )

        time1 = row1["arrival_time"]
        time2 = row2["arrival_time"]

        filled_records.append(

            row1.to_dict()

        )

        # =====================================
        # BRAK PRZYSTANKÓW
        # =====================================

        if stop2 - stop1 > 1:

            print()

            print(
                f"GAP: {stop1} -> {stop2}"
            )

    filled_records.append(

        arrival_df.iloc[-1].to_dict()

    )

    filled_df = pd.DataFrame(
        filled_records
    )

    return filled_df

# =========================================================
# VALIDATE CASE
# =========================================================

def validate_case(row):

    required_fields = [

        "KATALOG",
        "MZA.csv",

        "stoptimes_1.xlsx",
        "stoptimes_2.xlsx",

        "vehicle",
        "line"
    ]

    for field in required_fields:

        value = row[field]

        if pd.isna(value):

            return False

        if str(value).strip() == "":

            return False

    return True

# =========================================================
# HAVERSINE
# =========================================================

def haversine_m(

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


# =========================================================
# TOPOLOGY RECONSTRUCTION
# =========================================================

def reconstruct_trip_topology(
    df_trip,
    df_topology,
    trip_direction
):    
    
    print()
    print("MAP MATCHING DIRECTION")
    print(trip_direction)    

    print()
    print("Candidate generation...")

    candidate_list = []

    for i in range(len(df_trip)):

        lat_bus = df_trip.iloc[i]["lat"]
        lon_bus = df_trip.iloc[i]["lon"]

        distances = []

        for j in range(len(df_topology)):

            d = haversine_m(

                lat_bus,
                lon_bus,

                df_topology.iloc[j]["stop_lat"],
                df_topology.iloc[j]["stop_lon"]

            )

            distances.append(d)

        distances = np.array(distances)

        sorted_idx = np.argsort(
            distances
        )

        candidates = []

        for idx in sorted_idx[:3]:

            d = distances[idx]

            if d < 500:

                candidates.append({

                    "topology_idx":
                    idx,

                    "distance":
                    d,

                    "stop_sequence":
                    df_topology.iloc[idx][
                        "stop_sequence"
                    ]

                })

        candidate_list.append(
            candidates
        )

    
    print("DONE Candidate generation")

    # =====================================================
    # EMISSION PROBABILITY
    # =====================================================

    print()
    print("Emission probabilities...")

    for candidates in candidate_list:

        for c in candidates:

            d = c["distance"]

            p = np.exp(

                -0.5
                *
                (d / 30) ** 2

            )

            c["emission_prob"] = p

    print("DONE EMISSION")

    # =====================================================
    # GRAPH MATCHING
    # =====================================================

    print()
    print("Graph constrained matching...")

    matched_indices = []

    matched_distances = []

    nearest_indices = []

    previous_idx = None

    best_candidate = np.nan
    best_distance = np.nan
    best_score = -np.inf

    for candidates in candidate_list:

        if len(candidates) == 0:

            matched_indices.append(
                np.nan
            )

            matched_distances.append(
                np.nan
            )

            nearest_indices.append(
                np.nan
            )

            continue

        best_candidate = None

        best_score = -np.inf

        nearest_candidate = min(
            candidates,
            key=lambda x: x["distance"]
        )

        nearest_indices.append(
            nearest_candidate["topology_idx"]
        )

        for c in candidates:

            idx = c["topology_idx"]

            emission = c[
                "emission_prob"
            ]

            transition_penalty = 0

            if previous_idx is not None:

                jump = idx - previous_idx

                # =====================================
                # KIERUNEK
                # =====================================

                if trip_direction == 1:

                    if jump < 0:

                        transition_penalty -= 100

                if trip_direction == 2:

                    if jump > 0:

                        transition_penalty -= 100

                # =====================================
                # ZA DUŻY SKOK
                # =====================================

                if abs(jump) > 5:

                    transition_penalty -= 1000

            score = (

                emission

                +

                transition_penalty

            )

            if score > best_score:

                best_score = score

                best_candidate = idx

                best_distance = c["distance"]

                
        matched_indices.append(
            best_candidate
        )

        matched_distances.append(
            best_distance
        )

        previous_idx = best_candidate

        # =====================================
        # KONIEC PĘTLI
        # =====================================

    #print()
    #print("FIRST 50 RAW MATCHES")
    #print(matched_indices[:50])

    matched_indices = np.array(
        matched_indices,
        dtype=float
    )

    valid = np.where(
        ~np.isnan(matched_indices)
    )[0]

    for i in range(len(valid)-1):

        idx1 = valid[i]
        idx2 = valid[i+1]

        topo1 = matched_indices[idx1]
        topo2 = matched_indices[idx2]

        gap = idx2 - idx1

        if gap <= 1:
            continue

        interp = np.linspace(
            topo1,
            topo2,
            gap + 1
        )

        matched_indices[
            idx1:idx2+1
        ] = interp

    matched_indices = (
        pd.Series(matched_indices)
        .bfill()
        .ffill()
    )

    matched_indices = np.round(
        matched_indices
    )

    matched_indices = (
        matched_indices
        .astype(int)
        .values
    )

    df_trip["topology_idx"] = matched_indices

    df_trip["reconstructed_stop_sequence"] = (
        df_topology.iloc[
            matched_indices
        ]["stop_sequence"].values
    )

    unique_stops = np.unique(
        df_trip["reconstructed_stop_sequence"]
    )

    print(
        "Observed stops:",
        len(unique_stops)
    )

        # FILTR
    print()
    print("OBSERVED STOPS")

    print(
        np.unique(
            df_trip[
                "reconstructed_stop_sequence"
            ]
        )
    )
    print()
    print("STOP COUNTS")

    print(
        df_trip[
            "reconstructed_stop_sequence"
        ]
        .value_counts()
        .sort_index()
    )
    print()
    print("STOP 7 SAMPLES")

    print(
        df_trip[
            df_trip[
                "reconstructed_stop_sequence"
            ] == 7
        ][
            [
                "time",
                "lat",
                "lon"
            ]
        ].head(20)
    )
    print()
    print("STOP 3 SAMPLES")

    print(
        df_trip[
            df_trip[
                "reconstructed_stop_sequence"
            ] == 3
        ][
            [
                "time",
                "lat",
                "lon"
            ]
        ].head(20)
    )
    # FILTR KONIEC

    df_trip["topology_idx"] = matched_indices

    df_trip["vehicle_shape_dist"] = (
        df_topology.iloc[
            matched_indices
        ]["shape_dist_traveled"].values
    )
        
    

    df_trip["matched_stop_idx"] = matched_indices

    df_trip["matched_distance_m"] = matched_distances
    
    nearest_indices = np.array(
        nearest_indices
    )

    matched_indices_array = np.array(
        matched_indices
    )

    agreement = np.mean(

        nearest_indices

        ==

        matched_indices_array

    )

    return df_trip


#
# =========================================================
# PREPARE AVL
# =========================================================

def prepare_avl_data(df):

    print()
    print("Preparing AVL data...")

    # =====================================================
    # GPS
    # =====================================================

    df["lat"] = df["lat_raw"].apply(
        parse_coordinate
    )

    df["lon"] = df["lon_raw"].apply(
        parse_coordinate
    )

    # =====================================================
    # TIME
    # =====================================================

    df["time"] = parse_datetime_column(
        df["vehicle_time"]
    )

    # =====================================================
    # USUNIĘCIE BŁĘDÓW
    # =====================================================

    df = df.dropna(

        subset=[

            "lat",
            "lon",
            "time"
        ]

    ).copy()

    return df


# =========================================================
# LOAD TOPOLOGY
# =========================================================

def load_topology(path_topology):

    print()
    print("Loading topology...")

    try:

        df = pd.read_excel(

            path_topology,

            sheet_name="stoptimes"
        )

    except:

        df = pd.read_excel(
            path_topology
        )

    print()
    print("Topology loaded")

    print("Stops:")
    print(len(df))

    return df

# =========================================================
# LOAD TRIP SUMMARY
# =========================================================

def load_trip_summary(path_trip_summary):

    print()
    print("Loading trip summary...")

    df = pd.read_csv(
        path_trip_summary
    )

    # =====================================================
    # TIME
    # =====================================================

    if "start_time" in df.columns:

        df["start_time"] = pd.to_datetime(
            df["start_time"]
        )

    if "end_time" in df.columns:

        df["end_time"] = pd.to_datetime(
            df["end_time"]
        )

    print()
    print("Trip summary loaded")

    print("Trips:")
    print(len(df))

    return df


# =========================================================
# PRINT CASE
# =========================================================

def print_case_summary(

    case_paths,
    file_status
):

    print()
    print("===================================")

    print(
        f"CASE: "
        f"{case_paths['katalog']}"
    )

    print("===================================")

    print()
    print("LINE:")
    print(case_paths["line"])

    print()
    print("VEHICLE:")
    print(case_paths["vehicle"])

    print()
    print("AVL EXISTS:")
    print(file_status["avl_exists"])

    print()
    print("TOPOLOGY EXISTS:")
    print(file_status["topology_exists"])

    print()
    print("TRIP SUMMARY EXISTS:")
    print(file_status["trip_summary_exists"])

    print()
    print("COMPLETE CASE:")

    if file_status["complete_case"]:

        print("YES")

    else:

        print("NO")

# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("===================================")
    print("STEP3 AVL RECONSTRUCTION SYSTEM")
    print("===================================")

    # =====================================================
    # READ CATALOG
    # =====================================================

    catalog_df = read_catalog(
        PATH_CATALOG
    )

    # =====================================================
    # GLOBAL TABLE
    # =====================================================

    case_rows = []

    # =====================================================
    # LOOP
    # =====================================================

    for idx, row in catalog_df.iterrows():

        # FILTR PRZYPADKÓW
        if row["KATALOG"] != "08-05-151":
            continue

        if row["line"] != 151:
            continue

        if row["vehicle"] != 8567:
            continue

        # =================================================
        # VALIDATION
        # =================================================

        valid = validate_case(row)

        if not valid:

            print()
            print(f"CASE {idx+1}")
            print("INVALID -> skipped")

            continue

        try:

            # =============================================
            # PATHS
            # =============================================

            case_paths = build_case_paths(
                row
            )

            # =============================================
            # STATUS
            # =============================================

            file_status = check_case_files(
                case_paths
            )

            # =============================================
            # OUTPUT
            # =============================================

            create_step3_output(
                case_paths
            )

            # =============================================
            # PRINT
            # =============================================

            print_case_summary(

                case_paths,
                file_status
            )

            # =============================================
            # INCOMPLETE
            # =============================================

            if not file_status["complete_case"]:

                print()
                print("CASE SKIPPED")

                continue

            # =============================================
            # LOAD AVL
            # =============================================

            df_avl = load_avl(

                case_paths["path_avl"]
            )

            # =============================================
            # PREPARE AVL
            # =============================================

            df_avl = prepare_avl_data(
                df_avl
            )

            vehicle_id = case_paths["vehicle"]

            df_avl = df_avl[
                df_avl["vehicle_nr"] == vehicle_id
            ].copy()

           

            # =============================================
            # LOAD TOPOLOGY
            # =============================================

            df_topology_1 = load_topology(

                case_paths["path_topology_1"]

            )

            df_topology_2 = load_topology(

                case_paths["path_topology_2"]

            )       
            
            # =============================================
            # LOAD SUMMARY
            # =============================================

            df_trip_summary = load_trip_summary(

                case_paths[
                    "path_trip_summary"
                ]
            )

            # =============================================
            # BUILD TRIPS FROM SUMMARY
            # =============================================

            print()
            print("===================================")
            print("TRIPS FROM SUMMARY")
            print("===================================")

            

            for _, trip in df_trip_summary.iterrows():

                trip_id = int(
                    trip["trip_id"]
                )

                start_time = trip[
                    "start_time"
                ]

                end_time = trip[
                    "end_time"
                ]

                trip_direction = int(
                    trip["direction"]
                )

                # FILTR PRZYPADKÓW
                if trip_direction != -1:
                    continue

                if trip_direction == 1:

                    df_topology = df_topology_1
                    topology_name = "T1"
                    direction_id = 1

                else:

                    df_topology = df_topology_2
                    topology_name = "T2"
                    direction_id = 2

                '''
                print()
                print("TOPOLOGY COLUMNS")
                print(
                    df_topology.columns.tolist()
                )
                print()
                print(
                    df_topology.head()
                )
                '''
                

                # =========================================
                # CUT AVL SEGMENT
                # =========================================

                df_trip = df_avl[

                    (df_avl["time"] >= start_time)

                    &

                    (df_avl["time"] <= end_time)

                ].copy()

                # =========================================
                # SORT
                # =========================================

                df_trip = df_trip.sort_values(
                    "time"
                ).reset_index(drop=True)

                
                # =========================================
                # EMPTY
                # =========================================

                if len(df_trip) == 0:

                    print(
                        "WARNING: EMPTY TRIP"
                    )

                    continue

                
                df_trip = reconstruct_trip_topology(

                    df_trip,
                    df_topology,
                    trip_direction

                )                

                arrival_df = build_arrival_table(

                    df_trip,
                    df_topology,
                    direction_id

                )

                arrival_df = fill_missing_stops(

                    arrival_df,
                    df_topology

                )

                output_arrivals = os.path.join(

                    case_paths[
                        "step3_output_dir"
                    ],

                    f"trip_{trip_id:03d}_arrival_times.csv"

                )

                arrival_df.to_csv(

                    output_arrivals,

                    index=False

                )               

                
                # =========================================
                # TEMP EXPORT
                # =========================================

                output_trip = os.path.join(

                    case_paths[
                        "step3_output_dir"
                    ],

                    f"trip_{trip_id:03d}_raw.csv"
                )

                df_trip.to_csv(

                    output_trip,

                    index=False
                )

                topology_sequences = list(
                    df_topology["stop_sequence"]
                )

            # <-- KONIEC PĘTLI FOR
    
        except Exception as e:

            print()
            print("CASE FAILED")

            print(str(e))

        


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()