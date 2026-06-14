# =========================================================
# STEP 5
# =========================================================
#
# python step5_PRODUCTION.py 
#
# =========================================================
# STEP5 TRIP AVL-RACE_BOX MATCHUNG
# =========================================================
#

import os
import warnings

import pandas as pd
import numpy as np
import glob

warnings.filterwarnings("ignore")

# =========================================================
# PARAMETRY
# =========================================================

PATH_STEP3 = r"OUTPUT_STEP3"

PATH_STEP4 = r"OUTPUT_STEP4"

PATH_STEP5 = r"OUTPUT_STEP5"

# =========================================================
# CREATE OUTPUT
# =========================================================

os.makedirs(

    PATH_STEP5,

    exist_ok=True
)

# =====================================================
# BUILD TRIP SUMMARY
# =====================================================

def build_trip_summary(arrival_file):

    df = pd.read_csv(
        arrival_file
    )

    start_time = pd.to_datetime(

        df["arrival_time"].iloc[0]

    )

    end_time = pd.to_datetime(

        df["arrival_time"].iloc[-1]

    )

    if start_time.tzinfo is not None:

        start_time = (
            start_time
            .tz_convert(None)
            +
            pd.Timedelta(hours=2)
        )

    if end_time.tzinfo is not None:

        end_time = (
            end_time
            .tz_convert(None)
            +
            pd.Timedelta(hours=2)
        )

    duration_s = (

        end_time
        -
        start_time

    ).total_seconds()

    trip_id = int(

        os.path.basename(
            arrival_file
        )

        .split("_")[1]
    )

    direction = int(

        df["direction"].iloc[0]

    )

    if direction == 2:

        direction = -1

    return {

        "trip_id":
            trip_id,

        "direction":
            direction,

        "start_time":
            start_time,

        "end_time":
            end_time,

        "duration_s":
            duration_s,

        "n_stops":
            len(df)
    }

# =====================================================
# CASES
# =====================================================

case_dirs = sorted(

    d

    for d in os.listdir(PATH_STEP3)

    if os.path.isdir(
        os.path.join(PATH_STEP3, d)
    )
)

# =====================================================
# LOOP
# =====================================================

