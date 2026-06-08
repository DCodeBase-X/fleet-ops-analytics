# Analytics Methodology

This document describes how each KPI and analytical result in the Fleet Ops Analytics dashboard and notebook is computed. An auditor or stakeholder should be able to validate any number shown in the UI by applying the steps below to the underlying CSVs without reading application code.

---

## 1. Fleet Utilization Rate

### Computation

The source field is `utilization_rate` in `data/daily_utilization.csv`. Each row represents one vehicle on one date.

1. Apply the active filters (location, date range) to the CSV rows.
2. Compute the arithmetic mean of `utilization_rate` across all remaining rows.
3. Multiply by 100 to express the result as a percentage.

This value is exposed as `avg_util` in `compute_kpis()`.

### Baseline Comparison

`util_delta` measures how much the filtered subset deviates from the fleet-wide baseline:

```
util_delta = avg_util(filtered) − avg_util(all rows)
```

A positive `util_delta` means the selected location/period runs above the overall fleet average. A negative value means it runs below.

### Threshold Logic

| Range | Status | Label |
|---|---|---|
| avg_util ≥ 80% | On-target | Green |
| 60% ≤ avg_util < 80% | Watch | Amber |
| avg_util < 60% | Critical | Red |

Operationally, the 80% threshold represents a vehicle being productively deployed for at least four out of every five scheduled hours. The watch band (60–79%) indicates underuse that may warrant redeployment. The critical band (<60%) flags vehicles or locations where utilization is low enough to suggest either excess capacity or persistent operational problems.

### Known Limitation

`utilization_rate` in this dataset is generated from a uniform distribution. Real-world fleet utilization distributions typically exhibit heavier tails — a small number of vehicles log very high or very low utilization — which can shift mean-based KPIs materially. Conclusions drawn from this dataset about threshold breach rates should not be extrapolated to actual operations without first validating the distributional assumption.

---

## 2. Overtime Cost

### Computation

The source field is `overtime_hours` in `data/staff_overtime.csv`.

**OT cost:**

```
ot_cost = sum(overtime_hours) × $28.00
```

`$28.00` is the `OT_PREMIUM` constant defined in `dashboard/config.py`. It is applied uniformly to all roles and locations.

**OT ratio:**

```
avg_ot_shift(filtered)  = sum(overtime_hours, filtered)  / count(distinct dates, filtered)
avg_ot_shift(baseline)  = sum(overtime_hours, all rows)  / count(distinct dates, all rows)

ot_ratio = (avg_ot_shift(filtered) − avg_ot_shift(baseline)) / avg_ot_shift(baseline)
```

A positive `ot_ratio` means the filtered period or location logs more OT hours per day than the fleet-wide average. A negative value means fewer.

`shift_delta` is the raw (non-normalized) version:

```
shift_delta = avg_ot_shift(filtered) − avg_ot_shift(baseline)
```

### Summer Overindex

Computed in the notebook (`notebooks/fleet_analysis.ipynb`):

1. Isolate rows where month is June, July, or August (summer months).
2. Compute summer's share of total annual OT hours: `summer_OT_hrs / annual_OT_hrs`.
3. Compute summer's calendar weight: 3 months / 12 months = 25%.
4. Overindex factor = summer share / 25%.

An overindex factor of 1.0 means summer OT is exactly proportional to its calendar weight. A factor above 1.0 means summer is disproportionately OT-heavy.

### Known Limitation

`$28.00/hr` is a synthetic stand-in. Real OT premiums vary by role (e.g., drivers vs. mechanics), location (union vs. non-union), and collective agreement terms. Cost figures in this dashboard should not be used for actual budget projections without substituting the correct role- and location-specific rates from HR/payroll systems.

---

## 3. Maintenance Analysis

### Downtime Impact (Pearson Correlation)

Source tables: `data/maintenance_records.csv` (contains `downtime_days`, `maintenance_cost`, `maintenance_type`) and `data/daily_utilization.csv` (contains `utilization_rate`).

