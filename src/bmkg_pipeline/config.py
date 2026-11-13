"""Loads and validates configuration from environment variables (.env)."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

@dataclass(frozen=True)
# TODO 1
class Config:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    bmkg_base_url: str
    raw_data_dir: str
    log_level: str

def load_config() -> Config:
    """Read .env once and return a validated Config object."""
    
    #TODO 2
    env_path = Path(__file__).parents[2] / ".env"
    #TODO 3
    if not load_dotenv(dotenv_path=env_path):
        raise FileNotFoundError(f'.env not found: {env_path}')
    
    #TODO 4
    postgres_host = os.environ['POSTGRES_HOST']
    postgres_port = int(os.environ['POSTGRES_PORT'])
    postgres_db = os.environ['POSTGRES_DB']
    postgres_user = os.environ['POSTGRES_USER']
    postgres_password = os.environ['POSTGRES_PASSWORD']
    bmkg_base_url = os.environ['BMKG_BASE_URL']
    raw_data_dir = os.environ['RAW_DATA_DIR']
    log_level = os.environ['LOG_LEVEL']

    #TODO 5
    return Config(
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        bmkg_base_url=bmkg_base_url,
        raw_data_dir=raw_data_dir,
        log_level=log_level,
    )