for case_name in case_dirs:

    print()
    print("===================================")

    print(
        f"CASE: {case_name}"
    )

    print("===================================")

    step3_case = os.path.join(

        PATH_STEP3,

        case_name
    )

    step4_case = os.path.join(

        PATH_STEP4,

        case_name
    )

    print()
    print("STEP3:")

    print(
        os.path.exists(
            step3_case
        )
    )

    print()
    print("STEP4:")

    print(
        os.path.exists(
            step4_case
        )
    )

    if not os.path.exists(step4_case):

        print()
        print(
            "CASE SKIPPED"
        )

        continue

    vehicle_dirs = sorted(

        d

        for d in os.listdir(step3_case)

        if os.path.isdir(

            os.path.join(
                step3_case,
                d
            )
        )
    )

    print()
    print("VEHICLES:")

    print(
        len(vehicle_dirs)
    )

    for vehicle_name in vehicle_dirs:

        vehicle_step5_dir = os.path.join(

            PATH_STEP5,

            case_name,

            vehicle_name

        )

        os.makedirs(

            vehicle_step5_dir,

            exist_ok=True

        )

        print()
        print(
            vehicle_name
        )

        step3_vehicle = os.path.join(

            step3_case,

            vehicle_name
        )

        step4_vehicle = os.path.join(

            step4_case,

            vehicle_name
        )

        print(
            os.path.exists(
                step4_vehicle
            )
        )

        avl_files = sorted(

            glob.glob(

                os.path.join(

                    step3_vehicle,

                    "*arrival_times.csv"
                )
            )
        )

        rb_files = sorted(

            glob.glob(

                os.path.join(

                    step4_vehicle,

                    "*arrival_times.csv"
                )
            )
        )

        print()
        print("AVL ARRIVALS:")

        print(
            len(avl_files)
        )

        print()
        print("RACEBOX ARRIVALS:")

        print(
            len(rb_files)
        )

        avl_summary = []

        for f in avl_files:

            avl_summary.append(

                build_trip_summary(f)

            )

        rb_summary = []

        for f in rb_files:

            rb_summary.append(

                build_trip_summary(f)

            )

        df_avl = pd.DataFrame(
            avl_summary
        )

        df_rb = pd.DataFrame(
            rb_summary
        )

        print()
        print("AVL SUMMARY")

        if len(df_avl) == 0:

            print(
                "NO AVL ARRIVAL FILES"
            )

        else:

            print(

                df_avl[
                    [
                        "trip_id",
                        "direction",
                        "start_time",
                        "end_time",
                        "n_stops"
                    ]
                ]

            )
        print()
        print("RACEBOX SUMMARY")

        print(
            df_rb[
                [
                    "trip_id",
                    "direction",
                    "start_time",
                    "end_time",
                    "n_stops"
                ]
            ]
        )

        # =========================================
        # MATCHING
        # =========================================

        print()
        print("TRIP MATCHING")

        used_rb = set()

        matches = []

        for _, avl_row in df_avl.iterrows():

            best_score = np.inf

            best_match = None

            for _, rb_row in df_rb.iterrows():

                rb_id = rb_row["trip_id"]

                if rb_id in used_rb:

                    continue

                # ==========================
                # DIRECTION
                # ==========================

                if (
                    avl_row["direction"]
                    !=
                    rb_row["direction"]
                ):

                    continue

                # ==========================
                # TIME DIFFERENCES
                # ==========================

                start_diff = abs(

                    (
                        avl_row["start_time"]
                        -
                        rb_row["start_time"]
                    ).total_seconds()

                )

                end_diff = abs(

                    (
                        avl_row["end_time"]
                        -
                        rb_row["end_time"]
                    ).total_seconds()

                )

                duration_avl = (

                    avl_row["end_time"]
                    -
                    avl_row["start_time"]

                ).total_seconds()

                duration_rb = (

                    rb_row["end_time"]
                    -
                    rb_row["start_time"]

                ).total_seconds()

                duration_diff = abs(

                    duration_avl
                    -
                    duration_rb

                )

                # ==========================
                # GATES
                # ==========================

                if start_diff > 3600:

                    continue

                if end_diff > 3600:

                    continue

                # ==========================
                # SCORE
                # ==========================

                score = (

                    start_diff
                    +
                    end_diff
                    +
                    duration_diff

                )

                if score < best_score:

                    best_score = score

                    best_match = {

                        "case":
                            case_name,

                        "vehicle":
                            vehicle_name,

                        "avl_trip_id":
                            avl_row["trip_id"],

                        "racebox_trip_id":
                            rb_row["trip_id"],

                        "direction":
                            avl_row["direction"],

                        "start_diff_s":
                            round(start_diff, 1),

                        "end_diff_s":
                            round(end_diff, 1),

                        "duration_diff_s":
                            round(duration_diff, 1),

                        "score":
                            round(score, 1)
                    }

            if best_match is not None:

                if best_score > 1200:

                    continue

                used_rb.add(

                    best_match[
                        "racebox_trip_id"
                    ]
                )

                matches.append(
                    best_match
                )

        # =========================================
        # MATCHES DATAFRAME
        # =========================================

        df_matches = pd.DataFrame(
            matches
        )

        print()
        print("MATCHES")

        print(df_matches)

        output_match = os.path.join(

            vehicle_step5_dir,

            "trip_matching.csv"

        )

        df_matches.to_csv(

            output_match,

            index=False

        )

        print()
        print("SAVED")

        print(output_match)

        summary_df = pd.DataFrame([

            {

                "case":
                    case_name,

                "vehicle":
                    vehicle_name,

                "n_avl":
                    len(df_avl),

                "n_racebox":
                    len(df_rb),

                "n_matches":
                    len(df_matches),

                "matching_ratio_avl":

                    round(

                        100
                        *
                        len(df_matches)
                        /
                        max(len(df_avl), 1),

                        1

                    ),

                "matching_ratio_racebox":

                    round(

                        100
                        *
                        len(df_matches)
                        /
                        max(len(df_rb), 1),

                        1

                    )

            }

        ])

        output_summary = os.path.join(

            vehicle_step5_dir,

            "matching_summary.csv"

        )

        summary_df.to_csv(

            output_summary,

            index=False

        )

        print()
        print("SUMMARY SAVED")

        print(output_summary)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("===================================")
    print("STEP5 TRIP AVL-RACE_BOX MATCHUNG")
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
            # LOAD TOPOLOGY
            # =============================================

            df_topology = load_topology(

                case_paths["path_topology"]
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
            # TIME RANGE
            # =============================================

            print()
            print("AVL time range:")

            print(
                df_avl["vehicle_time"].iloc[0]
            )

            print(
                df_avl["vehicle_time"].iloc[-1]
            )

            print()
            print("Trip range:")

            print(
                df_trip_summary[
                    "start_time"
                ].min()
            )

            print(
                df_trip_summary[
                    "end_time"
                ].max()
            )

            print()
            print("READY FOR RECONSTRUCTION")

        except Exception as e:

            print()
            print("CASE FAILED")

            print(str(e))

