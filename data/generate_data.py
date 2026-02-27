"""
generate_data.py
Generates a realistic synthetic fleet operations dataset.

Simulates a regional rental fleet (~600 vehicles, 18 months of daily records)
covering utilization, overtime, maintenance, and location data.

Usage:
    python data/generate_data.py
Outputs:
    data/fleet_vehicles.csv
    data/daily_utilization.csv
    data/staff_overtime.csv
    data/maintenance_records.csv
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

SEED = 42
rng = np.random.default_rng(SEED)

# ── Config ────────────────────────────────────────────────────────────────────
FLEET_SIZE    = 600          # vehicles at start; grows to ~750 by end
LOCATIONS     = ["North", "South", "East", "West", "Central"]
VEHICLE_TYPES = ["Compact", "Mid-Size", "Full-Size", "SUV", "Truck"]
START_DATE    = date(2023, 1, 1)
END_DATE      = date(2024, 6, 30)

OUT_DIR = os.path.dirname(__file__)

# ── Vehicles ──────────────────────────────────────────────────────────────────
def build_vehicles(n: int) -> pd.DataFrame:
    makes = {
        "Compact":   ["Toyota Corolla", "Honda Civic", "Hyundai Elantra"],
        "Mid-Size":  ["Toyota Camry", "Honda Accord", "Nissan Altima"],
        "Full-Size": ["Chevrolet Impala", "Ford Taurus", "Chrysler 300"],
        "SUV":       ["Ford Explorer", "Chevrolet Equinox", "Toyota RAV4"],
        "Truck":     ["Ford F-150", "Chevrolet Silverado", "Ram 1500"],
    }
    types    = rng.choice(VEHICLE_TYPES, n, p=[0.25, 0.30, 0.20, 0.15, 0.10])
    models   = [rng.choice(makes[t]) for t in types]
    years    = rng.integers(2018, 2024, n)
    locs     = rng.choice(LOCATIONS, n)
    acquired = [START_DATE + timedelta(days=int(d))
                for d in rng.integers(0, 90, n)]   # staggered acquisition

    return pd.DataFrame({
        "vehicle_id":  [f"V{str(i).zfill(4)}" for i in range(1, n + 1)],
        "vehicle_type": types,
        "model":        models,
        "year":         years,
        "location":     locs,
        "acquired_date": acquired,
    })


# ── Daily Utilization ─────────────────────────────────────────────────────────
def build_utilization(vehicles: pd.DataFrame) -> pd.DataFrame:
    records = []
    dates   = [START_DATE + timedelta(d)
               for d in range((END_DATE - START_DATE).days + 1)]

    for _, v in vehicles.iterrows():
        active_dates = [d for d in dates if d >= v["acquired_date"]]
        n = len(active_dates)

        # Base utilization varies by type and location
        base = {"Compact": 0.82, "Mid-Size": 0.78, "Full-Size": 0.72,
                "SUV": 0.75, "Truck": 0.68}.get(v["vehicle_type"], 0.75)
        loc_bump = {"North": 0.03, "South": 0.01, "East": -0.02,
                    "West": 0.02, "Central": 0.0}.get(v["location"], 0.0)

        # Seasonal signal (summer peak)
        month_arr = np.array([d.month for d in active_dates])
        seasonal  = 0.06 * np.sin((month_arr - 3) * np.pi / 6)

        util = np.clip(
            rng.normal(base + loc_bump, 0.09, n) + seasonal, 0.10, 1.0
        )

        available_hrs = np.full(n, 24.0)
        hours_used    = np.round(util * available_hrs, 1)
        miles         = np.round(hours_used * rng.normal(18, 4, n).clip(8), 0)

        for i, d in enumerate(active_dates):
            records.append({
                "date":            d,
                "vehicle_id":      v["vehicle_id"],
                "location":        v["location"],
                "vehicle_type":    v["vehicle_type"],
                "available_hours": available_hrs[i],
                "hours_used":      hours_used[i],
                "miles_driven":    max(0, miles[i]),
                "utilization_rate": round(util[i], 4),
            })

    return pd.DataFrame(records)


# ── Staff Overtime ────────────────────────────────────────────────────────────
def build_overtime(n_employees: int = 220) -> pd.DataFrame:
    records = []
    dates   = [START_DATE + timedelta(d)
               for d in range((END_DATE - START_DATE).days + 1)]
    weekdays = [d for d in dates if d.weekday() < 5]   # Mon–Fri shifts only

    roles = ["Fleet Coordinator", "Service Agent", "Lot Attendant",
             "Branch Manager", "Maintenance Tech"]

    for emp_id in range(1, n_employees + 1):
        loc  = rng.choice(LOCATIONS)
        role = rng.choice(roles, p=[0.20, 0.35, 0.25, 0.10, 0.10])

        # OT baseline (higher for service agents and lot attendants)
        ot_base = {"Fleet Coordinator": 0.10, "Service Agent": 0.22,
                   "Lot Attendant": 0.18, "Branch Manager": 0.08,
                   "Maintenance Tech": 0.14}.get(role, 0.15)

        for d in weekdays:
            sched = 8.0
            # Summer surge drives overtime
            seasonal_ot = 0.06 if d.month in (6, 7, 8) else 0.0
            has_ot = rng.random() < (ot_base + seasonal_ot)
            actual = sched + (rng.uniform(0.5, 3.5) if has_ot else 0.0)
            records.append({
                "date":             d,
                "employee_id":      f"E{str(emp_id).zfill(4)}",
                "location":         loc,
                "role":             role,
                "scheduled_hours":  sched,
                "actual_hours":     round(actual, 1),
                "overtime_hours":   round(max(0.0, actual - sched), 1),
            })

    return pd.DataFrame(records)


# ── Maintenance Records ───────────────────────────────────────────────────────
def build_maintenance(vehicles: pd.DataFrame) -> pd.DataFrame:
    records = []
    maintenance_types = {
        "Oil Change":        (0.04,  80,   20,  0.5),   # freq/day, cost_mean, cost_std, downtime_days
        "Tire Rotation":     (0.02, 120,   30,  0.5),
        "Brake Service":     (0.01, 350,   80,  1.0),
        "Engine Repair":     (0.003, 900, 200,  2.5),
        "Recall/Inspection": (0.005, 200,  50,  1.0),
    }
    dates = [START_DATE + timedelta(d)
             for d in range((END_DATE - START_DATE).days + 1)]

    for _, v in vehicles.iterrows():
        active_dates = [d for d in dates if d >= v["acquired_date"]]
        for m_type, (freq, c_mean, c_std, downtime) in maintenance_types.items():
            for d in active_dates:
                if rng.random() < freq:
                    cost = max(0, rng.normal(c_mean, c_std))
                    records.append({
                        "vehicle_id":     v["vehicle_id"],
                        "location":       v["location"],
                        "vehicle_type":   v["vehicle_type"],
                        "date":           d,
                        "maintenance_type": m_type,
                        "cost":           round(cost, 2),
                        "downtime_days":  downtime,
                    })

    return pd.DataFrame(records)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating fleet data…")

    vehicles    = build_vehicles(FLEET_SIZE)
    utilization = build_utilization(vehicles)
    overtime    = build_overtime()
    maintenance = build_maintenance(vehicles)

    vehicles.to_csv(   f"{OUT_DIR}/fleet_vehicles.csv",     index=False)
    utilization.to_csv(f"{OUT_DIR}/daily_utilization.csv",  index=False)
    overtime.to_csv(   f"{OUT_DIR}/staff_overtime.csv",     index=False)
    maintenance.to_csv(f"{OUT_DIR}/maintenance_records.csv",index=False)

    print(f"  fleet_vehicles.csv       — {len(vehicles):,} vehicles")
    print(f"  daily_utilization.csv    — {len(utilization):,} records")
    print(f"  staff_overtime.csv       — {len(overtime):,} records")
    print(f"  maintenance_records.csv  — {len(maintenance):,} records")
    print("Done.")
