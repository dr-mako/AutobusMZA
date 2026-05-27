# step_2_racebox_trip_separator.py
#  =========================================================
# RACEBOX PRODUCTION SEGMENTATION SYSTEM
# =========================================================
#
# STEP1 ARCHITECTURE
# +
# STEP2 SEGMENTATION ENGINE
#
# =========================================================

import os
import glob
import warnings

import numpy as np
import pandas as pd

from pathlib import Path

from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2

import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# =========================================================
# PARAMETRY
# =========================================================

PATH_CATALOG = r"DANE/Katalog.xlsx"

PATH_DATA = r"DANE"

PATH_OUTPUT = r"OUTPUT"

MAX_STOP_DISTANCE = 120

TERMINAL_DWELL_TIME = 120

LOW_SPEED_THRESHOLD = 3

TRIM_SAMPLES = 15

#DOWNSAMPLE = 5

# =========================================================
# HAVERSINE
# =========================================================

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

# =========================================================
# READ CATALOG
# =========================================================

def read_catalog(path_catalog):

    print()
    print("Reading catalog...")

    df = pd.read_excel(path_catalog)

    required_columns = [

        "KATALOG",

        "RaceBox.csv",

        "stoptimes_1.xlsx",

        "vehicle",

        "od_dnia",
        "od_godz",

        "do_dnia",
        "do_godz"
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

    required = [

        "KATALOG",

        "RaceBox.csv",

        "stoptimes_1.xlsx",

        "vehicle"
    ]

    for field in required:

        value = row[field]

        if pd.isna(value):

            return False

        if str(value).strip() == "":

            return False

    return True

# =========================================================
# OUTPUT DIRECTORY
# =========================================================

def create_output_directory(

    output_root,
    racebox_name,
    vehicle_id
):

    output_dir = (

        Path(output_root)

        /

        f"{racebox_name}"

        /

        f"vehicle_{vehicle_id}"
    )

    output_dir.mkdir(

        parents=True,
        exist_ok=True
    )

    return str(output_dir)

# =========================================================
# READ RACEBOX
# =========================================================

def read_racebox(path_csv):

    print()
    print("Reading RaceBox...")

    df = pd.read_csv(path_csv)

    rename_dict = {

        "Latitude": "lat",
        "Longitude": "lon"
    }

    df = df.rename(
        columns=rename_dict
    )

    return df

# =========================================================
# READ STOPS
# =========================================================

def read_stops(path_excel):

    print()
    print("Reading stops...")

    df = pd.read_excel(
        path_excel
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
# PREPARE GPS
# =========================================================

def prepare_gps(df):

    print()
    print("Preparing GPS...")

    # =====================================================
    # TIME
    # =====================================================

    df["Time"] = pd.to_datetime(

        df["Time"],

        errors="coerce"
    )

    # =====================================================
    # DROP NaN
    # =====================================================

    df = df.dropna(

        subset=[

            "lat",
            "lon",
            "Time"
        ]

    ).copy()

    # =====================================================
    # SORT
    # =====================================================

    df = df.sort_values(
        "Time"
    )

    df = df.reset_index(
        drop=True
    )

    # =====================================================
    # MATLAB DOWNSAMPLING
    # =====================================================

    df = df.iloc[::7].copy()

    df = df.reset_index(
        drop=True
    )

    return df

# =========================================================
# OPTIONAL TIME FILTER
# =========================================================

def apply_time_filter(

    df,

    od_dnia,
    od_godz,

    do_dnia,
    do_godz
):

    print()
    print("Time filter...")

    # =====================================================
    # EMPTY
    # =====================================================

    if (

        pd.isna(od_dnia)
        or
        pd.isna(od_godz)

    ):

        return df

    # =====================================================
    # START
    # =====================================================

    start_day = int(od_dnia)
    start_hour = int(od_godz)

    # =====================================================
    # END
    # =====================================================

    if (

        pd.isna(do_dnia)
        or
        pd.isna(do_godz)

    ):

        end_day = start_day
        end_hour = 23

    else:

        end_day = int(do_dnia)
        end_hour = int(do_godz)

    # =====================================================
    # VECTOR
    # =====================================================

    day = df["Time"].dt.day

    hour = df["Time"].dt.hour

    # =====================================================
    # SAME DAY
    # =====================================================

    if start_day == end_day:

        idx = (

            (day == start_day)

            &

            (hour >= start_hour)

            &

            (hour <= end_hour)
        )

    # =====================================================
    # OVER MIDNIGHT
    # =====================================================

    else:

        idx = (

            (

                (day == start_day)

                &

                (hour >= start_hour)

            )

            |

            (

                (day == end_day)

                &

                (hour <= end_hour)

            )
        )

    df = df[idx].copy()

    df = df.reset_index(
        drop=True
    )

    print()
    print("After time filter:")
    print(len(df))

    return df
'''
# =========================================================
# SPEED
# =========================================================

def compute_speed(df):

    print()
    print("Speed estimation...")

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

            df.iloc[i]["Time"]

            -

            df.iloc[i-1]["Time"]

        ).total_seconds()

        time_s[i] = dt

        if dt > 0:

            speed_kmh[i] = (

                d / dt

            ) * 3.6

    df["speed_kmh"] = speed_kmh

    df["distance_m"] = distance_m

    df["time_s"] = time_s

    return df
'''
# =========================================================
# NEAREST STOP
# =========================================================

def assign_nearest_stop(

    df,
    stops_df
):

    print()
    print("Nearest stop assignment...")

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

    N = len(df)

    N_stops = len(stops_df)

    nearest_stop_id = []

    nearest_distance = []

    for i in range(N):
        '''
        if i % 1000 == 0:

            print(
                f"{i} / {N}"
            )
        '''
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

        dist_all = np.array(
            dist_all
        )

        idx_min = np.argmin(
            dist_all
        )

        nearest_stop_id.append(

            stop_sequence[idx_min]
        )

        nearest_distance.append(

            dist_all[idx_min]
        )

    df["nearest_stop_id"] = nearest_stop_id

    df["nearest_distance_m"] = nearest_distance

    return df

# =========================================================
# DISTANCE FILTER
# =========================================================

def apply_distance_filter(df):

    print()
    print("Distance filter...")

    df.loc[

        df["nearest_distance_m"]
        >
        MAX_STOP_DISTANCE,

        "nearest_stop_id"

    ] = np.nan

    return df

# =========================================================
# SPLIT CONSECUTIVE
# =========================================================

def split_consecutive(idx):

    idx = np.array(idx)

    # =====================================================
    # EMPTY
    # =====================================================

    if len(idx) == 0:

        return []

    # =====================================================
    # DIFFERENCES
    # =====================================================

    d = np.diff(idx)

    # =====================================================
    # BREAKS
    # =====================================================

    breaks = np.where(d > 1)[0]

    # =====================================================
    # GROUPS
    # =====================================================

    groups = []

    start = 0

    for b in breaks:

        groups.append(

            idx[start:b+1]
        )

        start = b + 1

    # =====================================================
    # LAST GROUP
    # =====================================================

    groups.append(

        idx[start:]
    )

    return groups

# =========================================================
# DIRECTION
# =========================================================

def compute_direction(df):

    print()
    print("Direction...")

    # =====================================================
    # REMOVE NaN EXACTLY LIKE MATLAB
    # =====================================================

    df = df.dropna(
        subset=["nearest_stop_id"]
    ).copy()

    df = df.reset_index(
        drop=True
    )

    # =====================================================
    # DIFF
    # =====================================================

    dstop = df[
        "nearest_stop_id"
    ].diff()

    N = len(df)

    direction = np.zeros(N)

    for i in range(1, N):

        if dstop.iloc[i] > 0:

            direction[i] = 1

        elif dstop.iloc[i] < 0:

            direction[i] = -1

        else:

            direction[i] = direction[i - 1]

    df["direction"] = direction

    return df

# =========================================================
# SEGMENT COURSES
# =========================================================

def segment_courses(df):

    print()
    print("Segment courses...")

    direction = (
        df["direction"]
        .to_numpy()
    )

    N = len(df)

    course_id = np.zeros(
        N,
        dtype=int
    )

    course = 1

    course_id[0] = course

    for i in range(1, N):

        # =================================================
        # DIRECTION CHANGE
        # =================================================

        if direction[i] != direction[i - 1]:

            # =============================================
            # IGNORE ZERO
            # =============================================

            if (

                direction[i] != 0
                and
                direction[i - 1] != 0

            ):

                course += 1

        course_id[i] = course

    df["course_id"] = course_id

    return df


# =========================================================
# EVALUATE COURSES
# =========================================================

def evaluate_courses(df):

    print()
    print("Evaluate courses...")

    rows = []

    for course in sorted(
        df["course_id"].unique()
    ):

        trip_df = df[
            df["course_id"] == course
        ]

        # =================================================
        # BASIC
        # =================================================

        n_samples = len(trip_df)

        start_time = trip_df[
            "Time"
        ].iloc[0]

        end_time = trip_df[
            "Time"
        ].iloc[-1]

        start_stop = trip_df[
            "nearest_stop_id"
        ].iloc[0]

        end_stop = trip_df[
            "nearest_stop_id"
        ].iloc[-1]

        # =================================================
        # AMPLITUDE
        # =================================================

        amplitude = (

            trip_df[
                "nearest_stop_id"
            ].max()

            -

            trip_df[
                "nearest_stop_id"
            ].min()
        )

        # =================================================
        # COVERAGE
        # =================================================

        n_unique_stops = (

            trip_df[
                "nearest_stop_id"
            ]

            .nunique()
        )

        # =================================================
        # ROW
        # =================================================

        rows.append({

            "course_id":
            int(course),

            "n_samples":
            n_samples,

            "start_time":
            start_time,

            "end_time":
            end_time,

            "start_stop":
            start_stop,

            "end_stop":
            end_stop,

            "amplitude":
            amplitude,

            "n_unique_stops":
            n_unique_stops
        })

    course_quality = pd.DataFrame(
        rows
    )

    return course_quality

# =========================================================
# TERMINAL SEGMENTATION
# =========================================================

def terminal_segmentation(df):

    print()
    print("Terminal segmentation...")

    # =====================================================
    # REMOVE NaN
    # =====================================================

    df = df.dropna(
        subset=["nearest_stop_id"]
    ).copy()

    df = df.reset_index(
        drop=True
    )

    # =====================================================
    # STOP ID
    # =====================================================

    stop_id = (
        df["nearest_stop_id"]
        .to_numpy()
    )

    # =====================================================
    # GLOBAL TERMINALS
    # =====================================================

    a = np.min(stop_id)

    b = np.max(stop_id)

    print()
    print("GLOBAL TERMINALS:")
    print(a, b)

    # =====================================================
    # TERMINAL INDICES
    # =====================================================

    pocz = np.where(
        stop_id == a
    )[0]

    kon = np.where(
        stop_id == b
    )[0]

    # =====================================================
    # GROUP TERMINALS
    # =====================================================

    pocz_groups = split_consecutive(
        pocz
    )

    kon_groups = split_consecutive(
        kon
    )

    # =====================================================
    # ARRIVAL / DEPARTURE
    # =====================================================

    przyj_pocz = []
    odj_pocz = []

    for g in pocz_groups:

        przyj_pocz.append(
            int(np.min(g))
        )

        odj_pocz.append(
            int(np.max(g))
        )

    przyj_konc = []
    odj_konc = []

    for g in kon_groups:

        przyj_konc.append(
            int(np.min(g))
        )

        odj_konc.append(
            int(np.max(g))
        )

    # =====================================================
    # TERMINAL EVENTS
    # =====================================================

    terminal_events = []

    # -----------------------------------------------------
    # A TERMINAL
    # -----------------------------------------------------

    for i in range(len(odj_pocz)):

        terminal_events.append({

            "terminal": a,

            "depart_idx": odj_pocz[i]
        })

    # -----------------------------------------------------
    # B TERMINAL
    # -----------------------------------------------------

    for i in range(len(odj_konc)):

        terminal_events.append({

            "terminal": b,

            "depart_idx": odj_konc[i]
        })

    # =====================================================
    # SORT CHRONOLOGICALLY
    # =====================================================

    terminal_events = sorted(

        terminal_events,

        key=lambda x: x["depart_idx"]
    )

    # =====================================================
    # COURSE ID
    # =====================================================

    course_id = np.zeros(
        len(df),
        dtype=int
    )

    trip_ranges = []

    course = 1

    # =====================================================
    # BUILD TRIPS
    # =====================================================

    for i in range(

        len(terminal_events) - 1
    ):

        e1 = terminal_events[i]

        e2 = terminal_events[i + 1]

        # -------------------------------------------------
        # MUST CHANGE TERMINAL
        # -------------------------------------------------

        if e1["terminal"] == e2["terminal"]:

            continue

        idx_start = e1["depart_idx"]

        idx_end = e2["depart_idx"]

        # -------------------------------------------------
        # VALID
        # -------------------------------------------------

        if idx_end <= idx_start:

            continue

        course_id[
            idx_start:idx_end+1
        ] = course

        trip_ranges.append([

            course,

            idx_start,
            idx_end,

            e1["terminal"],
            e2["terminal"]
        ])

        course += 1

    # =====================================================
    # SAVE COURSE ID
    # =====================================================

    df["course_id"] = course_id

    trip_table = pd.DataFrame(

        trip_ranges,

        columns=[

            "course_id",

            "idx_start",
            "idx_end",

            "start_stop",
            "end_stop"
        ]
    )

    return df, trip_table

# =========================================================
# RUN CORE
# =========================================================

def run_segmentation_core(

    df,
    stops_df
):

    # =====================================================
    # NEAREST STOP
    # =====================================================

    df = assign_nearest_stop(

        df,
        stops_df
    )

    # =====================================================
    # DISTANCE FILTER
    # =====================================================

    df = apply_distance_filter(df)

    # =====================================================
    # DIRECTION
    # =====================================================

    df = compute_direction(df)

    # =====================================================
    # SEGMENT COURSES
    # =====================================================

    df = segment_courses(df)

    return df

# =========================================================
# GLOBAL EXTREMA TRIPS
# =========================================================

def detect_global_trips(df):

    print()
    print("Global extrema trips...")

    stop_id = (
        df["nearest_stop_id"]
        .to_numpy()
    )

    # =====================================================
    # GLOBAL MIN / MAX
    # =====================================================

    a = np.nanmin(stop_id)

    b = np.nanmax(stop_id)

    print()
    print("GLOBAL EXTREMA:")
    print(a, b)

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

        # =================================================
        # CHANGE TERMINAL
        # =================================================

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

    return trip_df



# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # CATALOG
    # =====================================================

    catalog_df = read_catalog(
        PATH_CATALOG
    )

    # =====================================================
    # LOOP
    # =====================================================

    for idx, row in catalog_df.iterrows():

        print()
        print("===================================")
        print(f"CASE {idx + 1}")
        print("===================================")

        # =================================================
        # VALIDATE
        # =================================================

        valid = validate_case(row)

        if not valid:

            print("Incomplete case -> skipped")

            continue

        try:

            # =============================================
            # PARAMS
            # =============================================

            katalog = str(
                row["KATALOG"]
            )

            racebox_name = str(
                row["RaceBox.csv"]
            )

            stop_name = str(
                row["stoptimes_1.xlsx"]
            )

            vehicle_id = row["vehicle"]

            od_dnia = row["od_dnia"]
            od_godz = row["od_godz"]

            do_dnia = row["do_dnia"]
            do_godz = row["do_godz"]

            # =============================================
            # PATHS
            # =============================================

            path_racebox = os.path.join(

                PATH_DATA,

                katalog,

                racebox_name + ".csv"
            )

            path_stops = os.path.join(

                PATH_DATA,

                katalog,

                stop_name + ".xlsx"
            )
            # =============================================
            # EXISTS
            # =============================================

            if not os.path.exists(path_racebox):

                print("Missing RaceBox file")

                continue

            if not os.path.exists(path_stops):

                print("Missing stops file")

                continue

            # =============================================
            # OUTPUT
            # =============================================

            output_dir = create_output_directory(

                PATH_OUTPUT,

                racebox_name,

                vehicle_id
            )

            # =============================================
            # READ
            # =============================================

            df = read_racebox(
                path_racebox
            )

            stops_df = read_stops(
                path_stops
            )

            # =============================================
            # PREPARE
            # =============================================

            df = prepare_gps(df)

            # =============================================
            # TIME FILTER
            # =============================================
            '''
            df = apply_time_filter(

                df,

                od_dnia,
                od_godz,

                do_dnia,
                do_godz
            )
            '''
            # =============================================
            # EMPTY
            # =============================================

            if len(df) == 0:

                print()
                print("No data after filters")

                continue

            # =============================================
            # CORE
            # =============================================

            df = run_segmentation_core(

                df,
                stops_df
            )

            # =====================================================
            # COURSE QUALITY
            # =====================================================

            course_quality = evaluate_courses(
                df
            )

            # =====================================================
            # MINIMUM COURSE SIZE
            # =====================================================

            MIN_AMPLITUDE = 5

            good_ids = (

                course_quality[

                    course_quality[
                        "n_unique_stops"
                    ]

                    >

                    MIN_AMPLITUDE

                ]["course_id"]

                .to_list()
            )

            # =====================================================
            # FILTER GOOD COURSES
            # =====================================================

            df = df[

                df["course_id"]
                .isin(good_ids)

            ].copy()

            df = df.reset_index(
                drop=True
            )

            print()
            print("GOOD COURSES:")
            print(sorted(good_ids))

            
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

                # -------------------------------------------------
                # FILENAME
                # -------------------------------------------------

                filename = (
                    f"trip_{int(course):03d}.csv"
                )

                path = os.path.join(
                    output_dir,
                    filename
                )

                # -------------------------------------------------
                # SAVE
                # -------------------------------------------------

                trip_df.to_csv(

                    path,

                    index=False
                )

                print("Zapisano:")
                print(path)

                

            # =====================================================
            # GLOBAL TERMINALS
            # =====================================================

            a = df[
                "nearest_stop_id"
            ].min()

            b = df[
                "nearest_stop_id"
            ].max()

            # =====================================================
            # CONTROL PLOT
            # =====================================================

            print()
            print("Control plot...")

            plt.figure(figsize=(16, 7))

            unique_courses = sorted(
                df["course_id"].unique()
            )

            n_courses = len(unique_courses)

            # =====================================================
            # COLORS
            # =====================================================

            cmap = plt.cm.get_cmap(

                "tab20",

                min(max(n_courses, 1), 20)
            )

            # =====================================================
            # LOOP
            # =====================================================

            for i, course in enumerate(unique_courses):

                trip_df = df[
                    df["course_id"] == course
                ]

                color = cmap(i % 20)

                # =================================================
                # REMOVE REPEATED STOPS
                # =================================================

                idx_keep = np.concatenate([

                    [True],

                    np.diff(

                        trip_df[
                            "nearest_stop_id"
                        ]

                    ) != 0
                ])

                trip_df = trip_df[
                    idx_keep
                ].copy()

                # -------------------------------------------------
                # SCATTER
                # -------------------------------------------------

                plt.scatter(

                    trip_df["Time"],

                    trip_df["nearest_stop_id"],

                    s=4,

                    color=color,

                    alpha=0.7
                )
                
                # -------------------------------------------------
                # LINE
                # -------------------------------------------------

                plt.plot(

                    trip_df["Time"],

                    trip_df["nearest_stop_id"],

                    linewidth=1.2,

                    color=color,

                    alpha=0.9
                )

                # =========================================
                # DURATION
                # =========================================

                duration_min = (

                    time_ab[1]
                    -
                    time_ab[0]

                ).total_seconds() / 60

                # =========================================
                # SUMMARY
                # =========================================

                summary_rows.append({

                    "vehicle_id":

                        vehicle_id,

                    "course_id":

                        int(course),

                    "start_time":

                        time_ab[0],

                    "end_time":

                        time_ab[1],

                    "start_stop":

                        int(stop_terminal[0]),

                    "end_stop":

                        int(stop_terminal[1]),

                    "direction":

                        int(dir_mode),

                    "duration_min":

                        duration_min
                })

                # =================================================
                # COURSE DIRECTION
                # =================================================

                dir_course = trip_df[
                    "direction"
                ]

                dir_course = dir_course[
                    dir_course != 0
                ]

                if len(dir_course) == 0:

                    continue

                # dominant direction
                dir_mode = dir_course.mode()

                if len(dir_mode) == 0:

                    continue

                dir_mode = dir_mode.iloc[0]

                # =================================================
                # TERMINALS
                # =================================================

                if dir_mode == 1:

                    stop_terminal = [a, b]

                else:

                    stop_terminal = [b, a]

                # =================================================
                # DATA
                # =================================================

                u_stop = trip_df[
                    "nearest_stop_id"
                ].to_numpy()

                t_med = trip_df[
                    "Time"
                ].to_numpy()

                # =================================================
                # QUALITY
                # =================================================

                if (

                    len(u_stop) > 10

                    and

                    np.min(u_stop) - a <= 5

                    and

                    np.max(u_stop) - b <= 5
                ):

                    # =============================================
                    # SORT FOR INTERPOLATION
                    # =============================================

                    idx_sort = np.argsort(
                        u_stop
                    )

                    u_sort = u_stop[
                        idx_sort
                    ]

                    t_sort = t_med[
                        idx_sort
                    ]

                    # =============================================
                    # REMOVE DUPLICATES
                    # =============================================

                    u_unique, idx_unique = np.unique(

                        u_sort,

                        return_index=True
                    )

                    t_unique = t_sort[
                        idx_unique
                    ]

                    # =============================================
                    # INTERPOLATION
                    # =============================================

                    try:

                        time_ab = np.interp(

                            stop_terminal,

                            u_unique,

                            t_unique.astype(
                                "datetime64[s]"
                            ).astype(np.int64)
                        )

                        time_ab = pd.to_datetime(
                            time_ab,
                            unit="s"
                        )

                        # =========================================
                        # LINE
                        # =========================================

                        plt.plot(

                            time_ab,

                            stop_terminal,

                            "-",

                            color=color,

                            linewidth=2
                        )

                    except:

                        pass
            
                        # =====================================================
            # FINAL SUMMARY
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
            # LABELS
            # =====================================================

            plt.xlabel("Time")

            plt.ylabel("Stop sequence")

            plt.title(

                f"RaceBox segmentation | "
                f"vehicle {vehicle_id}"
            )

            plt.grid(True)

            plt.tight_layout()

            # =====================================================
            # SAVE
            # =====================================================

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

            print()
            print("Zapisano:")
            print(plot_path)

            print()
            print("Trips detected:")

            print(
                sorted(
                    df["course_id"].unique()
                )
            )

            print()
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