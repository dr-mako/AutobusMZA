# =========================================================
# MATLAB-COMPATIBLE AVL SEGMENTATION SYSTEM
# =========================================================
#
# FILOZOFIA:
#
# 1. NOWOCZESNY IMPORT I ORGANIZACJA
# 2. MAKSYMALNIE PROSTA SEGMENTACJA
# 3. CORE ZGODNY SEMANTYCZNIE Z MATLAB
#
# =========================================================

import os
import warnings

import numpy as np
import pandas as pd

from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# python step1_avl_trip_separator.py

# =========================================================
# PARAMETRY
# =========================================================

PATH_CATALOG = r"DANE/Katalog.xlsx"

PATH_DATA = r"DANE"

PATH_OUTPUT = r"OUTPUT"

MAX_STOP_DISTANCE = 120  # [m]

# =========================================================
# HAVERSINE
# =========================================================

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
        cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c

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

# =====================================================
# CONTROL PLOT
# =====================================================

def create_control_plot(

    df,
    output_dir,
    line_nr,
    vehicle_id

):

    #print()
    #print("Control plot...")

    plt.figure(figsize=(16, 7))

    unique_courses = sorted(
        df["course_id"].unique()
    )

    n_courses = len(unique_courses)
    

    # =================================================
    # DUŻO KURSÓW
    # =================================================

    cmap = plt.cm.get_cmap(
        "tab20",
        min(max(n_courses, 1), 20)
    )

    for i, course in enumerate(unique_courses):

        trip_df = df[
            df["course_id"] == course
        ]

        color = cmap(i % 20)

        plt.scatter(

            trip_df["time"],

            trip_df["nearest_stop_id"],

            s=4,

            color=color,

            alpha=0.7
        )

        plt.plot(

        trip_df["time"],

        trip_df["nearest_stop_id"],

        linewidth=1.2,

        color=color,

        alpha=0.9
    )

    # =================================================
    # OPISY
    # =================================================

    plt.xlabel("Time")

    plt.ylabel("Stop sequence")

    plt.title(

        f"AVL segmentation | "
        f"line {line_nr} | "
        f"vehicle {vehicle_id}"
    )

    plt.grid(True)

    plt.tight_layout()

    # =================================================
    # SAVE
    # =================================================

    plot_path = os.path.join(

        output_dir,
        "trip_segmentation.png"
    )

    plt.savefig(

        plot_path,

        dpi=300,

        bbox_inches="tight"
    )

    plt.close()

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
# CREATE OUTPUT DIRECTORY
# =========================================================

def create_output_directory(

    output_root,
    katalog,
    line_nr,
    vehicle_id

):

    path_output = (

        Path(output_root)

        /

        f"{katalog}_line_{line_nr}"

        /

        f"vehicle_{vehicle_id}"
    )

    path_output.mkdir(
        parents=True,
        exist_ok=True
    )

    return str(path_output)

# =========================================================
# READ AVL
# =========================================================

def read_avl_file(path_csv):

    print()
    print("Reading AVL...")

    # =====================================================
    # MZA CSV:
    # separator = ;
    # brak nagłówków
    # =====================================================

    df = pd.read_csv(

        path_csv,

        sep=";",

        header=None,

        engine="python"
    )

    #print()
    #print("RAW AVL:")
    #print(df.head())

    #print()
    #print("SHAPE:")
    #print(df.shape)

    # =====================================================
    # MATLAB-COMPATIBLE COLUMN ASSIGNMENT
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

    return df

# =========================================================
# READ STOPS
# =========================================================

def read_stops(path_excel):

    print()
    print("Reading stops...")

    df = pd.read_excel(
        path_excel,
        sheet_name="stoptimes"
    )

    required = [

        "stop_sequence",
        "stop_lat",
        "stop_lon"
    ]

    for col in required:

        if col not in df.columns:

            raise Exception(
                f"Missing stop column: {col}"
            )

    return df

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
# FILTER CASE
# =========================================================

