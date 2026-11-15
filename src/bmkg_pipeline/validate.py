"""Step 3 - Validate: checks required fields and ranges; routes rejected records to quarantine."""

import math

# Fields every earthquake record must have. Optional fields (e.g. Wilayah, Potensi) are not
# checked here: a missing optional field should not throw away an otherwise good record.
REQUIRED_FIELDS = ("DateTime", "Coordinates", "Magnitude", "Kedalaman")

# Plausible ranges. Wide on purpose: a rule that is too strict quarantines real events.
MIN_MAGNITUDE = 0.0
MAX_MAGNITUDE = 10.0
MIN_DEPTH_KM = 0.0


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

    return reasons