**Grain alignment:** Both tables are aggregated to the monthly × location level before joining:

- Maintenance: `sum(downtime_days)` grouped by `(location, year, month)`
- Utilization: `avg(utilization_rate)` grouped by `(location, year, month)`

The JOIN key is `(location, year, month)`. This prevents row-count mismatches that would arise from joining at the daily × vehicle grain.

**Correlation:** Computed using DuckDB's `CORR()` aggregate function, which implements the standard Pearson r formula over the joined monthly aggregates.

### Interpreting r ≈ 0.53

A Pearson r of approximately 0.53 indicates a moderate positive association: locations and months with more downtime days tend to show lower average utilization rates. The relationship is directionally consistent with the hypothesis that vehicle downtime reduces productive deployment hours.

Correlation does not imply causation. Alternative explanations include reverse causation (low utilization periods coincide with scheduled maintenance windows) or a shared confounding factor (seasonal demand cycles affecting both simultaneously).

### Reactive vs. Scheduled Maintenance

The notebook approximates reactive maintenance by filtering `maintenance_type` to `Engine Repair` and `Brake Service` occurring in November–February. This is a heuristic, not a field-level classification. The raw data does not contain a `scheduled` / `reactive` flag.

### Known Limitation

The correlation is estimated on 90 data points (5 locations × 18 months). This sample size is adequate for illustrative analysis but insufficient to establish statistical significance with high confidence or to generalize findings beyond this synthetic dataset.

---

## 4. Cost Impact Levers

The notebook presents three parameterized savings scenarios. All figures are estimates derived from the synthetic dataset and should be treated as directional, not precise.

### Lever 1 — Summer OT Reduction

```
savings = summer_ot_cost × reduction_rate
```

Two scenarios are shown: `reduction_rate = 0.20` (20% reduction) and `reduction_rate = 0.30` (30% reduction). `summer_ot_cost` is computed the same way as `ot_cost` but scoped to June–August rows only.

### Lever 2 — Fleet Rebalancing (Idle Pool)

1. Compute each vehicle's average utilization across the full dataset.
2. Identify vehicles where that average is below 50% — the idle pool.
3. `idle_count` = number of such vehicles.
4. `lift` = fleet-wide average utilization − idle pool average utilization.

This quantifies the utilization gap that rebalancing (redeployment or disposal) could theoretically close.

**Note on current dataset:** `idle_count` is 0 in the current synthetic dataset because the minimum per-vehicle average utilization is approximately 68%, above the 50% threshold. The lever logic is correct; the synthetic data simply contains no idle vehicles. A real dataset with genuine underutilization would populate this lever with non-zero figures.

### Lever 3 — Pre-Winter Maintenance Shift

```
savings = cost(Engine Repair + Brake Service, Nov–Feb) × 0.10
```

The hypothesis is that shifting a portion of reactive winter maintenance to pre-season scheduled work reduces both emergency labor premiums and unplanned downtime. The 10% savings estimate is an illustrative assumption, not derived from empirical data.

---

## 5. Known Limitations (Consolidated)

| Area | Limitation |
|---|---|
| Synthetic data | All four CSVs are generated from parameterized distributions with fixed random seeds. Distributions are predominantly uniform; real-world fleet data exhibits skew, outliers, and autocorrelation not present here. |
| 80% utilization target | Represents a common fleet management benchmark adopted for this project. It is not derived from or calibrated to this dataset. |
| $28/hr OT premium | Synthetic stand-in. Real premiums are role-, location-, and contract-specific. |
| Correlation sample size | 90 monthly × location data points; sufficient for illustrative purposes, insufficient for formal statistical inference. |
| Maintenance classification | No scheduled/reactive flag in source data; reactive maintenance is approximated by type and season. |
| Lever 3 savings rate | The 10% pre-winter maintenance savings assumption is illustrative. No empirical basis is provided. |
