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
