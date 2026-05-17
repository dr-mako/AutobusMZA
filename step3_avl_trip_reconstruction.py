# =====================================================
# step3_avl_trip_reconstruction.py
#
# SINGLE AVL TRIP
#
# TOPOLOGICAL TRAJECTORY RECONSTRUCTION
#
# =====================================================

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

BUS_NUMBER = "146"

#TARGET_TRIP = 3

N_CANDIDATES = 3

MAX_CANDIDATE_DISTANCE = 250

MAX_INDEX_JUMP = 5

BACKWARD_PENALTY = 100

SIGMA_GPS = 30

summary_rows = []

# =====================================================
# ŚCIEŻKI
# =====================================================

base_dir = os.getcwd()

data_dir = os.path.join(
    base_dir,
    "DANE"
)

trip_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP1_AVL"
)

output_dir = os.path.join(
    base_dir,
    "OUTPUT_STEP3"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

# =====================================================
# HAVERSINE
# =====================================================

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

# =====================================================
# TOPOLOGIA
# =====================================================

print()
print("===================================")
print("TOPOLOGIA")
print("===================================")

file_topology = os.path.join(
    data_dir,
    "stoptimes_146_DW_FAL.xlsx"
)

df_topology = pd.read_excel(
    file_topology
)

topology = pd.DataFrame({

    "lat":
    df_topology["stop_lat"],

    "lon":
    df_topology["stop_lon"],

    "stop_sequence":
    df_topology["stop_sequence"]
})

print("Liczba punktów topologii:")
print(len(topology))

# =====================================================
# AVL TRIPS
# =====================================================

trip_files = sorted(

    glob.glob(

        os.path.join(
            trip_dir,
            "trip_[0-9][0-9][0-9].csv"
        )
    )
)

print()
print("Liczba kursów:")
print(len(trip_files))

# =====================================================
# LOOP
# =====================================================

for trip_file in trip_files:

    try:

        print()
        print("===================================")
        print("AVL TRIP")
        print("===================================")

        print(trip_file)

        # -------------------------------------------------
        # TRIP ID
        # -------------------------------------------------

        trip_id = (

            os.path.basename(trip_file)

            .replace("trip_", "")
            .replace(".csv", "")
        )

        # -------------------------------------------------
        # LOAD
        # -------------------------------------------------

        df = pd.read_csv(
            trip_file
        )

        # =====================================================
        # CZAS
        # =====================================================

        df["vehicle_time"] = pd.to_datetime(
            df["vehicle_time"]
        )

        # =====================================================
        # KANDYDACI
        # =====================================================

        print()
        print("Candidate generation...")

        candidate_list = []

        for i in range(len(df)):

            lat_bus = df.iloc[i]["lat"]

            lon_bus = df.iloc[i]["lon"]

            distances = []

            for j in range(len(topology)):

                d = haversine(

                    lat_bus,
                    lon_bus,

                    topology.iloc[j]["lat"],
                    topology.iloc[j]["lon"]
                )

                distances.append(d)

            distances = np.array(
                distances
            )

            sorted_idx = np.argsort(
                distances
            )

            candidates = []

            for idx in sorted_idx[:N_CANDIDATES]:

                d = distances[idx]

                if d < MAX_CANDIDATE_DISTANCE:

                    candidates.append({

                        "topology_idx":
                        idx,

                        "distance":
                        d,

                        "stop_sequence":
                        topology.iloc[idx][
                            "stop_sequence"
                        ]
                    })

            candidate_list.append(
                candidates
            )

        print("DONE")

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
                    (d / SIGMA_GPS) ** 2
                )

                c["emission_prob"] = p

        print("DONE")

        # =====================================================
        # DIRECTION LOCK
        # =====================================================

        print()
        print("Direction lock...")

        first_valid = []

        for candidates in candidate_list[:20]:

            if len(candidates) > 0:

                first_valid.append(

                    candidates[0][
                        "stop_sequence"
                    ]
                )

        direction_sign = np.sign(

            np.mean(
                np.diff(first_valid)
            )
        )

        if direction_sign >= 0:

            print("Direction: FORWARD")

        else:

            print("Direction: BACKWARD")

        # =====================================================
        # GRAPH CONSTRAINED MATCHING
        # =====================================================

        print()
        print("Graph constrained matching...")

        matched_indices = []

        previous_idx = None

        for candidates in candidate_list:

            if len(candidates) == 0:

                matched_indices.append(
                    np.nan
                )

                continue

            best_candidate = None

            best_score = -np.inf

            for c in candidates:

                idx = c["topology_idx"]

                emission = c[
                    "emission_prob"
                ]

                transition_penalty = 0

                if previous_idx is not None:

                    jump = idx - previous_idx

                    # -----------------------------------------
                    # KIERUNEK
                    # -----------------------------------------

                    if direction_sign > 0:

                        if jump < 0:

                            transition_penalty -= (
                                BACKWARD_PENALTY
                            )

                    else:

                        if jump > 0:

                            transition_penalty -= (
                                BACKWARD_PENALTY
                            )

                    # -----------------------------------------
                    # ZA DUŻY SKOK
                    # -----------------------------------------

                    if abs(jump) > MAX_INDEX_JUMP:

                        transition_penalty -= 1000

                score = (
                    emission
                    +
                    transition_penalty
                )

                if score > best_score:

                    best_score = score

                    best_candidate = idx

            matched_indices.append(
                best_candidate
            )

            previous_idx = best_candidate

        print("DONE")

        # =====================================================
        # GAP FILLING
        # =====================================================

        print()
        print("Gap filling...")

        matched_indices = np.array(
            matched_indices,
            dtype=float
        )

        valid = np.where(
            ~np.isnan(matched_indices)
        )[0]

        # brak poprawnych punktów
        if len(valid) == 0:

            print("EMPTY MATCH")
            continue

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

        # -------------------------------------------------
        # fill edge NaN
        # -------------------------------------------------

        matched_indices = pd.Series(
            matched_indices
        )

        matched_indices = (
            matched_indices
            .bfill()
            .ffill()
        )

        # nadal same NaN
        if matched_indices.isna().all():

            print("ALL NaN")
            continue

        matched_indices = np.round(
            matched_indices
        )

        matched_indices = (
            matched_indices
            .astype(int)
            .values
        )

        print("DONE")

        # =====================================================
        # RECONSTRUCTED TRAJECTORY
        # =====================================================

        reconstructed_lat = []

        reconstructed_lon = []

        reconstructed_stop = []

        for idx in matched_indices:

            if idx < 0:
                continue

            if idx >= len(topology):
                continue

            reconstructed_lat.append(

                topology.iloc[idx]["lat"]
            )

            reconstructed_lon.append(

                topology.iloc[idx]["lon"]
            )

            reconstructed_stop.append(

                topology.iloc[idx][
                    "stop_sequence"
                ]
            )

        df["reconstructed_lat"] = (
            reconstructed_lat
        )

        df["reconstructed_lon"] = (
            reconstructed_lon
        )

        df["reconstructed_stop"] = (
            reconstructed_stop
        )

        # =====================================================
        # EXPORT
        # =====================================================

        output_csv = os.path.join(

            output_dir,

            f"reconstructed_trip_{int(trip_id):03d}.csv"
        )

        df.to_csv(
            output_csv,
            index=False
        )

        print()
        print("Zapisano:")
        print(output_csv)

        # =====================================================
        # PLOT MAP
        # =====================================================

        print()
        print("Plot map...")

        plt.figure(figsize=(12, 8))

        # AVL
        plt.scatter(

            df["lon"],
            df["lat"],

            s=10,

            alpha=0.5,

            label="AVL"
        )

        # full topology
        plt.plot(

            topology["lon"],
            topology["lat"],

            linewidth=2,

            label="Full route topology"
        )

        # reconstruction
        plt.plot(

            df["reconstructed_lon"],
            df["reconstructed_lat"],

            linewidth=3,

            label="Reconstructed trip"
        )

        # stop labels
        for i in range(len(topology)):

            # ---------------------------------------------
            # podpis co 2 przystanki
            # ---------------------------------------------

            if i % 2 != 0:

                continue

            plt.text(

                topology.iloc[i]["lon"],
                topology.iloc[i]["lat"],

                str(
                    int(
                        topology.iloc[i][
                            "stop_sequence"
                        ]
                    )
                ),

                fontsize=9
            )

        plt.xlabel("Longitude")

        plt.ylabel("Latitude")

        plt.title(
            f"AVL reconstruction | Trip {int(trip_id)}"
        )

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        plot_path = os.path.join(

            output_dir,

            f"reconstruction_trip_{int(trip_id):03d}.png"
        )

        plt.savefig(
            plot_path,
            dpi=300
        )

        plt.close()

        print()
        print("Zapisano:")
        print(plot_path)

        # =====================================================
        # STOP SEQUENCE PLOT
        # =====================================================

        plt.figure(figsize=(14, 6))

        plt.scatter(

            df["vehicle_time"],

            df["nearest_stop_id"],

            s=10,

            alpha=0.5,

            label="Original AVL"
        )

        plt.plot(

            df["vehicle_time"],

            df["reconstructed_stop"],

            linewidth=2,

            label="Reconstructed"
        )

        plt.xlabel("Time")

        plt.ylabel("Stop sequence")

        plt.title(
            f"AVL reconstructed stop sequence | Trip {int(trip_id)}"
        )

        plt.grid(True)

        plt.legend()

        plt.tight_layout()

        plot_path2 = os.path.join(

            output_dir,

            f"stop_sequence_trip_{int(trip_id):03d}.png"
        )

        plt.savefig(
            plot_path2,
            dpi=300
        )

        plt.close()

        print()
        print("Zapisano:")
        print(plot_path2)

        # =====================================================
        # STOP ARRIVAL INTERPOLATION
        # =====================================================

        print()
        print("Stop arrival interpolation...")

        arrival_records = []

        # ---------------------------------------------
        # reconstructed stop sequence
        # ---------------------------------------------

        stop_seq = df[
            "reconstructed_stop"
        ].values

        time_seq = pd.to_datetime(
            df["vehicle_time"]
        )

        # ---------------------------------------------
        # wszystkie przystanki
        # ---------------------------------------------

        unique_stops = np.unique(
            stop_seq
        )

        # =================================================
        # INTERPOLACJA
        # =================================================

        for stop_id in unique_stops:

            # ---------------------------------------------
            # indeksy próbek dla przystanku
            # ---------------------------------------------

            idx = np.where(
                stop_seq == stop_id
            )[0]

            if len(idx) == 0:

                continue

            # ---------------------------------------------
            # pierwszy moment osiągnięcia
            # ---------------------------------------------

            first_idx = idx[0]

            arrival_time = time_seq.iloc[
                first_idx
            ]

            arrival_records.append({

                "stop_sequence":
                int(stop_id),

                "arrival_time":
                arrival_time
            })

        # =================================================
        # DATAFRAME
        # =================================================

        arrival_df = pd.DataFrame(
            arrival_records
        )

        # =================================================
        # SORT BY REAL TRAVEL ORDER
        # =================================================

        if direction_sign >= 0:

            arrival_df = arrival_df.sort_values(
                "stop_sequence"
            )

        else:

            arrival_df = arrival_df.sort_values(
                "stop_sequence",
                ascending=False
            )

        # =================================================
        # TRAVEL TIME BETWEEN STOPS
        # =================================================

        arrival_df[
            "travel_time_s"
        ] = (

            arrival_df[
                "arrival_time"
            ].diff()

            .dt.total_seconds()
        )

        print()
        print(arrival_df)

        # =====================================================
        # QUALITY CONTROL
        # =====================================================

        MAX_TRAVEL_TIME = 300

        arrival_df["anomaly"] = (
            arrival_df["travel_time_s"]
            > MAX_TRAVEL_TIME
        )

        n_anomalies = arrival_df["anomaly"].sum()

        print()
        print("Quality control...")
        print(
            f"Anomalous segments: {n_anomalies}"
        )

        # =================================================
        # EXPORT CSV
        # =================================================

        arrival_path = os.path.join(

            output_dir,

            f"arrival_times_trip_{int(trip_id):03d}.csv"
        )

        arrival_df.to_csv(

            arrival_path,

            index=False
        )

        print()
        print("Zapisano:")
        print(arrival_path)        

         # =====================================================
        # SUMMARY
        # =====================================================

        summary_rows.append({

            "trip_id": int(trip_id),

            "start_time":
                arrival_df["arrival_time"].min(),

            "end_time":
                arrival_df["arrival_time"].max(),

            "start_stop":
                arrival_df["stop_sequence"].iloc[0],

            "end_stop":
                arrival_df["stop_sequence"].iloc[-1],

            "direction":

                "FORWARD"

                if direction_sign >= 0

                else "BACKWARD",

            "n_points": len(df),

            "n_reconstructed": len(matched_indices),

            "n_stops": len(arrival_df),

            "trip_duration_s":
                (
                    arrival_df["arrival_time"].max()
                    -
                    arrival_df["arrival_time"].min()
                ).total_seconds(),

            "mean_travel_time_s":
                arrival_df["travel_time_s"].mean(),

            "median_travel_time_s":
                arrival_df["travel_time_s"].median(),

            "max_travel_time_s":
                arrival_df["travel_time_s"].max(),

            "n_anomalies":
                n_anomalies
        })
        print()
        print("DONE")

    except Exception as e:

        print()
        print("ERROR:")
        print(trip_file)
        print(e)

        continue

# =====================================================
# GLOBAL SUMMARY
# =====================================================

summary_df = pd.DataFrame(
    summary_rows
)

summary_file = os.path.join(

    output_dir,
    "trip_summary.csv"
)

summary_df.to_csv(

    summary_file,
    index=False
)

print()
print("===================================")
print("GLOBAL SUMMARY")
print("===================================")

print(summary_df)

print()
print("Zapisano:")
print(summary_file)