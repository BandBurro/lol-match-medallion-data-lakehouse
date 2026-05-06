# LoL Meta Analytics

> Personal League of Legends data pipeline and analytics dashboard — from raw Riot API data to interactive champion meta insights.

---

## Dashboard Showcase

| Overview Tab | Champion Comparison |
|:---:|:---:|
| ![Overview](docs/screenshots/tab_overview.png) | ![Comparison](docs/screenshots/tab_comparison.png) |

| Meta Analysis | Tier List |
|:---:|:---:|
| ![Meta](docs/screenshots/tab_meta.png) | ![Tier List](docs/screenshots/tab_tierlist.png) |

---

## Architecture

```
Riot Games API
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│           Apache Airflow  (Docker Compose)                  │
│                                                             │
│  [Bronze Extraction] ──► [Silver Transformation] ──►        │
│                           [Gold Aggregations]               │
└─────────────────────────────────────────────────────────────┘
         │                       │                    │
         ▼                       ▼                    ▼
  bronze_matches_lol    silver_matches_lol   gold_champion_stats_lol
  (raw JSON strings)    (per-game rows)      (per-champion stats)
         └───────────────────────┴────────────────────┘
                                 │
                     Databricks Delta Lake
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Dash Dashboard      │
                     │   (Plotly + DBC)      │
                     │   localhost:8050      │
                     └───────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 3.2.1 (CeleryExecutor, Docker Compose) |
| Data Processing | PySpark on Databricks (Delta Lake) |
| Data Source | Riot Games Match API v5 |
| Storage | Databricks Delta Lake (Bronze / Silver / Gold) |
| Dashboard | Dash 4.1.0 + Plotly 6.7.0 + dash-bootstrap-components |
| Backend Services | PostgreSQL 16 + Redis 7.2 (Airflow metadata & broker) |
| Container Runtime | Docker + Docker Compose |

---

## Project Structure

```
projeto-lol/
├── .env                          # Airflow settings (gitignored — see .env.example)
├── .env.example                  # Airflow env template
├── .gitignore
├── README.md
│
├── config/
│   └── airflow.cfg               # Airflow configuration
│
├── dags/
│   └── dag_lol_pipeline.py       # Daily DAG: triggers Bronze → Silver → Gold jobs
│
├── databricks/
│   ├── 1_Bronze_Extraction_LoL.py      # Riot API → raw JSON Delta table
│   ├── 2_Silver_Transformation_LoL.py  # Parse participants → clean per-game rows
│   └── 3_Gold_Aggregations_LoL.py      # Aggregate per-champion win rates & stats
│
├── infra/
│   ├── docker-compose.yaml       # Full Airflow stack (Postgres + Redis + Celery)
│   └── Dockerfile                # Dash dashboard container image
│
├── lol_analytics_dash/
│   ├── .env                      # Databricks credentials (gitignored — see .env.example)
│   ├── .env.example              # Databricks env template
│   ├── requirements.txt          # Dashboard Python dependencies
│   └── app.py                    # Interactive Dash application (3 tabs, 6 charts)
│
├── docs/
│   └── screenshots/              # Dashboard screenshots (add after first deploy)
│
├── logs/                         # Airflow runtime logs (gitignored)
└── plugins/                      # Airflow plugins directory (empty)
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine + Compose v2
- Python 3.13 (for local dashboard development)
- A Databricks workspace with:
  - A running SQL Warehouse
  - Three Databricks Jobs created for Bronze, Silver, and Gold scripts — note their Job IDs
- A [Riot Games API key](https://developer.riotgames.com/) (development keys expire every 24 hours)

---

## Setup

### 1. Clone and configure environment variables

```bash
git clone <repo-url>
cd projeto-lol

# Airflow settings
cp .env.example .env
# Edit .env — set AIRFLOW_UID to your Linux UID: id -u

# Dashboard credentials
cp lol_analytics_dash/.env.example lol_analytics_dash/.env
# Edit lol_analytics_dash/.env with your Databricks connection details
```

### 2. Configure the DAG with your Databricks Job IDs

Open [dags/dag_lol_pipeline.py](dags/dag_lol_pipeline.py) and replace the three job IDs with your own:

```python
extrair_bronze   = DatabricksRunNowOperator(job_id=YOUR_BRONZE_JOB_ID,  ...)
transformar_silver = DatabricksRunNowOperator(job_id=YOUR_SILVER_JOB_ID, ...)
agregar_gold     = DatabricksRunNowOperator(job_id=YOUR_GOLD_JOB_ID,    ...)
```

Then add a `databricks_default` Airflow Connection via the UI (Admin → Connections) with your workspace host and personal access token.

### 3. Start Airflow

```bash
docker compose -f infra/docker-compose.yaml up airflow-init
docker compose -f infra/docker-compose.yaml up -d
```

Access the UI at **http://localhost:8080** (user: `airflow`, password: `airflow`).

### 4. Run the dashboard — local development

```bash
cd lol_analytics_dash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:8050**.

### 5. Run the dashboard — Docker

```bash
# Build context must be the project root
docker build -f infra/Dockerfile -t lol-dashboard .
docker run -p 8050:8050 --env-file lol_analytics_dash/.env lol-dashboard
```

---

## Pipeline Description

| Stage | Script | Input | Output Delta Table |
|---|---|---|---|
| Bronze | `databricks/1_Bronze_Extraction_LoL.py` | Riot API Match-V5 | `bronze_matches_lol` — raw JSON strings |
| Silver | `databricks/2_Silver_Transformation_LoL.py` | `bronze_matches_lol` | `silver_matches_lol` — one row per game |
| Gold | `databricks/3_Gold_Aggregations_LoL.py` | `silver_matches_lol` | `gold_champion_stats_lol` — per-champion stats |

Airflow triggers these three Databricks Jobs in sequence once per day via `DatabricksRunNowOperator`.

---

## Environment Variables Reference

### Root `.env` — Airflow

| Variable | Required | Description |
|---|---|---|
| `AIRFLOW_UID` | Yes | Linux UID for file ownership in containers (`id -u`) |
| `_PIP_ADDITIONAL_DEPENDENCIES` | No | Extra packages installed in Airflow containers at startup |
| `FERNET_KEY` | Recommended | Stable encryption key — generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

### `lol_analytics_dash/.env` — Dashboard

| Variable | Required | Description |
|---|---|---|
| `DATABRICKS_SERVER_HOSTNAME` | Yes | Databricks workspace hostname |
| `DATABRICKS_HTTP_PATH` | Yes | SQL Warehouse HTTP path |
| `DATABRICKS_ACCESS_TOKEN` | Yes | Personal access token (`dapi...`) |

---

## Notes

- The Riot API key hardcoded in `databricks/1_Bronze_Extraction_LoL.py` is a development key (expires every 24 hours). Clear or rotate it before making this repository public.
- The dashboard falls back to mock data automatically if the Databricks connection fails, so it can run offline for UI development.

---

## License

Personal project. All rights reserved.