def filter_case(

    df,
    line_nr,
    vehicle_id,

    od_dnia,
    od_godz,

    do_dnia,
    do_godz
):

    print()
    print("Filtering case...")

    # =====================================================
    # LINE
    # =====================================================

    df = df[
        df["line"].astype(str)
        ==
        str(line_nr)
    ].copy()


        # =====================================================
    # TIME FILTER
    # MATLAB-COMPATIBLE
    # =====================================================

    if (

        not pd.isna(od_dnia)
        and
        not pd.isna(od_godz)

    ):

        day = df["time"].dt.day

        hour = df["time"].dt.hour

        idx_time = (
            (day == od_dnia)
            &
            (hour >= od_godz)
        )

        df = df[idx_time].copy()
    '''
    print()
    print(df["time"].min())

    print(df["time"].max())

    print()

    print(
        sorted(
            df["time"].dt.hour.unique()
        )
    )
    '''


    # =====================================================
    # VEHICLE
    # =====================================================

    # =====================================================
    # VEHICLE FILTER
    # =====================================================

    vehicle_id = int(vehicle_id)

    df["vehicle_nr"] = pd.to_numeric(

        df["vehicle_nr"],
        errors="coerce"
    )

    print()
    print("TARGET VEHICLE:")
    print(vehicle_id)

    #print()
    #print("UNIQUE VEHICLES:")
    #print(sorted(df["vehicle_nr"].dropna().unique())[:20])

    df = df[

        df["vehicle_nr"]
        ==
        vehicle_id

    ].copy()

    print()
    print("AFTER VEHICLE FILTER:")
    print(len(df))

    if len(df) == 0:

        return df

    # =====================================================
    # SORTOWANIE
    # =====================================================

    df = df.sort_values(
        "time"
    ).reset_index(drop=True)

    return df

# =========================================================
# NEAREST STOP
# =========================================================

def assign_nearest_stop(

    df_bus,
    stops_df
):

    #print()
    #print("Nearest stop assignment...")

    stop_sequence = (
        stops_df["stop_sequence"]
        .to_numpy()
    )

    lat_stop = (
        stops_df["stop_lat"]
        .to_numpy()
    )

    lon_stop = (
        stops_df["stop_lon"]
        .to_numpy()
    )

    nearest_stop_id = []

    nearest_distance = []

    N = len(df_bus)

    N_stops = len(stops_df)

    # =====================================================
    # MATLAB STYLE:
    # KAŻDY PUNKT NIEZALEŻNIE
    # =====================================================

    for i in range(N):

        lat_bus = df_bus.iloc[i]["lat"]

        lon_bus = df_bus.iloc[i]["lon"]

        dist_all = []

        for j in range(N_stops):

            d = haversine(

                lat_bus,
                lon_bus,

                lat_stop[j],
                lon_stop[j]
            )

            dist_all.append(d)

        dist_all = np.array(
            dist_all,
            dtype=np.float64
        )

        idx_min = np.argmin(dist_all)

        nearest_stop_id.append(
            stop_sequence[idx_min]
        )

        nearest_distance.append(
            dist_all[idx_min]
        )

    df_bus["nearest_stop_id"] = nearest_stop_id

    '''
    # =====================================================
    # SMOOTH STOP ID
    # =====================================================

    stop_id = np.array(
        nearest_stop_id,
        dtype=float
    )

    stop_id_filtered = stop_id.copy()

    for i in range(3, len(stop_id) - 3):

        window = stop_id[i-3:i+4]

        if not np.any(np.isnan(window)):

            stop_id_filtered[i] = np.median(window)
    '''    

    df_bus["nearest_stop_id"] = nearest_stop_id

    df_bus["nearest_distance_m"] = nearest_distance

    return df_bus


# =========================================================
# DISTANCE FILTER
# =========================================================

def apply_distance_filter(df_bus):

    #print()
    #print("Distance filter...")

    # =====================================================
    # MATLAB:
    # TYLKO NaN
    # =====================================================

    df_bus.loc[

        df_bus["nearest_distance_m"]
        >
        MAX_STOP_DISTANCE,

        "nearest_stop_id"

    ] = np.nan

    return df_bus

# =========================================================
# DIRECTION
# =========================================================

# =========================================================
# DIRECTION
# MATLAB-COMPATIBLE
# =========================================================

# =========================================================
# DIRECTION
# =========================================================

