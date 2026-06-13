# AVL vs RaceBox Validation Framework

## Objective

The objective of this project is to assess the accuracy of AVL (Automatic Vehicle Location) data provided by a public transport operator using a high-frequency RaceBox GNSS recorder as a reference source.

The study is performed on a selected set of vehicle-day cases defined in the project catalog. For each case, AVL and RaceBox data originate from the same vehicle operating on the same route.

The final goal is to quantify arrival-time errors and travel-time errors derived from AVL data.

---

## Processing Pipeline

### STEP1 – AVL Trip Separator

Input:

* AVL.csv
* stop timetable

Output:

* separated AVL trips

File:

* step1_avl_trip_separator.py

---

### STEP2 – RaceBox Trip Separator

Input:

* RaceBox.csv
* stop timetable

Output:

* separated RaceBox trips

File:

* step2_racebox_trip_separator.py

---

### STEP3 – AVL Trip Reconstruction

Input:

* AVL trips (STEP1)
* route topology
* trip summary

Processing:

* graph-constrained map matching
* stop sequence reconstruction
* arrival-time extraction
* arrival-time interpolation for low-quality observations

Output:

* trip_xxx_raw.csv
* trip_xxx_matched.csv
* trip_xxx_arrival_times.csv

File:

* step3_PRODUCTION_AVL_TRIP_RECONSTRUCTION.py

---

### STEP4 – RaceBox Trip Reconstruction

Input:

* RaceBox trips (STEP2)
* route topology
* trip summary

Processing:

* graph-constrained map matching
* stop sequence reconstruction
* arrival-time extraction

RaceBox observations are treated as the reference source and are not corrected using interpolation.

Output:

* trip_xxx_raw.csv
* trip_xxx_matched.csv
* trip_xxx_arrival_times.csv

File:

* step4_racebox_reconstruction_v2.py

---

## Planned Stages

### STEP5 – Trip Matching

Objective:

* pair AVL and RaceBox trips representing the same physical journey

Planned output:

* matched AVL-RaceBox trip pairs

---

### STEP6 – Arrival Time Validation

Objective:

* compare AVL arrival times with RaceBox arrival times

Metrics:

* arrival time error
* stop-to-stop travel time error

---

### STEP7 – Global Validation Analysis

Objective:

* aggregate results from all validated trips

Planned analyses:

* error distributions
* MAE
* RMSE
* percentile statistics
* line-specific and direction-specific performance

---

## Reference Data

RaceBox data are treated as the ground-truth reference.

AVL data are treated as the system under evaluation.

---

## Current Status

Completed:

* STEP1
* STEP2
* STEP3
* STEP4

In development:

* STEP5
* STEP6
* STEP7
