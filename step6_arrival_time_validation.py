# =====================================================
# step6_arrival_time_validation.py
#
# AVL vs RACEBOX
#
# STOP ARRIVAL TIME VALIDATION
#
# =====================================================

import os

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

# =====================================================
# PARAMETRY
# =====================================================



# =====================================================
# PATHS
# =====================================================

base_dir = os.getcwd()

step3_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP3"
)

step4_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP4"
)

step5_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP5"
)

step6_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP6"
)

os.makedirs(
    step6_dir,
    exist_ok=True
)

# =====================================================
# LOAD MATCHING
# =====================================================

matching_file = os.path.join(

    step5_dir,
    "trip_matching.csv"
)

df_matching = pd.read_csv(
    matching_file
)

print()
print("===================================")
print("MATCHED PAIRS")
print("===================================")

print(df_matching[[
    "avl_course_id",
    "racebox_course_id",
    "confidence"
]])

# =====================================================
# LOOP
# =====================================================

global_metrics = []

for _, match_row in df_matching.iterrows():

    AVL_TRIP = int(
        match_row["avl_course_id"]
    )

    RB_TRIP = int(
        match_row["racebox_course_id"]
    )

    print()
    print("===================================")
    print("VALIDATION")
    print("===================================")

    print(
        f"AVL {AVL_TRIP:03d} vs RB {RB_TRIP:03d}"
    )

    try:

        print()
        print("===================================")
        print("LOAD")
        print("===================================")

        avl_file = os.path.join(

            step3_dir,

            f"arrival_times_trip_{AVL_TRIP:03d}.csv"
        )

        rb_file = os.path.join(

            step4_dir,

            f"racebox_arrival_times_trip_{RB_TRIP:03d}.csv"
        )

        print(avl_file)
        print(rb_file)

        df_avl = pd.read_csv(
            avl_file
        )

        df_rb = pd.read_csv(
            rb_file
        )

        # =====================================================
        # DATETIME
        # =====================================================

        df_avl["arrival_time"] = pd.to_datetime(
            df_avl["arrival_time"]
        )

        df_rb["arrival_time"] = pd.to_datetime(
            df_rb["arrival_time"],
            utc=True
        ).dt.tz_convert(None)

        # =====================================================
        # MERGE
        # =====================================================

        print()
        print("Merge stop arrivals...")

        df = pd.merge(

            df_avl,
            df_rb,

            on="stop_sequence",

            suffixes=(
                "_avl",
                "_rb"
            )
        )

        # =====================================================
        # TIME ERROR
        # =====================================================

        print()
        print("Compute errors...")

        # =====================================================
        # RELATIVE TIMES
        # =====================================================

        df["relative_avl_s"] = (

            df["arrival_time_avl"]
            -
            df["arrival_time_avl"].iloc[0]

        ).dt.total_seconds()

        df["relative_rb_s"] = (

            df["arrival_time_rb"]
            -
            df["arrival_time_rb"].iloc[0]

        ).dt.total_seconds()

        # =====================================================
        # ERROR
        # =====================================================

        df["error_s"] = (

            df["relative_avl_s"]
            -
            df["relative_rb_s"]

        )

        df["abs_error_s"] = np.abs(
            df["error_s"]
        )

        df["abs_error_s"] = np.abs(
            df["error_s"]
        )

        # =====================================================
        # METRICS
        # =====================================================

        mae = df[
            "abs_error_s"
        ].mean()

        rmse = np.sqrt(

            np.mean(
                df["error_s"] ** 2
            )
        )

        median_error = df[
            "abs_error_s"
        ].median()

        max_error = df[
            "abs_error_s"
        ].max()

        p95 = np.percentile(

            df["abs_error_s"],
            95
        )

        # =====================================================
        # PRINT
        # =====================================================

        print()
        print("===================================")
        print("METRICS")
        print("===================================")

        print(f"MAE      : {mae:.2f} s")

        print(f"RMSE     : {rmse:.2f} s")

        print(f"Median   : {median_error:.2f} s")

        print(f"Max      : {max_error:.2f} s")

        print(f"P95      : {p95:.2f} s")

        # =====================================================
        # TABLE
        # =====================================================

        print()
        print(df[[
            "stop_sequence",
            "arrival_time_avl",
            "arrival_time_rb",
            "error_s",
            "abs_error_s"
        ]])

        # =====================================================
        # EXPORT CSV
        # =====================================================

        output_csv = os.path.join(

            step6_dir,

            f"validation_AVL_{AVL_TRIP:03d}_RB_{RB_TRIP:03d}.csv"
        )

        df.to_csv(
            output_csv,
            index=False
        )

        print()
        print("Zapisano:")
        print(output_csv)

        # =====================================================
        # PLOT 1
        # ARRIVAL TIMES
        # =====================================================

        print()
        print("Plot arrival times...")

        plt.figure(figsize=(14, 6))

        plt.plot(

            df["stop_sequence"],

            (
                df["arrival_time_avl"]
                -
                df["arrival_time_avl"].iloc[0]
            ).dt.total_seconds(),

            linewidth=2,

            marker="o",

            label="AVL reconstructed"
        )

        plt.plot(

            df["stop_sequence"],

            (
                df["arrival_time_rb"]
                -
                df["arrival_time_rb"].iloc[0]
            ).dt.total_seconds(),

            linewidth=2,

            marker="o",

            label="RaceBox reference"
        )

        plt.xlabel("Stop sequence")

        plt.ylabel("Travel time from first stop [s]")

        plt.title(
            f"Arrival time comparison | AVL {AVL_TRIP} vs RB {RB_TRIP}"
        )

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        plot1 = os.path.join(

            step6_dir,

            f"arrival_comparison_AVL_{AVL_TRIP:03d}_RB_{RB_TRIP:03d}.png"
        )

        plt.savefig(
            plot1,
            dpi=300
        )

        plt.close()

        print("Zapisano:")
        print(plot1)

        # =====================================================
        # PLOT 2
        # ERROR
        # =====================================================

        print()
        print("Plot errors...")

        plt.figure(figsize=(14, 6))

        plt.bar(

            df["stop_sequence"],

            df["error_s"]
        )

        plt.axhline(
            0,
            linewidth=1
        )

        plt.xlabel("Stop sequence")

        plt.ylabel("Arrival time error [s]")

        plt.title(
            f"AVL reconstruction error | AVL {AVL_TRIP} vs RB {RB_TRIP}"
        )

        plt.grid(True)

        plt.tight_layout()

        plot2 = os.path.join(

            step6_dir,

            f"error_plot_AVL_{AVL_TRIP:03d}_RB_{RB_TRIP:03d}.png"
        )

        plt.savefig(
            plot2,
            dpi=300
        )

        plt.close()

        print("Zapisano:")
        print(plot2)

        # =====================================================
        # PLOT 3
        # HISTOGRAM
        # =====================================================

        print()
        print("Plot histogram...")

        plt.figure(figsize=(10, 6))

        plt.hist(

            df["abs_error_s"],

            bins=15
        )

        plt.xlabel("Absolute error [s]")

        plt.ylabel("Count")

        plt.title(
            f"Error distribution | AVL {AVL_TRIP} vs RB {RB_TRIP}"
        )

        plt.grid(True)

        plt.tight_layout()

        plot3 = os.path.join(

            step6_dir,

            f"histogram_AVL_{AVL_TRIP:03d}_RB_{RB_TRIP:03d}.png"
        )

        plt.savefig(
            plot3,
            dpi=300
        )

        plt.close()

        print("Zapisano:")
        print(plot3)

        # =====================================================
        # PLOT 4
        # ERROR PROFILE
        # =====================================================

        print()
        print("Plot error profile...")

        plt.figure(figsize=(14, 6))

        plt.plot(

            df["stop_sequence"],

            df["error_s"],

            marker="o",
            linewidth=2
        )

        plt.axhline(
            0,
            linestyle="--",
            linewidth=1
        )

        plt.xlabel("Stop sequence")

        plt.ylabel("Arrival time error [s]")

        plt.title(
            f"Error profile along route | AVL {AVL_TRIP} vs RB {RB_TRIP}"
        )

        plt.grid(True)

        plt.tight_layout()

        plot4 = os.path.join(

            step6_dir,

            f"error_profile_AVL_{AVL_TRIP:03d}_RB_{RB_TRIP:03d}.png"
        )

        plt.savefig(
            plot4,
            dpi=300
        )

        plt.close()

        print("Zapisano:")
        print(plot4)

                # =================================================
        # GLOBAL METRICS
        # =================================================

        global_metrics.append({

            "avl_trip":
                AVL_TRIP,

            "rb_trip":
                RB_TRIP,

            "confidence":
                match_row["confidence"],

            "mae":
                mae,

            "rmse":
                rmse,

            "median":
                median_error,

            "max":
                max_error,

            "p95":
                p95,

            "n_stops":
                len(df)
        })

        print()
        print("DONE")

    except Exception as e:

            print()
            print("ERROR:")
            print(e)

            continue

    # =====================================================
    # GLOBAL VALIDATION SUMMARY
    # =====================================================

    summary_df = pd.DataFrame(
        global_metrics
    )

    summary_path = os.path.join(

        step6_dir,
        "validation_summary.csv"
    )

    summary_df.to_csv(

        summary_path,
        index=False
    )

    print()
    print("===================================")
    print("GLOBAL VALIDATION SUMMARY")
    print("===================================")

    print(summary_df)

    print()
    print("Zapisano:")
    print(summary_path)

    print()
    print("DONE")