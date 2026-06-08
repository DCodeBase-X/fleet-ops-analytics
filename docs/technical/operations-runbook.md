# Operations Runbook

Procedures for setting up, running, and maintaining the Fleet Ops Analytics project.

---

## Prerequisites

- Python 3.11 or later
- Git with Git LFS installed (`git lfs version` must succeed — LFS is required to pull the CSV files in `data/`)

---

## Setup

```bash
git clone <repo>
cd fleet-ops-analytics
git lfs pull                         # fetch CSV files tracked by LFS
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Verify the install:

```bash
python -c "import streamlit, duckdb, plotly; print('OK')"
```

---

## Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501. The sidebar provides location and date-range filters.

---

## Generate / Regenerate Synthetic Data

```bash
python generate_data.py
```

Overwrites all four CSVs in `data/`:

- `daily_utilization.csv`
- `staff_overtime.csv`
- `maintenance_records.csv`
- `fleet_vehicles.csv`

Seeds are fixed; output is deterministic — running the script twice produces identical files.

**Cache note:** Streamlit caches data with a 3600-second TTL. After regenerating data, the dashboard will continue serving the old data for up to one hour unless you either:

- Click the **Regenerate Data** button in the sidebar, or
- Restart the Streamlit server (`Ctrl-C`, then re-run `streamlit run dashboard/app.py`).

---

## Run the Notebook

```bash
jupyter notebook notebooks/fleet_analysis.ipynb
# or
jupyter lab
```

Select the project venv as the kernel (`Python (.venv)` or equivalent). Run cells top-to-bottom; each section depends on the DuckDB in-memory connection established in cell 1. Skipping or reordering cells will cause `NameError` or stale query results.

---

## Run Tests

```bash
pytest tests/ -v
```

Expected: 30 tests pass (9 for `config.py`, 6 for `data.py`, 15 for `charts.py`).

---

## Add a New Location

1. Open `generate_data.py` and add the location name to the `LOCATIONS` list.
2. Run `python generate_data.py` to regenerate all CSVs.
3. No dashboard code changes are required. The location filter populates dynamically from the data.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError: data/*.csv` | CSVs not generated or Git LFS not pulled | `git lfs pull`, then `python generate_data.py` |
| Dashboard shows stale data after regeneration | Streamlit cache (ttl=3600) | Click **Regenerate Data** in sidebar, or restart the server |
| `Port 8501 already in use` | A prior Streamlit instance is still running | `pkill -f streamlit`, or run on an alternate port: `streamlit run dashboard/app.py --server.port 8502` |
| `ModuleNotFoundError: duckdb` | Package not installed in active venv | `pip install "duckdb>=1.0.0"` |
| Notebook cells fail with `NameError` | Cells were run out of order | **Kernel → Restart & Run All** |
