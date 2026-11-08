# BMKG Earthquake Pipeline

An hourly data pipeline that builds a permanent, deduplicated history of Indonesian earthquakes
from a public source that only ever exposes the latest 15 events.

> **Status:** in progress — local development environment set up; pipeline steps not yet implemented.

## The problem

BMKG (Indonesia's Meteorology, Climatology and Geophysics Agency) publishes earthquake data as a
**sliding window**: the feed always holds the 15 most recent events, and there is no way to request
historical data. Think of a notice board that fits exactly 15 sheets of paper — every new sheet
pushes the oldest one off.

Copying that board into a table every hour creates three problems:

1. **Duplicates** — a naive `INSERT` stores the same earthquake up to 15 times.
2. **Gaps** — if the job stops for a day and more than 15 events occur, the overflow is lost forever.
3. **Dirty formats** — dates like `15 Mei 2026`, times in WIB, depth as the string `10 km`,
   magnitude as text.

The pipeline's value is that it **creates history the source does not keep**: after a month BMKG
still shows 15 events, while the target table holds hundreds — each exactly once.

## Design goals

| Goal | Meaning | How it is measured |
|---|---|---|
| Idempotent | Re-running any hour produces the same table | Row count unchanged after 3 re-runs |
| Incremental | Only new or changed records are written | New vs unchanged counts logged per run |
| Resilient | Transient errors are retried with backoff | % of scheduled runs that succeed |
| Replayable | Raw responses are kept intact | Backfill from raw tested at least once |
| Observable | Every run records what was fetched, written, rejected | Alert fired during a failure drill |
| Low cost | Runs inside the GCP free tier | Billing report: $0/month |

## Architecture

### Local development (current stage)

```
BMKG Open Data  --JSON-->  Python pipeline (venv)  --write-->  data/raw/<ingest_date>/
3 JSON feeds                      |                                    |
                                  | structured logs                    | load
                                  v                                    v
                            console / file                     PostgreSQL (Docker Compose)
                                                               staging -> earthquakes
```

### Target (production)

<!-- TODO: add the GCP diagram (Cloud Scheduler -> Cloud Run Job -> Cloud Storage -> BigQuery -> Looker Studio) -->

Storage targets are swapped through configuration, not by rewriting pipeline logic:
local folder ↔ Cloud Storage, PostgreSQL ↔ BigQuery.

## The six steps of one run

| # | Step | Module | What it does |
|---|---|---|---|
| 1 | Extract | `extract.py` | Calls the 3 BMKG feeds; retries 5xx and timeouts 3× with exponential backoff |
| 2 | Land raw | `land.py` | Stores each response as-is, partitioned by ingest date, never overwritten |
| 3 | Validate | `validate.py` | Checks required fields and plausible ranges; rejected rows go to a quarantine table, not the bin |
| 4 | Transform | `transform.py` | Parses Indonesian dates, converts WIB to UTC, casts depth and magnitude, builds the unique key |
| 5 | Load | `load.py` | `MERGE` into the target table by unique key — insert new, update revised, skip unchanged |
| 6 | Log & alert | `logging_setup.py` | One structured log line per run (fetched, new, updated, rejected); alerts on failure |

## How to run

<!-- TODO: fill in once the pipeline runs end to end -->

```bash
# 1. Configuration
cp .env.example .env          # then edit the values

# 2. Start the local database
docker compose up -d

# 3. Install dependencies
python -m venv .venv
.venv/Scripts/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Run one pipeline cycle
python -m src.bmkg_pipeline.main
```

## Project structure

```
.
├── src/bmkg_pipeline/     # one module per pipeline step
│   ├── main.py            # orchestrates a single run
│   ├── config.py          # configuration from environment variables
│   ├── logging_setup.py   # structured logging
│   ├── extract.py land.py validate.py transform.py load.py
├── sql/                   # DDL for the target and quarantine tables
├── tests/
├── data/raw/              # local raw zone (git-ignored)
├── docker-compose.yml     # local PostgreSQL
├── requirements.txt
├── .env.example
├── DECISIONS.md           # every design choice, with its trade-off
└── NOTES.md               # problems hit along the way
```

## Data source

Earthquake data is provided by **BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)** through
their public Open Data service: <https://data.bmkg.go.id/>

Endpoints used:

| Endpoint | Contents |
|---|---|
| `autogempa.json` | Most recent earthquake (1 record) |
| `gempaterkini.json` | 15 most recent M5.0+ earthquakes |
| `gempadirasakan.json` | 15 most recent earthquakes reported as felt |

No API key is required. Please credit BMKG when reusing this data.
