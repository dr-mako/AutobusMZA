# =====================================================
# step6_arrival_PRODUCTION.py
#
# AVL vs RACEBOX
#
# STOP ARRIVAL TIME VALIDATION
#
# =====================================================
#
# python step6_arrival_PRODUCTION.py


import os

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

# =========================================================
# PARAMETRY
# =========================================================

PATH_STEP5 = r"OUTPUT_STEP5"

PATH_STEP6 = r"OUTPUT_STEP6"

EDGE_STOPS_TO_REMOVE = 2

OUTLIER_THRESHOLD = 60

# =====================================================
# GLOBAL RESULTS
# =====================================================

global_results = []

all_errors = []

# =========================================================
# CREATE OUTPUT
# =========================================================

os.makedirs(

    PATH_STEP6,

    exist_ok=True
)

# =====================================================
# CASES
# =====================================================

case_dirs = sorted(

    d

    for d in os.listdir(PATH_STEP5)

    if os.path.isdir(
        os.path.join(PATH_STEP5, d)
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

    # =====================================================
    # CASE FILTER
    # =====================================================
    # AVL tego przypadku jest zapisywane bez sekund

    if case_name == "13-05-146_line_146":

        print()
        print(
            "SKIPPED - AVL TIME RESOLUTION INVALID"
        )

        continue

    step5_case = os.path.join(

        PATH_STEP5,

        case_name
    )    

    print()
    print("STEP5:")

    print(
        os.path.exists(
            step5_case
        )
    )

    if not os.path.exists(step5_case):

        print()
        print(
            "CASE SKIPPED"
        )

        continue

    vehicle_dirs = sorted(

        d

        for d in os.listdir(step5_case)

        if os.path.isdir(

            os.path.join(
                step5_case,
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

        print()

        print(vehicle_name)

        step5_vehicle = os.path.join(

            step5_case,

            vehicle_name
        )

        matching_file = os.path.join(

            step5_vehicle,

            "trip_matching.csv"
        )

        print(
            os.path.exists(
                matching_file
            )
        )

        if not os.path.exists(

            matching_file

        ):

            continue

        try:

            df_matching = pd.read_csv(
                matching_file
            )

        except pd.errors.EmptyDataError:

            print()
            print(
                "NO MATCHES"
            )

            continue

        print()

        print("MATCHES:")

        print(
            len(df_matching)
        )

        step3_vehicle = os.path.join(

            "OUTPUT_STEP3",

            case_name,

            vehicle_name
        )

        step4_vehicle = os.path.join(

            "OUTPUT_STEP4",

            case_name,

            vehicle_name
        )

        step6_vehicle = os.path.join(

            PATH_STEP6,

            case_name,

            vehicle_name
        )

        os.makedirs(

            step6_vehicle,

            exist_ok=True
        )

        for _, match_row in df_matching.iterrows():

            avl_trip_id = int(
                match_row["avl_trip_id"]
            )

            rb_trip_id = int(
                match_row["racebox_trip_id"]
            )

            avl_file = os.path.join(

                step3_vehicle,

                f"trip_{avl_trip_id:03d}_arrival_times.csv"
            )

            rb_file = os.path.join(

                step4_vehicle,

                f"trip_{rb_trip_id:03d}_arrival_times.csv"
            )

            df_avl = pd.read_csv(
                avl_file
            )

            df_rb = pd.read_csv(
                rb_file
            )
            '''
            print()
            print("AVL")

            print(df_avl.columns.tolist())

            print()
            print("RACEBOX")

            print(df_rb.columns.tolist())
            '''

            # =====================================================
            # DATETIME
            # =====================================================

            df_avl["arrival_time_corrected"] = pd.to_datetime(
                df_avl["arrival_time_corrected"]
            )

            # AVL jest w czasie lokalnym CEST
            # RaceBox w UTC
            # sprowadzamy AVL do UTC

            df_avl["arrival_time_corrected"] = (

                df_avl["arrival_time_corrected"]

                - pd.Timedelta(hours=2)
            )

            df_rb["arrival_time"] = (

                pd.to_datetime(
                    df_rb["arrival_time"],
                    format="mixed",
                    utc=True
                )

                .dt.tz_convert(None)
            )

            # =====================================
            # DIAGNOSTYKA AVL
            # =====================================

            print()
            print("AVL TIMES SAMPLE")

            print(

                df_avl[
                    [
                        "arrival_time",
                        "arrival_time_corrected"
                    ]
                ].head(20)

            )           

            # =====================================================
            # MERGE
            # =====================================================

            df_compare = pd.merge(

                df_avl,

                df_rb,

                on="stop_sequence",

                suffixes=(

                    "_avl",

                    "_rb"
                )
            ) 

            # =====================================================
            # REMOVE EDGE STOPS
            # =====================================================

            if len(df_compare) > 2 * EDGE_STOPS_TO_REMOVE:

                df_compare = (

                    df_compare

                    .sort_values(
                        "stop_sequence"
                    )

                    .iloc[
                        EDGE_STOPS_TO_REMOVE:
                        -EDGE_STOPS_TO_REMOVE
                    ]

                    .copy()
                )           

            # =====================================================
            # ARRIVAL ERROR
            # =====================================================

            df_compare["arrival_error_s"] = (

                df_compare["arrival_time_corrected"]

                -

                df_compare["arrival_time_rb"]

            ).dt.total_seconds()

            # =====================================================
            # COMMON STOPS
            # =====================================================

            print()
            print("COMMON STOPS:")

            print(
                len(df_compare)
            )

            print()

            print(

                df_compare[

                    [

                        "stop_sequence",

                        "arrival_time_corrected",

                        "arrival_time_rb",

                        "arrival_error_s"

                    ]

                ].head(10)

            )

            # =====================================================
            # ERROR SUMMARY
            # =====================================================

            print()
            print("ERROR SUMMARY")

            print(

                df_compare[
                    "arrival_error_s"
                ].describe()

            )

            # =====================================================
            # OUTLIERS THRESHOLD
            # =====================================================            

            errors = df_compare["arrival_error_s"].values

            valid_mask = np.ones(len(df_compare), dtype=bool)

            for i in range(1, len(df_compare)-1):

                current = abs(errors[i])

                prev = abs(errors[i-1])

                next_ = abs(errors[i+1])

                if (
                    current > OUTLIER_THRESHOLD
                    and
                    prev < OUTLIER_THRESHOLD
                    and
                    next_ < OUTLIER_THRESHOLD
                ):

                    valid_mask[i] = False

            df_compare_filtered = df_compare.loc[
                valid_mask
            ].copy()

            # OUTLIERS REMOVED

            outliers = df_compare.loc[
                ~valid_mask
            ]

            if len(outliers) > 0:

                print()
                print("OUTLIERS REMOVED")

                print(
                    outliers[
                        [
                            "stop_sequence",
                            "arrival_error_s",
                            "arrival_time_corrected",
                            "arrival_time_rb"
                        ]
                    ]
                )

            print()
            print("COMMON STOPS RAW:")
            print(len(df_compare))

            print()
            print("COMMON STOPS FILTERED:")
            print(len(df_compare_filtered))

            print()
            print("MAX ABS ERROR:")

            print(
                np.max(
                    np.abs(
                        df_compare_filtered["arrival_error_s"]
                    )
                )
            )

            print()
            print("LARGEST ERRORS")

            print(
                df_compare_filtered.loc[
                    np.abs(df_compare_filtered["arrival_error_s"]) > 60,
                    [
                        "stop_sequence",
                        "arrival_error_s"
                    ]
                ]
            )

            # METRYKI
            errors = df_compare_filtered[
                "arrival_error_s"
            ]

            all_errors.extend(
                errors.tolist()
            )

            mae = np.abs(errors).mean()

            rmse = np.sqrt(
                np.mean(errors**2)
            )

            median = errors.median()

            max_abs = np.abs(errors).max()

            p95 = np.percentile(
                np.abs(errors),
                95
            )

            n_stops = len(
                df_compare_filtered
            )

            global_results.append({

                "case":
                    case_name,

                "vehicle":
                    vehicle_name,

                "avl_trip":
                    avl_trip_id,

                "racebox_trip":
                    rb_trip_id,

                "n_stops":
                    n_stops,

                "mae_s":
                    mae,

                "rmse_s":
                    rmse,

                "median_s":
                    median,

                "max_abs_s":
                    max_abs,

                "p95_abs_s":
                    p95
            })

            # SAVE
            comparison_file = os.path.join(

                step6_vehicle,

                f"trip_{avl_trip_id:03d}_comparison.csv"
            )


            df_compare_filtered[
                [
                    "stop_sequence",
                    "arrival_time_corrected",
                    "arrival_time_rb",
                    "arrival_error_s"
                ]
            ].to_csv(
                comparison_file,
                index=False
            )

            print()
            print("SAVED:")

            print(comparison_file)

# =====================================================
# GLOBAL SUMMARY
# =====================================================

summary_df = pd.DataFrame(
    global_results
)

summary_file = os.path.join(

    PATH_STEP6,

    "validation_summary.csv"
)

summary_df.to_csv(

    summary_file,

    index=False
)

print()
print("GLOBAL SUMMARY SAVED")

print(summary_file)

print()
print("OVERALL RESULTS")

print()

print(
    summary_df[
        [
            "mae_s",
            "rmse_s",
            "median_s",
            "max_abs_s"
        ]
    ].describe()
)

all_errors = np.array(all_errors)

print()
print("GLOBAL STOP-LEVEL RESULTS")

print()

print(
    f"N stops: {len(all_errors)}"
)

print(
    f"MAE: {np.mean(np.abs(all_errors)):.2f}"
)

print(
    f"RMSE: {np.sqrt(np.mean(all_errors**2)):.2f}"
)

print(
    f"Median: {np.median(all_errors):.2f}"
)

print(
    f"P95: {np.percentile(np.abs(all_errors),95):.2f}"
)

print(
    f"Max abs: {np.max(np.abs(all_errors)):.2f}"
)

print()
print("TRIPS ANALYSED:")

print(
    len(summary_df)
)

print()
print("TOTAL STOPS:")

print(
    summary_df["n_stops"].sum()
)