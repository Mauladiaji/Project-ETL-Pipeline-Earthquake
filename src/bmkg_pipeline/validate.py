"""Step 3 - Validate: checks required fields and ranges; routes rejected records to quarantine."""

import math
from datetime import datetime, timedelta, timezone

# Fields every earthquake record must have. Optional fields (e.g. Wilayah, Potensi) are not
# checked here: a missing optional field should not throw away an otherwise good record.
REQUIRED_FIELDS = ("DateTime", "Coordinates", "Magnitude", "Kedalaman")

# Plausible ranges. Wide on purpose: a rule that is too strict quarantines real events.
MIN_MAGNITUDE = 0.0
MAX_MAGNITUDE = 10.0
MIN_DEPTH_KM = 0.0

# Region BMKG reports on: Indonesia (about lat -11..6, lon 95..141) plus a wide margin, because
# BMKG also reports offshore events outside the land area. Observed data so far: lat -9.2..5.59,
# lon 95.72..141.9. Too narrow a box would quarantine real events.
MIN_LAT, MAX_LAT = -15.0, 15.0
MIN_LON, MAX_LON = 90.0, 150.0

# Allow a few minutes of clock difference between BMKG and this machine.
FUTURE_TOLERANCE = timedelta(minutes=5)


def _is_empty(value) -> bool:
    """True when the value is None or text that is empty once spaces are stripped."""
    return value is None or str(value).strip() == ""


def _to_number(value) -> float:
    """Read the leading number from text such as "5.1" or "10 km".

    Raises ValueError when there is no usable number (e.g. "N/A", "nan", "inf").
    """
    parts = str(value).split()
    if not parts:
        raise ValueError("empty value")
    number = float(parts[0])
    # float("nan") and float("inf") parse fine, and every comparison with nan is False,
    # so without this check a nan would slip past the range checks below.
    if not math.isfinite(number):
        raise ValueError(f"not a finite number: {value!r}")
    return number


def _check_number(record: dict, field: str, minimum: float, maximum: float | None = None) -> list[str]:
    """Return rejection reasons for a numeric field (empty list = OK)."""
    value = record.get(field)
    if _is_empty(value):
        return []  # already reported as "missing or empty"; do not report it twice

    try:
        number = _to_number(value)
    except ValueError:
        return [f"{field} is not a number: {value!r}"]

    if number < minimum:
        return [f"{field} below minimum {minimum}: {number}"]
    if maximum is not None and number > maximum:
        return [f"{field} above maximum {maximum}: {number}"]
    return []


def _check_coordinates(record: dict) -> list[str]:
    """Return rejection reasons for "Coordinates" (text such as "-0.93,128.60")."""
    value = record.get("Coordinates")
    if _is_empty(value):
        return []  # already reported as "missing or empty"

    parts = str(value).split(",")
    if len(parts) != 2:
        return [f"Coordinates must look like 'lat,lon': {value!r}"]

    try:
        lat, lon = (_to_number(part) for part in parts)
    except ValueError:
        return [f"Coordinates are not numbers: {value!r}"]

    reasons = []
    if not MIN_LAT <= lat <= MAX_LAT:
        reasons.append(f"latitude outside expected region {MIN_LAT}..{MAX_LAT}: {lat}")
    if not MIN_LON <= lon <= MAX_LON:
        reasons.append(f"longitude outside expected region {MIN_LON}..{MAX_LON}: {lon}")
    return reasons


def _check_not_in_future(record: dict) -> list[str]:
    """Return rejection reasons for "DateTime" (ISO 8601, UTC, e.g. 2026-11-10T15:51:37+00:00)."""
    value = record.get("DateTime")
    if _is_empty(value):
        return []  # already reported as "missing or empty"

    try:
        moment = datetime.fromisoformat(str(value))
    except ValueError:
        return [f"DateTime is not ISO 8601: {value!r}"]

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)  # BMKG DateTime is UTC; assume so if no offset

    if moment > datetime.now(timezone.utc) + FUTURE_TOLERANCE:
        return [f"DateTime is in the future: {value}"]
    return []


def validate_record(record: dict) -> list[str]:
    """Return the reasons a record is rejected; an empty list means the record is valid.

    A record can break several rules at once, so every rule is checked and all reasons are
    returned. The quarantine table needs the full list to explain the rejection.
    """
    reasons: list[str] = []

    for field in REQUIRED_FIELDS:
        if _is_empty(record.get(field)):
            reasons.append(f"missing or empty: {field}")

    reasons += _check_number(record, "Magnitude", MIN_MAGNITUDE, MAX_MAGNITUDE)
    reasons += _check_number(record, "Kedalaman", MIN_DEPTH_KM)
    reasons += _check_coordinates(record)
    reasons += _check_not_in_future(record)

    return reasons
