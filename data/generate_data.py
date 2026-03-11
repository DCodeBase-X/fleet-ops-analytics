"""
generate_data.py
Generates a realistic synthetic fleet operations dataset.

Simulates a regional rental fleet (~5,200 vehicles, 18 months of daily records)
covering utilization, overtime, maintenance, and location data.

Seasonal realism:
  - Summer (Jun–Aug): vacation travel spikes Compact/Mid-Size demand and miles;
    staff vacations drive overtime up across all roles.
  - Winter (Nov–Feb): SUV/Truck demand rises for tournaments, games, cold weather;
    engine/brake maintenance increases; overtime eases except holiday events.
  - Spring/Fall: transitional baselines.

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
import string

SEED = 42
rng = np.random.default_rng(SEED)

# ── Config 
FLEET_SIZE    = 5200         # vehicles at start; grows to ~6500 by end
LOCATIONS     = ["North", "South", "East", "West", "Central"]
VEHICLE_TYPES = ["Compact", "Mid-Size", "Full-Size", "SUV", "Truck"]
START_DATE    = date(2023, 1, 1)
END_DATE      = date(2024, 6, 30)

OUT_DIR = os.path.dirname(__file__)

# ── Seasonal lookup tables (index 0 = January … 11 = December) 

# Utilization delta by vehicle type and month.
# Compact/Mid-Size peak summer (vacation road trips).
# SUV/Truck peak winter (cold weather, tournaments, sporting events).
_UTIL_SEASONAL = {
    "Compact":   np.array([-0.07,-0.06,-0.01, 0.02, 0.05, 0.09, 0.11, 0.09, 0.04, 0.00,-0.04,-0.06]),
    "Mid-Size":  np.array([-0.04,-0.04, 0.00, 0.02, 0.04, 0.07, 0.09, 0.07, 0.03,-0.01,-0.03,-0.04]),
    "Full-Size": np.array([-0.01,-0.01, 0.00, 0.01, 0.02, 0.03, 0.03, 0.03, 0.01, 0.00,-0.01,-0.01]),
    "SUV":       np.array([ 0.06, 0.06, 0.02,-0.01,-0.02,-0.04,-0.03,-0.03, 0.00, 0.03, 0.06, 0.08]),
    "Truck":     np.array([ 0.05, 0.05, 0.01,-0.01,-0.01,-0.03,-0.02,-0.02, 0.00, 0.02, 0.05, 0.06]),
}

# Miles-per-hour multiplier by month.
# Summer = longer vacation trips; winter = shorter, more local trips.
_MILES_MULT = np.array([0.78, 0.80, 0.90, 0.96, 1.05, 1.20, 1.28, 1.22, 1.05, 0.95, 0.84, 0.79])

# OT probability delta by month.
# Jun–Aug: staff vacations + peak demand → high OT.
# Nov–Dec: holiday tournaments, events → moderate OT bump.
# Jan–Feb: slow season, less travel, staff available → OT dips.
_OT_SEASONAL = np.array([-0.04,-0.03, 0.00, 0.01, 0.03, 0.10, 0.13, 0.10, 0.02, 0.01, 0.05, 0.06])

# Utilization delta by location and month.
# South/West warm climates carry higher utilization in summer (tourism, road trips).
# North/Central cool significantly in winter; holiday months (Nov–Dec) partially
# recover due to event travel, but still trail South/West.
_LOC_SEASONAL = {
    #              Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
    "South":   np.array([ 0.02, 0.02, 0.03, 0.04, 0.05, 0.08, 0.09, 0.08, 0.05, 0.03, 0.02, 0.02]),
    "West":    np.array([ 0.01, 0.01, 0.02, 0.03, 0.05, 0.08, 0.09, 0.08, 0.04, 0.02, 0.01, 0.01]),
    "East":    np.array([-0.01,-0.01, 0.00, 0.01, 0.02, 0.04, 0.05, 0.04, 0.02, 0.00,-0.01,-0.01]),
    "Central": np.array([-0.04,-0.04,-0.01, 0.01, 0.02, 0.03, 0.04, 0.03, 0.01,-0.01, 0.01, 0.01]),
    "North":   np.array([-0.06,-0.06,-0.02, 0.01, 0.02, 0.04, 0.05, 0.04, 0.01,-0.02, 0.01, 0.01]),
}

# Maintenance frequency multipliers by month (relative to base).
# High-mileage summer months drive oil changes and tire rotations up.
# Cold winter months stress engines and brakes.
_MAINT_SEASONAL = {
    "Oil Change":        np.array([0.85,0.85,0.95,1.00,1.05,1.20,1.25,1.20,1.05,1.00,0.90,0.85]),
    "Tire Rotation":     np.array([0.90,0.90,0.95,1.00,1.05,1.15,1.20,1.15,1.05,1.00,0.95,0.90]),
    "Brake Service":     np.array([1.20,1.15,1.00,0.95,0.90,0.85,0.85,0.85,0.90,1.00,1.10,1.20]),
    "Engine Repair":     np.array([1.25,1.20,1.05,0.95,0.90,0.85,0.85,0.85,0.90,1.00,1.10,1.25]),
    "Recall/Inspection": np.array([0.90,0.90,1.15,1.20,1.10,0.95,0.90,0.95,1.10,1.15,1.00,0.90]),
}


# ── Vehicles 
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

    chars = list(string.ascii_uppercase + string.digits)
    seen = set()
    vehicle_ids = []
    while len(vehicle_ids) < n:
        vid = "".join(rng.choice(chars, 6))
        if vid not in seen:
            seen.add(vid)
            vehicle_ids.append(vid)

    return pd.DataFrame({
        "vehicle_id":   vehicle_ids,
        "vehicle_type": types,
        "model":        models,
        "year":         years,
        "location":     locs,
        "acquired_date": acquired,
    })


# ── Daily Utilization ─────────────────────────────────────────────────────────
def build_utilization(vehicles: pd.DataFrame) -> pd.DataFrame:
    all_dates = np.array([START_DATE + timedelta(d)
                          for d in range((END_DATE - START_DATE).days + 1)])
    all_months = np.array([d.month for d in all_dates])  # 1-based

    records = []

    for _, v in vehicles.iterrows():
        mask         = all_dates >= v["acquired_date"]
        active_dates = all_dates[mask]
        months       = all_months[mask]
        n            = len(active_dates)

        # Base utilization by vehicle type
        base = {"Compact": 0.82, "Mid-Size": 0.78, "Full-Size": 0.72,
                "SUV": 0.75, "Truck": 0.68}.get(v["vehicle_type"], 0.75)

        # Seasonal bumps: vehicle-type demand + location climate (both month-indexed)
        seasonal = (
            _UTIL_SEASONAL[v["vehicle_type"]][months - 1]
            + _LOC_SEASONAL[v["location"]][months - 1]
        )

        util = np.clip(
            rng.normal(base, 0.09, n) + seasonal, 0.10, 1.0
        )

        available_hrs = np.full(n, 24.0)
        hours_used    = np.round(util * available_hrs, 1)

        # Miles-per-hour varies seasonally: summer trips are longer
        base_mph      = rng.normal(18, 4, n).clip(8)
        miles_mult    = _MILES_MULT[months - 1]
        miles         = np.round(hours_used * base_mph * miles_mult, 0)

        for i, d in enumerate(active_dates):
            records.append({
                "date":             d,
                "vehicle_id":       v["vehicle_id"],
                "location":         v["location"],
                "vehicle_type":     v["vehicle_type"],
                "available_hours":  available_hrs[i],
                "hours_used":       hours_used[i],
                "miles_driven":     miles[i],
                "utilization_rate": round(util[i], 4),
            })

    return pd.DataFrame(records)


# ── Staff Overtime 
def build_overtime(n_employees: int = 220) -> pd.DataFrame:
    records  = []
    all_dates = [START_DATE + timedelta(d)
                 for d in range((END_DATE - START_DATE).days + 1)]

    # Weekdays Mon–Fri for regular shifts; add weekend coverage Jun–Aug
    # (peak demand season requires 7-day operations)
    def _include(d: date) -> bool:
        if d.weekday() < 5:
            return True
        return d.month in (6, 7, 8)   # summer weekends

    shift_dates = [d for d in all_dates if _include(d)]

    roles = ["Fleet Coordinator", "Service Agent", "Lot Attendant",
             "Branch Manager", "Maintenance Tech"]

    # OT base probability per role
    ot_base = {
        "Fleet Coordinator": 0.10,
        "Service Agent":     0.22,
        "Lot Attendant":     0.18,
        "Branch Manager":    0.08,
        "Maintenance Tech":  0.14,
    }

    for emp_id in range(1, n_employees + 1):
        loc  = rng.choice(LOCATIONS)
        role = rng.choice(roles, p=[0.20, 0.35, 0.25, 0.10, 0.10])
        base = ot_base[role]

        for d in shift_dates:
            sched       = 8.0
            # Seasonal OT delta: staff vacations in summer drive coverage gaps;
            # holiday/tournament events push Nov–Dec up; Jan–Feb are quiet.
            seasonal_ot = _OT_SEASONAL[d.month - 1]
            prob        = min(max(base + seasonal_ot, 0.0), 0.95)
            has_ot      = rng.random() < prob
            # Summer OT tends to run longer (harder to fill coverage gaps)
            ot_max      = 4.5 if d.month in (6, 7, 8) else 3.5
            actual      = sched + (rng.uniform(0.5, ot_max) if has_ot else 0.0)
            records.append({
                "date":            d,
                "employee_id":     f"E{str(emp_id).zfill(4)}",
                "location":        loc,
                "role":            role,
                "scheduled_hours": sched,
                "actual_hours":    round(actual, 1),
                "overtime_hours":  round(max(0.0, actual - sched), 1),
            })

    return pd.DataFrame(records)


# ── Maintenance Records 
def build_maintenance(vehicles: pd.DataFrame) -> pd.DataFrame:
    records = []
    # base: (freq/day, cost_mean, cost_std, downtime_days)
    maintenance_types = {
        "Oil Change":        (0.04,  80,   20,  0.5),
        "Tire Rotation":     (0.02, 120,   30,  0.5),
        "Brake Service":     (0.01, 350,   80,  1.0),
        "Engine Repair":     (0.003, 900, 200,  2.5),
        "Recall/Inspection": (0.005, 200,  50,  1.0),
    }
    all_dates = np.array([START_DATE + timedelta(d)
                          for d in range((END_DATE - START_DATE).days + 1)])
    all_months = np.array([d.month for d in all_dates])

    for _, v in vehicles.iterrows():
        mask         = all_dates >= v["acquired_date"]
        active_dates = all_dates[mask]
        months       = all_months[mask]

        for m_type, (base_freq, c_mean, c_std, downtime) in maintenance_types.items():
            # Seasonal frequency multiplier per date
            freq_arr = base_freq * _MAINT_SEASONAL[m_type][months - 1]
            hits     = rng.random(len(active_dates)) < freq_arr
            for i in np.where(hits)[0]:
                cost = max(0.0, rng.normal(c_mean, c_std))
                records.append({
                    "vehicle_id":       v["vehicle_id"],
                    "location":         v["location"],
                    "vehicle_type":     v["vehicle_type"],
                    "date":             active_dates[i],
                    "maintenance_type": m_type,
                    "cost":             round(cost, 2),
                    "downtime_days":    downtime,
                })

    return pd.DataFrame(records)


# ── Main 
if __name__ == "__main__":
    print("Generating fleet data…")

    vehicles    = build_vehicles(FLEET_SIZE)
    utilization = build_utilization(vehicles)
    overtime    = build_overtime(n_employees=220)
    maintenance = build_maintenance(vehicles)

    os.makedirs(OUT_DIR, exist_ok=True)
    vehicles.to_csv(   f"{OUT_DIR}/fleet_vehicles.csv",     index=False)
    utilization.to_csv(f"{OUT_DIR}/daily_utilization.csv",  index=False)
    overtime.to_csv(   f"{OUT_DIR}/staff_overtime.csv",     index=False)
    maintenance.to_csv(f"{OUT_DIR}/maintenance_records.csv",index=False)

    print(f"  fleet_vehicles.csv       — {len(vehicles):,} vehicles")
    print(f"  daily_utilization.csv    — {len(utilization):,} records")
    print(f"  staff_overtime.csv       — {len(overtime):,} records")
    print(f"  maintenance_records.csv  — {len(maintenance):,} records")
    print("Done.")
