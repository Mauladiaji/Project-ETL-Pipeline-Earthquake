# Notes

A running log of anything that broke, surprised me, or took longer than expected — written down
the moment it happens, not at the end of the project. These entries become the "What broke"
section of the portfolio write-up.

Format: date, what happened, what the cause turned out to be, how it was fixed.

---

## 2026-11-08 — Docker data directory filled the system disk

**What happened:** before any pipeline work, the environment audit showed drive `C:` had only
2.4 GB free, while Docker Desktop on WSL2 stores its entire disk image under
`C:\Users\<user>\AppData\Local\Docker`.

**Why it matters:** container images and database volumes only ever grow, and a WSL `.vhdx` file
does not shrink on its own. A full system disk means `docker compose up` fails halfway through,
or Windows itself starts misbehaving.

**Fix:** moved Docker Desktop's disk image location to a drive with free space before pulling the
PostgreSQL image.

**Lesson:** audit disk, RAM and tool versions *before* writing code, not after the first failure.

---

## 2026-11-08 — Open question: how does MERGE recognise the same earthquake?

**Context:** the primary key is an auto-increment surrogate ID (see DECISIONS.md). A surrogate ID
is assigned by the database, so the same earthquake arriving in two consecutive hourly pulls would
receive two different IDs.

**Problem:** the design goals require the pipeline to be idempotent (row count unchanged after
three re-runs). `MERGE` needs a condition to decide "this incoming record already exists". The
surrogate ID cannot provide that condition.

**To resolve before writing `load.py`:** decide what identifies an event for the `MERGE ... ON`
clause (for example a unique constraint on identifying fields), and test that it survives a
revision of the source data. Record the outcome in DECISIONS.md.
