# Data Dictionary — Fleet Ops Analytics

This document defines all source CSV schemas, derived columns added at load time, and the constants and thresholds used in KPI classification. Intended audience: analysts onboarding to the dataset, and engineers modifying the data layer.

All four CSV files live in `data/` relative to the project root. The path is resolved at import time in `config.py` as `DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))`.

---

## Source CSV Schemas

### `daily_utilization.csv`

One row per vehicle per day. Primary grain: `(date, vehicle_id)`.

| Column | Type | Description | Example | Business Definition |
|---|---|---|---|---|
| `date` | date | Calendar date of the observation | `2023-01-22` | The day on which vehicle activity was recorded |
| `vehicle_id` | string | Unique vehicle identifier | `NKWH3Y` | Alphanumeric code assigned to each fleet unit at acquisition |
| `location` | string | Operating location / depot | `East` | The branch or region where the vehicle is stationed (values: `East`, `West`, `Central`, `North`, `South`) |
| `vehicle_type` | string | Vehicle category | `SUV` | Classification used for demand segmentation and fleet planning (values: `SUV`, `Compact`, `Mid-Size`, `Truck`, `Full-Size`) |
| `available_hours` | float | Total hours the vehicle was available for rental | `24.0` | Hours in the day the vehicle was not in maintenance or otherwise out of service |
| `hours_used` | float | Actual hours the vehicle was in active use | `20.5` | Rental hours during the observation day |
| `miles_driven` | float | Miles driven during the observation day | `312.0` | Odometer delta; used for mileage-based maintenance triggers |
| `utilization_rate` | float | Fraction of available hours the vehicle was in use | `0.8558` | Computed as `hours_used / available_hours`; raw value is a decimal in [0, 1]; values above 1.0 are not expected in clean data |

---

### `staff_overtime.csv`

One row per employee per day. Primary grain: `(date, employee_id)`.

| Column | Type | Description | Example | Business Definition |
|---|---|---|---|---|
| `date` | date | Calendar date of the shift | `2023-01-02` | Day the employee worked |
| `employee_id` | string | Unique employee identifier | `E0001` | Internal HR identifier |
| `location` | string | Location where the employee worked | `South` | Branch or depot (same value set as `daily_utilization.csv`) |
| `role` | string | Employee job role | `Fleet Coordinator` | Operational role used to classify OT cost responsibility (values: `Fleet Coordinator`, `Service Agent`, `Lot Attendant`, `Shuttle Driver`, `Maintenance Tech`) |
| `scheduled_hours` | float | Hours the employee was originally scheduled to work | `8.0` | Standard shift length as planned |
| `actual_hours` | float | Total hours worked | `8.0` | Actual clocked hours including any overtime |
| `overtime_hours` | float | Hours worked beyond the scheduled shift | `0.0` | `actual_hours - scheduled_hours`; zero on non-OT days; values below zero are not expected in clean data |

---

### `maintenance_records.csv`

One row per maintenance event per vehicle. Primary grain: `(vehicle_id, date, maintenance_type)`.

| Column | Type | Description | Example | Business Definition |
|---|---|---|---|---|
| `vehicle_id` | string | Vehicle that received maintenance | `NKWH3Y` | Foreign key to `fleet_vehicles.csv` |
| `location` | string | Location where maintenance was performed | `East` | Branch where the vehicle was stationed at time of service |
| `vehicle_type` | string | Vehicle category | `SUV` | Denormalized from vehicle record for convenience |
| `date` | date | Date maintenance was performed | `2023-02-26` | Calendar date of the maintenance event |
| `maintenance_type` | string | Type of maintenance performed | `Oil Change` | Service category (values: `Oil Change`, `Tire Rotation`, `Brake Service`, `Engine Repair`, `Transmission Service`) |
| `cost` | float | Total cost of the maintenance event in USD | `106.34` | Parts and labor cost; does not include lost-revenue estimate from downtime |
| `downtime_days` | float | Days the vehicle was unavailable due to this maintenance event | `0.5` | Fleet availability reduction; fractional days are used for same-day events that returned the vehicle to service before end of business |

---

### `fleet_vehicles.csv`

One row per vehicle. Primary grain: `vehicle_id`.

| Column | Type | Description | Example | Business Definition |
|---|---|---|---|---|
| `vehicle_id` | string | Unique vehicle identifier | `NKWH3Y` | Primary key; matches `vehicle_id` in `daily_utilization.csv` and `maintenance_records.csv` |
| `vehicle_type` | string | Vehicle category | `SUV` | Classification used for demand planning |
| `model` | string | Make and model name | `Toyota RAV4` | Specific vehicle model; used for maintenance trend analysis |
| `year` | integer | Model year | `2023` | Manufacturing year; used for age-based maintenance risk profiling |
| `location` | string | Home depot / branch | `East` | Primary location the vehicle is assigned to; may differ from `maintenance_records.location` if the vehicle was moved |
| `acquired_date` | date | Date the vehicle entered the fleet | `2023-01-22` | Used for fleet growth trajectory analysis in the dashboard |