def compute_direction(df_bus):

    #print()
    #print("Direction...")

    stop_id = df_bus[
        "nearest_stop_id"
    ].to_numpy()

    N = len(stop_id)

    # =====================================================
    # MATLAB:
    # dstop = diff(stop_id)
    # =====================================================

    dstop = np.diff(stop_id)

    # =====================================================
    # DEBUG
    # =====================================================

    dstop_full = np.full(N, np.nan)

    dstop_full[1:] = dstop

    df_bus["dstop"] = dstop_full

    # =====================================================
    # DIRECTION
    # =====================================================

    direction = np.zeros(N)

    for i in range(1, N):

        value = dstop[i - 1]

        if value > 0:

            direction[i] = 1

        elif value < 0:

            direction[i] = -1

        else:

            direction[i] = direction[i - 1]

    df_bus["direction"] = direction

    return df_bus

#########################################################################
# SEGMENTATION
#########################################################################

def segment_courses(df_bus):

    #print()
    #print("Course segmentation...")

    direction = df_bus[
        "direction"
    ].to_numpy()

    N = len(df_bus)

    course_id = np.zeros(N)

    course = 1

    course_id[0] = course

    # =====================================================
    # MATLAB-COMPATIBLE
    # =====================================================

    for i in range(1, N):

        direction_change = (

            direction[i]
            !=
            direction[i - 1]

        )

        valid_direction = (

            direction[i] != 0
            and
            direction[i - 1] != 0

        )

        if direction_change and valid_direction:

            course += 1

        course_id[i] = course

    df_bus["course_id"] = course_id.astype(int)

    return df_bus

# =========================================================
# GLOBAL EXTREMA
# =========================================================

def detect_global_trips(

    df_bus,
    output_dir
):

    print()
    print("Global extrema trips...")

    stop_id = (
        df_bus["nearest_stop_id"]
        .to_numpy()
    )

    # =====================================================
    # GLOBAL MIN / MAX
    # =====================================================

    a = np.nanmin(stop_id)
    b = np.nanmax(stop_id)

    #print()
    #print("GLOBAL EXTREMA:")
    #print(a, b)

    # =====================================================
    # TERMINALS
    # =====================================================

    idx_terminal = np.where(

        (stop_id == a)
        |
        (stop_id == b)

    )[0]

    terminal_values = stop_id[
        idx_terminal
    ]

    # =====================================================
    # FULL TRIPS
    # =====================================================

    trip_ranges = []

    for i in range(

        len(idx_terminal) - 1

    ):

        v1 = terminal_values[i]
        v2 = terminal_values[i + 1]

        # ================================================
        # CHANGE TERMINAL
        # ================================================

        if v1 != v2:

            idx1 = idx_terminal[i]
            idx2 = idx_terminal[i + 1]

            trip_ranges.append([

                idx1,
                idx2,

                int(v1),
                int(v2)
            ])

    trip_df = pd.DataFrame(

        trip_ranges,

        columns=[

            "idx_start",
            "idx_end",

            "start_stop",
            "end_stop"
        ]
    )

    # =====================================================
    # CONTROL PLOT
    # =====================================================

    plt.figure(figsize=(14,6))

    plt.plot(
        stop_id,
        linewidth=1
    )

    plt.plot(

        idx_terminal,

        terminal_values,

        ".r",

        markersize=10
    )

    for _, row in trip_df.iterrows():

        plt.plot(

            [row["idx_start"], row["idx_end"]],

            [row["start_stop"], row["end_stop"]],

            linewidth=3
        )

    plt.grid(True)

    plt.title(
        "Global extrema trips"
    )

    plt.xlabel("Sample")

    plt.ylabel("Stop ID")

    plt.tight_layout()

    plot_path = os.path.join(

        output_dir,

        "global_extrema_trips.png"
    )

    plt.savefig(
        plot_path,
        dpi=300
    )

    plt.close()

    return trip_df

# =========================================================
# TRIP TIME EVALUATION
# =========================================================

def evaluate_trip_times(

    trip_df,
    df_bus
):

    print()
    print("Trip time evaluation...")

    time_vector = (
        df_bus["time"]
        .to_numpy()
    )

    duration_min = []

    for _, row in trip_df.iterrows():

        idx1 = int(
            row["idx_start"]
        )

        idx2 = int(
            row["idx_end"]
        )

        t1 = time_vector[idx1]
        t2 = time_vector[idx2]

        dt = (

            (t2 - t1)
            / np.timedelta64(1, "m")

        )

        duration_min.append(dt)

    trip_df = trip_df.copy()

    trip_df["duration_min"] = (
        np.round(
            duration_min,
            1
        )
    )
    '''
    print()
    print(

        trip_df[[
            "start_stop",
            "end_stop",
            "duration_min"
        ]]
    )
    '''

    return trip_df

