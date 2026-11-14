"""Loads and validates configuration from environment variables (.env)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Repo root is two levels above this file: src/bmkg_pipeline/config.py -> repo/
REPO_ROOT = Path(__file__).parents[2]
ENV_PATH = REPO_ROOT / ".env"


@dataclass(frozen=True)
class Config:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    # repr=False keeps the password out of print(cfg) and log lines.
    postgres_password: str = field(repr=False)
    bmkg_base_url: str
    raw_data_dir: str  # always an absolute path (see load_config)
    log_level: str


def load_config() -> Config:
    """Read .env once and return a validated Config object."""
    # load_dotenv returns False when the file is missing -> fail loudly.
    if not load_dotenv(dotenv_path=ENV_PATH):
        raise FileNotFoundError(f".env not found: {ENV_PATH}")

    # os.environ[...] raises KeyError if a variable is missing (fail fast).
    postgres_host = os.environ["POSTGRES_HOST"]
    postgres_port = int(os.environ["POSTGRES_PORT"])  # .env values are text
    postgres_db = os.environ["POSTGRES_DB"]
    postgres_user = os.environ["POSTGRES_USER"]
    postgres_password = os.environ["POSTGRES_PASSWORD"]
    bmkg_base_url = os.environ["BMKG_BASE_URL"]
    log_level = os.environ["LOG_LEVEL"]

    # A relative path like "data/raw" depends on the folder the program is started from.
    # Anchor it to the repo root so data always lands in the same place; an absolute
    # path (e.g. on a server or in Docker) is used as given.
    raw_data_dir = Path(os.environ["RAW_DATA_DIR"])
    if not raw_data_dir.is_absolute():
        raw_data_dir = REPO_ROOT / raw_data_dir

    return Config(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        bmkg_base_url=bmkg_base_url,
        raw_data_dir=str(raw_data_dir),
        log_level=log_level,
    )
