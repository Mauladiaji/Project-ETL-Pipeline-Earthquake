# Design decisions

Every decision must come with a trade-off. If no downside can be named, the choice was not
understood well enough.

| Date | Decision | Alternative | Why | Trade-off |
|---|---|---|---|---|
| 2026-11-08 | Develop locally first (Docker + PostgreSQL), deploy to GCP later | Build directly on GCP | Fast, free iteration; does not burn the 90-day trial credit | Code must stay portable between PostgreSQL and BigQuery (`MERGE` syntax differs) |
| 2026-11-08 | PostgreSQL in Docker Compose | Install PostgreSQL natively on the host | Infrastructure as code: identical database for anyone, one command to start, easy to reset | One more tool to learn; needs disk space for images |
| 2026-11-08 | `postgres:17-alpine` image | `postgres:17` (Debian-based) | Much smaller image, which matters on a machine with little free system disk | Alpine uses musl libc; rare compatibility quirks with some extensions |
| 2026-11-08 | Python 3.12.6 for the virtual environment | Python 3.14 (also installed) | All required libraries ship prebuilt wheels for 3.12; 3.14 often forces a source build that fails on Windows | Not on the newest release; will need a planned upgrade later |
| 2026-11-08 | `venv` from the standard library | `uv` or Poetry | No extra tooling to install or explain while learning the fundamentals | Slower installs; no lock file, so transitive dependencies are not fully pinned |
| 2026-11-08 | Exact version pins in `requirements.txt` | Unpinned or `>=` ranges | Reproducible installs; a library release cannot break the pipeline on its own | Updates are a manual, deliberate step |
| 2026-11-08 | Configuration via `.env` + `python-dotenv`, `.env.example` committed | Hard-coded values, or a committed config file | Same code runs in every environment; no secret ever reaches the repository | Two files to keep in sync when a new setting is added |
| 2026-11-08 | One module per pipeline step, named after the step | A single `pipeline.py` | Separation of concerns: each step is testable and explainable in isolation | More files to navigate for a small project |
| *(pending)* | Unique key for an earthquake event | Auto-increment surrogate ID | *(to be decided)* | *(to be decided)* |
| *(planned)* | Keep raw JSON responses | Transform in memory, store clean rows only | Allows replay and backfill after a bug is fixed | Extra storage; needs a retention rule |
| *(planned)* | `MERGE` (upsert) into the target table | Append everything, deduplicate in a view | Target table is always clean and query-ready | `MERGE` scans the target; needs partitioning at scale |
| *(planned)* | Hourly schedule | Every minute | Respects the source's fair use; M5.0+ events are not that frequent | Up to one hour of latency |
