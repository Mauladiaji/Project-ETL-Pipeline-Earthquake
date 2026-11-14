"""Step 2 - Land raw: stores each response as-is, partitioned by ingest date, never overwritten."""
import json
from datetime import datetime, timezone
from pathlib import Path


def land_raw(
    feed_name: str,
    payload: dict,
    raw_dir: str,
    ingested_at: datetime | None = None,
) -> Path:
    """Write one feed response to <raw_dir>/<feed>/<YYYY-MM-DD>/<HHMMSS>Z.json and return the path.

    Raises FileExistsError instead of overwriting an existing file, and ValueError
    when feed_name is not a plain name (it must never point outside raw_dir).
    """
    # The feed name becomes a folder name: refuse anything that could escape raw_dir
    # (e.g. "../x" or "a/b").
    if feed_name in {"", ".", ".."} or Path(feed_name).name != feed_name:
        raise ValueError(f"Invalid feed name for a folder: {feed_name!r}")

    # Default to "now" in UTC and normalise any other timezone to UTC, so the date
    # folder never depends on where the code runs.
    if ingested_at is None:
        ingested_at = datetime.now(timezone.utc)
    elif ingested_at.tzinfo is None:
        ingested_at = ingested_at.replace(tzinfo=timezone.utc)  # naive -> assume UTC
    else:
        ingested_at = ingested_at.astimezone(timezone.utc)

    # Layout: <raw_dir>/<feed>/<YYYY-MM-DD>/<HHMMSS>Z.json  ("Z" marks UTC)
    path = Path(raw_dir) / feed_name / f"{ingested_at:%Y-%m-%d}" / f"{ingested_at:%H%M%S}Z.json"

    path.parent.mkdir(parents=True, exist_ok=True)

    # Mode "x" refuses to overwrite an existing file: raw data is never replaced.
    with path.open("x", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False)

    return path
