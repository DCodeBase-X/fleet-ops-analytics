# Fleet Ops Analytics

Interactive analytics dashboard for a 5,200-vehicle fleet — utilization, overtime costs, efficiency, and maintenance tracking.

![Operations Brief](visuals/ops-brief.png)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-FFA500?style=flat)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat&logo=plotly&logoColor=white)

---

## Dashboard Views

**Operations Brief** — Fleet-wide utilization rate, daily trends, and operational KPIs.

![Operations Brief](visuals/ops-brief.png)

**OT Intelligence** — Overtime spend breakdown by location and driver, cost variance analysis.

![OT Intelligence](visuals/ot-intelligence.png)

**Fleet Efficiency** — Vehicle utilization distribution, outlier identification, and efficiency scoring.

![Fleet Efficiency](visuals/fleet-efficiency.png)

**Maintenance Radar** — Maintenance frequency, cost tracking, and vehicle status by type.

![Maintenance Radar](visuals/maintenance-radar.png)

---

## Getting Started

**Prerequisites:** Python 3.10+

```bash
git clone https://github.com/DCodeBase-X/fleet-ops-analytics.git
cd fleet-ops-analytics
pip install -r requirements.txt
streamlit run dashboard/app.py
```

To run the deep-dive analysis notebook:

```bash
jupyter notebook notebooks/fleet_analysis.ipynb
```

---

## Project Structure

```
fleet-ops-analytics/
├── dashboard/        # Streamlit app — config, data loading, charts, entry point
├── data/             # Source CSV files (synthetic fleet data, 4 files)
├── notebooks/        # Jupyter notebook with DuckDB SQL analysis
├── tests/            # Pytest test suite
├── visuals/          # Dashboard screenshots
└── requirements.txt
```

---

## License

MIT © 2026 Damarius McNair
