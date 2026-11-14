"""Step 6 - Log and alert: structured logging, one summary line per run."""
import logging
import time
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def setup_logging(level: str = "INFO", log_dir: str | None = None) -> None:
    """Configure the root logger once: console always, plus a file when log_dir is given."""
    # Every module logger reports to the root logger, so configuring it once is enough.
    root = logging.getLogger()

    # Turn the level name (e.g. "INFO") into its number; fail loudly on an unknown name.
    level_names = logging.getLevelNamesMapping()
    level_name = level.upper()
    if level_name not in level_names:
        raise ValueError(f"Unknown log level '{level}'. Valid levels: {sorted(level_names)}")
    root.setLevel(level_names[level_name])

    # Remove old handlers so calling this twice does not print every line twice.
    root.handlers.clear()

    # One formatter shared by every handler, with timestamps in UTC.
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    formatter.converter = time.gmtime

    # Console handler: always on.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # File handler: only when a log folder is given (e.g. unattended scheduled runs).
    if log_dir is not None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(Path(log_dir) / "pipeline.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