# =========================================================
# GLOBAL COURSE QUALITY
# =========================================================

def evaluate_global_courses(

    trip_df,
    course_quality,
    df_bus
):

    print()
    print("Global course quality...")

    # =====================================================
    # MEDIAN TIME
    # =====================================================

    median_time = (
        trip_df["duration_min"]
        .median()
    )

    results = []

    for _, trip in trip_df.iterrows():

        idx1 = int(
            trip["idx_start"]
        )

        idx2 = int(
            trip["idx_end"]
        )

        duration = trip["duration_min"]

        # =================================================
        # TIME QUALITY
        # =================================================

        time_ok = (

            duration >= 0.6 * median_time
            and
            duration <= 1.5 * median_time

        )

        # =================================================
        # LOCAL COURSES INSIDE GLOBAL TRIP
        # =================================================

        idx_range = df_bus.iloc[
            idx1:idx2 + 1
        ]

        local_courses = (
            idx_range["course_id"]
            .unique()
        )

        local_df = course_quality[

            course_quality["course_id"]
            .isin(local_courses)

        ]

        # =================================================
        # LOCAL QUALITY
        # =================================================

        mean_coverage = (
            local_df[
                "stop_coverage"
            ].mean()
        )

        # =================================================
        # GLOBAL QUALITY
        # =================================================

        if (

            time_ok
            and            
            mean_coverage > 0.5

        ):

            quality = "GOOD"

        else:

            quality = "BAD"

        results.append([

            int(trip["start_stop"]),
            int(trip["end_stop"]),

            round(duration, 1),
            round(mean_coverage, 2),

            quality
        ])

    global_df = pd.DataFrame(

        results,

        columns=[

            "start_stop",
            "end_stop",

            "duration_min",

            "mean_coverage",

            "quality"
        ]
    )

    print()
    print(global_df)

    return global_df

# =========================================================
# COURSE QUALITY
# =========================================================

def evaluate_courses(df_bus):

    print()
    print("Course quality...")

    all_stop_id = df_bus[
        "nearest_stop_id"
    ].dropna()

    GLOBAL_AMPLITUDE = (

        all_stop_id.max()
        -
        all_stop_id.min()

    )

    unique_courses = sorted(

        df_bus["course_id"].unique()

    )    

    results = []

    for course in unique_courses:

        idx = (
            df_bus["course_id"]
            == course
        )

        stops_course = df_bus.loc[
            idx,
            "nearest_stop_id"
        ].to_numpy()

        stop_id = stops_course[
            ~np.isnan(stops_course)
        ]
        
        if len(stop_id) == 0:

            continue

        a = stop_id.min()
        b = stop_id.max()

        amplitude = abs(
            b - a
        )

        visited_stops = len(
            np.unique(stop_id)
        )

        stop_coverage = np.round(

            visited_stops
            /
            (amplitude + 1),

            2
        )

        if (

            stop_coverage > 0.8
            and
            amplitude >= 0.7 * GLOBAL_AMPLITUDE

        ):

            quality = "GOOD"

        else:

            quality = "BAD"

        idx_min = stop_id.argmin()
        idx_max = stop_id.argmax()

        # =============================================
        # DIRECTION
        # =============================================

        if idx_min < idx_max:

            direction = 1

            start_stop = a
            end_stop = b

        else:

            direction = -1

            start_stop = b
            end_stop = a

        amplitude = abs(
            b - a
        )

        results.append([

            int(course),

            int(start_stop),
            int(end_stop),

            int(amplitude),

            int(visited_stops),

            float(stop_coverage),

            quality,

            int(direction)
        ])

    results_df = pd.DataFrame(

        results,

        columns=[

            "course_id",

            "start_stop",
            "end_stop",

            "amplitude",

            "visited_stops",

            "stop_coverage",

            "quality",

            "direction"
        ]
    )

    #print()
    #print(results_df)

    return results_df

# =========================================================
# MERGE COURSES
# =========================================================

