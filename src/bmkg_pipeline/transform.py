"""Step 4 - Transform: turns validated text records into typed rows (UTC time, floats, clean text)."""

from datetime import datetime, timezone


def _clean_text(value) -> str | None:
    """Strip spaces; turn missing or blank text into None (one single form of "empty")."""
    if value is None:
        return None
    return str(value).strip() or None


def transform_record(record: dict, source_feed: str, ingested_at: datetime) -> dict:
    """Turn one validated BMKG record (all text) into a typed row.

    The record must already have passed validate_record, so required fields are present.
    This is a pure function: no file or database access, which keeps it easy to test and replay.
    """
    # BMKG "DateTime" is already ISO 8601 UTC, so "Tanggal"/"Jam" (WIB text) are not needed.
    event_time_utc = datetime.fromisoformat(record["DateTime"]).astimezone(timezone.utc)

    # "Coordinates" is "latitude,longitude" with sign (negative = south / west).
    lat_text, lon_text = record["Coordinates"].split(",")
    latitude = float(lat_text)
    longitude = float(lon_text)

    magnitude = float(record["Magnitude"])

    # "Kedalaman" looks like "10 km": keep the number, drop the unit.
    depth_km = float(record["Kedalaman"].split()[0])

    # Optional text fields: missing or blank becomes None (NULL in the database).
    region = _clean_text(record.get("Wilayah"))
    tsunami_potential = _clean_text(record.get("Potensi"))

    return {
        "event_time_utc": event_time_utc,
        "latitude": latitude,
        "longitude": longitude,
        "magnitude": magnitude,
        "depth_km": depth_km,
        "region": region,
        "tsunami_potential": tsunami_potential,
        "source_feed": source_feed,
        "ingested_at": ingested_at,
    }
