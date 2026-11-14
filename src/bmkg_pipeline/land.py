"""Step 2 - Land raw: stores each response as-is, partitioned by ingest date, never overwritten."""
import json
from datetime import datetime, timezone
from pathlib import Path


def land_raw(feed_name: str, payload: dict, raw_dir: str, ingested_at: datetime | None = None) -> Path:
    """Write one feed response to <raw_dir>/<feed>/<YYYY-MM-DD>/<HHMMSS>Z.json and return the path.

    Raises FileExistsError instead of overwriting an existing file.
    """
    # TODO 1: default to "now" in UTC; normalise any other timezone to UTC so that
    # the date folder never depends on where the code runs.
    if ingested_at is None:
        ingested_at = datetime.now(timezone.utc)
    elif ingested_at.tzinfo is None:
        ingested_at = ingested_at.replace(tzinfo=timezone.utc)  # naive -> assume UTC
    else:
        ingested_at = ingested_at.astimezone(timezone.utc)

    # TODO 2: <raw_dir>/<feed>/<YYYY-MM-DD>/<HHMMSS>Z.json
    path = (
        Path(raw_dir)
        / feed_name
        / ingested_at.strftime("%Y-%m-%d")
        / f"{ingested_at.strftime('%H%M%S')}Z.json"
    )

    # TODO 3: create the folder tree if it does not exist yet
    path.parent.mkdir(parents=True, exist_ok=True)

    # TODO 4: mode "x" refuses to overwrite: raw data is never replaced.
    with path.open("x", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False)

    return path