def merge_courses(

    df_bus,
    course_quality,

    MAX_JOIN_GAP=2,
    SMALL_AMPLITUDE=10
):

    print()
    print("Merge courses...")

    course_quality = (
        course_quality
        .sort_values("course_id")
        .reset_index(drop=True)
    )

    replace_map = {}

    for i in range(

        len(course_quality) - 1

    ):

        row1 = course_quality.iloc[i]
        row2 = course_quality.iloc[i + 1]

        # =================================================
        # PARAMS
        # =================================================

        course1 = row1["course_id"]
        course2 = row2["course_id"]

        end1 = row1["end_stop"]
        start2 = row2["start_stop"]

        amp1 = row1["amplitude"]
        amp2 = row2["amplitude"]

        dir1 = row1["direction"]
        dir2 = row2["direction"]

        # =================================================
        # CONDITIONS
        # =================================================

        same_direction = (
            dir1 == dir2
        )

        close_stops = (
            abs(end1 - start2)
            <=
            MAX_JOIN_GAP
        )

        small_course = True

        # =================================================
        # MERGE
        # =================================================

        if (

            same_direction
            and
            close_stops
            and
            small_course

        ):

            replace_map[
                course2
            ] = course1

    # =====================================================
    # APPLY MAP
    # =====================================================

    for old_id, new_id in replace_map.items():

        df_bus.loc[

            df_bus["course_id"]
            ==
            old_id,

            "course_id"

        ] = new_id

    # =====================================================
    # REINDEX
    # =====================================================

    unique_ids = sorted(
        df_bus["course_id"].unique()
    )

    new_map = {

        old: new
        for new, old
        in enumerate(unique_ids, 1)

    }

    df_bus["course_id"] = (

        df_bus["course_id"]
        .map(new_map)
        .astype(int)

    )

    return df_bus

# =========================================================
# RUN CORE
# =========================================================

def run_segmentation_core(

    df_bus,
    stops_df
):

    # =====================================================
    # NEAREST STOP
    # =====================================================

    df_bus = assign_nearest_stop(
        df_bus,
        stops_df
    )

    # =====================================================
    # DISTANCE FILTER
    # =====================================================

    df_bus = apply_distance_filter(
        df_bus
    )

    df_bus["nearest_stop_id"] = pd.to_numeric(

        df_bus["nearest_stop_id"],

        errors="coerce"
    )

    # =====================================================
    # DIRECTION
    # =====================================================

    df_bus = compute_direction(
        df_bus
    )
    

    # =====================================================
    # SEGMENTATION
    # =====================================================

    df_bus = segment_courses(
        df_bus
    )

    return df_bus


# =========================================================
# MAIN
# =========================================================