---

## Derived Columns Added at Load Time

`load_data()` in `dashboard/data.py` adds the following columns to the in-memory DataFrames after CSV load. These columns are not present in the source files. They are computed once and stored in the cached `FleetData` object.

### Columns added to the `util` DataFrame

| Column | Source | Computation | Type | Business Purpose |
|---|---|---|---|---|
| `utilization_pct` | `utilization_rate` | `utilization_rate × 100` | float | Converts the raw [0, 1] rate to a percentage for display and status classification |
| `month_period` | `date` | `date.dt.to_period("M")` | Period[M] | Monthly grouping key for time-series aggregations; stored as a Period object |
| `month_str` | `date` | `date.dt.strftime("%b")` | string | Three-letter month abbreviation (e.g., `"Jan"`) for chart axis labels |
| `month_num` | `date` | `date.dt.month` | integer | Integer month number (1–12) for sort ordering when month abbreviations are used |
| `season` | `date` | `"Summer (Jun-Aug)"` if month ∈ {6, 7, 8} else `"Rest of Year"` | string | Seasonal grouping used for summer vs. non-summer OT and utilization comparisons |

### Columns added to the `ot` DataFrame

| Column | Source | Computation | Type | Business Purpose |
|---|---|---|---|---|
| `day_name` | `date` | `date.dt.day_name()` | string | Full day of week name (e.g., `"Monday"`) for weekday vs. weekend OT pattern analysis |
| `month_period` | `date` | `date.dt.to_period("M")` | Period[M] | Monthly grouping key; used in `compute_kpis` to count distinct months for per-month rate calculations |

### Columns added to the `maint` DataFrame

| Column | Source | Computation | Type | Business Purpose |
|---|---|---|---|---|
| `month_period` | `date` | `date.dt.to_period("M")` | Period[M] | Monthly grouping key for maintenance spend trend charts |

Note: `month_str` and `month_num` are added to the `util` DataFrame only, not to `ot`. The `ot` DataFrame uses `day_name` for its primary temporal breakdown, and monthly aggregations on `ot` use `month_period` directly.

---

## Constants and Thresholds

### Business Constants

| Constant | Value | Location | Business Rationale |
|---|---|---|---|
| `OT_PREMIUM` | `28.0` | `config.py` | Hourly cost multiplier applied to all overtime hours. Represents the standard loaded OT rate used in fleet operations cost accounting for this analysis. The value is used as `overtime_hours × OT_PREMIUM` throughout the dashboard and notebook to produce dollar cost figures. It does not vary by role or location in the current implementation. |

### Utilization Status Thresholds

Defined in `config.util_status(pct: float) -> str`. Applied to `utilization_pct` (percentage, not rate).

| Range | Status Label | Interpretation |
|---|---|---|
| `pct >= 80` | `"green"` | On-target. Vehicle or group is meeting the 80% utilization floor considered optimal for this fleet. |
| `60 <= pct < 80` | `"amber"` | Watch. Below target but not critically low; may indicate seasonal trough, recent acquisition, or addressable allocation gap. |
| `pct < 60` | `"red"` | Critical. Significant underutilization; vehicle or location is a reallocation candidate or may indicate untracked downtime. |

The 80% target appears as a reference line in all utilization charts. The 50% floor used in `compute_kpis` for `vehicles_under_50` is a separate operational threshold not covered by `util_status`.

### OT Cost Ratio Thresholds

Defined in `config.ot_status(ratio: float) -> str`. The `ratio` is computed in `compute_kpis` as `(avg_monthly_cost - baseline_monthly_cost) / baseline_monthly_cost`, where baseline is the unfiltered dataset average.

| Range | Status Label | Interpretation |
|---|---|---|
| `ratio < -0.05` | `"green"` | Favorable. Filtered period OT cost is more than 5% below the overall baseline average. Indicates a relatively low-OT period or location. |
| `-0.05 <= ratio < 0.15` | `"amber"` | Normal. OT cost is within 15% above baseline; within acceptable operational variance. |
| `ratio >= 0.15` | `"red"` | Elevated. OT cost exceeds baseline by 15% or more; warrants investigation into scheduling, seasonal demand, or staffing gaps. |

### Shift Delta Thresholds

Applied in `compute_kpis` to `shift_delta = avg_ot_shift - baseline_ot` (difference in average OT hours per shift between the filtered period and the full dataset baseline). This status is computed inline rather than through a named function in `config.py`.

| Condition | Status Label | Interpretation |
|---|---|---|
| `shift_delta < 0` | `"green"` | Average OT per shift in the filtered period is lower than the overall baseline. |
| `0 <= shift_delta < 0.5` | `"amber"` | Slightly elevated per-shift OT vs. baseline; monitor but not actionable on its own. |
| `shift_delta >= 0.5` | `"red"` | Per-shift OT is materially higher than baseline; often correlates with specific high-OT locations or summer weeks. |
