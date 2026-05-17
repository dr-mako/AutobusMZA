# step5_trip_matching.py

import os
import pandas as pd
import numpy as np

# =====================================================
# PATHS
# =====================================================

base_dir = os.getcwd()

output_dir = os.path.join(
    base_dir,
    "OUTPUT"
)

racebox_dir = os.path.join(
    base_dir,
    "OUTPUT_RACEBOX"
)

step5_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP5"
)

os.makedirs(
    step5_dir,
    exist_ok=True
)

# =====================================================
# LOAD SUMMARIES
# =====================================================

print()
print("===================================")
print("LOAD SUMMARIES")
print("===================================")

avl_summary_path = os.path.join(
    output_dir,
    "trip_summary.csv"
)

racebox_summary_path = os.path.join(
    racebox_dir,
    "trip_summary.csv"
)

df_avl = pd.read_csv(
    avl_summary_path
)

df_rb = pd.read_csv(
    racebox_summary_path
)

# =====================================================
# DATETIME
# =====================================================

# -------------------------------------------------
# AVL
# -------------------------------------------------

df_avl["start_time"] = pd.to_datetime(
    df_avl["start_time"],
    utc=True
).dt.tz_convert(None)

df_avl["end_time"] = pd.to_datetime(
    df_avl["end_time"],
    utc=True
).dt.tz_convert(None)

# -------------------------------------------------
# RACEBOX
# -------------------------------------------------

df_rb["start_time"] = pd.to_datetime(
    df_rb["start_time"],
    utc=True
).dt.tz_convert(None)

df_rb["end_time"] = pd.to_datetime(
    df_rb["end_time"],
    utc=True
).dt.tz_convert(None)

# =====================================================
# DURATION
# =====================================================

df_avl["duration_s"] = (
    df_avl["end_time"]
    -
    df_avl["start_time"]
).dt.total_seconds()

df_rb["duration_s"] = (
    df_rb["end_time"]
    -
    df_rb["start_time"]
).dt.total_seconds()

# =====================================================
# DIRECTION
# =====================================================

def get_direction(row):

    if row["end_stop"] > row["start_stop"]:

        return "FORWARD"

    elif row["end_stop"] < row["start_stop"]:

        return "BACKWARD"

    else:

        return "UNKNOWN"

df_avl["direction"] = df_avl.apply(
    get_direction,
    axis=1
)

df_rb["direction"] = df_rb.apply(
    get_direction,
    axis=1
)

# =====================================================
# REMOVE UNKNOWN
# =====================================================

df_avl = df_avl[
    df_avl["direction"] != "UNKNOWN"
].copy()

df_rb = df_rb[
    df_rb["direction"] != "UNKNOWN"
].copy()

# =====================================================
# MATCHING
# =====================================================

print()
print("===================================")
print("TRIP MATCHING")
print("===================================")

used_rb = set()

matches = []

# =====================================================
# AVL LOOP
# =====================================================

for _, avl_row in df_avl.iterrows():

    best_score = np.inf

    best_match = None

    # =================================================
    # RACEBOX LOOP
    # =================================================

    for _, rb_row in df_rb.iterrows():

        rb_id = rb_row["course_id"]

        # already matched
        if rb_id in used_rb:

            continue

        # -------------------------------------------------
        # DIRECTION
        # -------------------------------------------------

        if avl_row["direction"] != rb_row["direction"]:

            continue

        # -------------------------------------------------
        # START TIME GATE
        # -------------------------------------------------

        start_diff = abs(

            (
                avl_row["start_time"]
                -
                rb_row["start_time"]
            ).total_seconds()

        )

        # max 30 min

        if start_diff > 1800:

            continue

        # -------------------------------------------------
        # DURATION GATE
        # -------------------------------------------------

        duration_diff = abs(

            avl_row["duration_s"]
            -
            rb_row["duration_s"]

        )

        # max 20 min

        if duration_diff > 1200:

            continue

        # -------------------------------------------------
        # TERMINAL CONSISTENCY
        # -------------------------------------------------

        start_stop_diff = abs(

            avl_row["start_stop"]
            -
            rb_row["start_stop"]

        )

        end_stop_diff = abs(

            avl_row["end_stop"]
            -
            rb_row["end_stop"]

        )

        if start_stop_diff > 5:

            continue

        if end_stop_diff > 5:

            continue

        # -------------------------------------------------
        # END TIME DIFFERENCE
        # -------------------------------------------------

        end_diff = abs(

            (
                avl_row["end_time"]
                -
                rb_row["end_time"]
            ).total_seconds()

        )

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score = (

            start_diff
            +
            end_diff
            +
            duration_diff

        )

        # -------------------------------------------------
        # BEST MATCH
        # -------------------------------------------------

        if score < best_score:

            best_score = score

            best_match = {

                "avl_course_id":
                    avl_row["course_id"],

                "racebox_course_id":
                    rb_row["course_id"],

                "direction":
                    avl_row["direction"],

                "avl_start":
                    avl_row["start_time"],

                "rb_start":
                    rb_row["start_time"],

                "start_diff_s":
                    start_diff,

                "end_diff_s":
                    end_diff,

                "duration_diff_s":
                    duration_diff,

                "score":
                    score

            }

    # =================================================
    # SAVE MATCH
    # =================================================

    if best_match is not None:

        used_rb.add(
            best_match["racebox_course_id"]
        )

        matches.append(
            best_match
        )
        
# =====================================================
# DATAFRAME
# =====================================================

df_matches = pd.DataFrame(
    matches
)

# =====================================================
# CONFIDENCE
# =====================================================

confidence = []

for score in df_matches["score"]:

    if score < 300:

        confidence.append("HIGH")

    elif score < 900:

        confidence.append("MEDIUM")

    else:

        confidence.append("LOW")

df_matches["confidence"] = confidence

# =====================================================
# PRINT
# =====================================================

print()
print(df_matches)

# =====================================================
# SAVE
# =====================================================

output_path = os.path.join(

    step5_dir,
    "trip_matching.csv"

)

df_matches.to_csv(
    output_path,
    index=False
)

print()
print("Zapisano:")
print(output_path)

print()
print("DONE")