def main():
    '''
    print()
    print("====================================")
    print("MATLAB-COMPATIBLE SEGMENTATION")
    print("====================================")
    '''

    # =====================================================
    # CATALOG
    # =====================================================

    catalog_df = read_catalog(
        PATH_CATALOG
    )

    # =====================================================
    # ITERACJA PO PRZYPADKACH
    # =====================================================

    for idx, row in catalog_df.iterrows():

        print()
        print("====================================")
        print(f"CASE {idx + 1}")
        print("====================================")

        # =================================================
        # WALIDACJA
        # =================================================

        valid = validate_case(row)

        if not valid:

            print("Incomplete case -> skipped")

            continue

        try:

            # =============================================
            # PARAMETRY
            # =============================================

            katalog = str(row["KATALOG"])
            #print(katalog)

            mza_csv = str(row["MZA.csv"])
            #print(mza_csv)

            stop_xlsx = str(
                row["stoptimes_1.xlsx"]
            )
            #print(stop_xlsx)

            line_nr = row["line"]
            #print(line_nr)

            vehicle_id = row["vehicle"]
            #print(vehicle_id)

            od_dnia = row["od_dnia"]
            #print(od_dnia)
            od_godz = row["od_godz"]
            #print(od_godz)

            do_dnia = row["do_dnia"]
            #print(do_dnia)
            do_godz = row["do_godz"]
            #print(do_godz)

            # =============================================
            # ŚCIEŻKI
            # =============================================

            path_mza = os.path.join(

                PATH_DATA,
                katalog,
                mza_csv + ".csv"
            )

            #print(path_mza)

            path_stops = os.path.join(

                PATH_DATA,
                katalog,
                stop_xlsx + ".xlsx"
            )

            #print(path_stops)

            # =============================================
            # SPRAWDZENIE PLIKÓW
            # =============================================

            if not os.path.exists(path_mza):

                print("Missing AVL file")

                continue

            if not os.path.exists(path_stops):

                print("Missing stop file")

                continue

            # =============================================
            # OUTPUT DIRECTORY
            # =============================================

            output_dir = create_output_directory(

                PATH_OUTPUT,

                katalog,
                line_nr,
                vehicle_id
            )

            #print()
            #print("OUTPUT:")
            #print(output_dir)

            # =============================================
            # READ DATA
            # =============================================

            df_avl = read_avl_file(
                path_mza
            )

            stops_df = read_stops(
                path_stops
            )

            # =============================================
            # PREPARE AVL
            # =============================================

            df_avl = prepare_avl_data(
                df_avl
            )

            # =============================================
            # FILTER CASE
            # =============================================

            df_bus = filter_case(

                df_avl,

                line_nr,
                vehicle_id,

                od_dnia,
                od_godz,

                do_dnia,
                do_godz
            )

            # =============================================
            # EMPTY
            # =============================================

            if len(df_bus) == 0:

                print()
                print("No data after filters")

                continue

            # =============================================
            # CORE
            # =============================================

            df_bus = run_segmentation_core(

                df_bus,
                stops_df
            )

            course_quality = evaluate_courses(
                df_bus
            )

            trip_df = detect_global_trips(

                df_bus,
                output_dir
            )

            trip_df = evaluate_trip_times(

                trip_df,
                df_bus
            )

            global_quality = evaluate_global_courses(

                trip_df,
                course_quality,
                df_bus
            )

            # =====================================================
            # TRIP SUMMARY CSV
            # =====================================================

            trip_summary = []

            for i in range(len(trip_df)):

                idx1 = int(
                    trip_df.iloc[i]["idx_start"]
                )

                idx2 = int(
                    trip_df.iloc[i]["idx_end"]
                )

                segment = df_bus.iloc[
                    idx1:idx2 + 1
                ]

                direction = 0

                start_stop = int(
                    trip_df.iloc[i]["start_stop"]
                )

                end_stop = int(
                    trip_df.iloc[i]["end_stop"]
                )

                if end_stop > start_stop:

                    direction = 1

                else:

                    direction = -1

                trip_summary.append({

                    "trip_id":
                    i + 1,

                    "vehicle_nr":
                    vehicle_id,

                    "start_time":
                    segment["time"].iloc[0],

                    "end_time":
                    segment["time"].iloc[-1],

                    "duration_min":
                    round(
                        trip_df.iloc[i]["duration_min"],
                        1
                    ),

                    "start_stop":
                    int(
                        trip_df.iloc[i]["start_stop"]
                    ),

                    "end_stop":
                    int(
                        trip_df.iloc[i]["end_stop"]
                    ),

                    "mean_coverage":
                    round(
                        global_quality.iloc[i][
                            "mean_coverage"
                        ],
                        2
                    ),

                    "quality":
                    global_quality.iloc[i][
                        "quality"
                    ],

                    "n_samples":
                    len(segment),

                    "direction":
                    direction,
                })

            trip_summary = pd.DataFrame(
                trip_summary
            )

            if np.any(

                global_quality["quality"]
                == "BAD"

            ):

                print()
                print("BAD CASE -> skipped")

                return

            # =====================================================
            # EXPORT CSV
            # =====================================================

            course_quality.to_csv(

            os.path.join(
                output_dir,
                "course_quality.csv"
            ),

            index=False
            )

            trip_summary.to_csv(

                os.path.join(
                    output_dir,
                    "trip_summary.csv"
                ),

                index=False
            )            
            
            '''
            df_bus = merge_courses(

                df_bus,
                course_quality
            )
            
            course_quality = evaluate_courses(
                df_bus
            )
            '''
            

            create_control_plot(

            df_bus,

            output_dir,

            line_nr,

            vehicle_id
            )

            # =====================================================
            # STOP ID PLOT
            # =====================================================

            #print()
            #print("Stop ID plot...")

            plt.figure(figsize=(16, 6))

            plt.plot(

                df_bus["nearest_stop_id"].to_numpy(),

                linewidth=1
            )

            plt.xlabel("Sample")

            plt.ylabel("nearest_stop_id")

            plt.title(

                f"Nearest stop ID | "
                f"line {line_nr} | "
                f"vehicle {vehicle_id}"
            )

            plt.grid(True)

            plt.tight_layout()

            plt.savefig(

                os.path.join(
                    output_dir,
                    "nearest_stop_id.png"
                ),

                dpi=300
            )

            plt.close()

            
            print("DONE")

        except Exception as e:

            print()
            print("CASE FAILED")
            print(str(e))

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()