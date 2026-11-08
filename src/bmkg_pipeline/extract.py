"""Step 1 - Extract: fetches the BMKG JSON feeds, with retry and exponential backoff."""
import logging
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ExtractError(Exception):
    """Raised when a feed cannot be fetched after all retry attempts."""


# TODO 1: constants
MAX_RETRY = 3
TIMEOUT_SECONDS = 10
VALID_FEEDS = ("autogempa", "gempaterkini", "gempadirasakan")

# Repo root is two levels above this file: src/bmkg_pipeline/extract.py -> repo/
ENV_PATH = Path(__file__).parents[2] / ".env"


# TODO 2: build the feed URL
def build_feed_url(feed_name: str) -> str:
    """Return the full URL for a BMKG feed, e.g. 'autogempa' -> '<base>/autogempa.json'."""
    # Reject unknown names before touching the network.
    if feed_name not in VALID_FEEDS:
        raise ValueError(f"Unknown feed '{feed_name}'. Valid feeds: {VALID_FEEDS}")

    # load_dotenv returns False when the file is missing -> fail loudly.
    if not load_dotenv(dotenv_path=ENV_PATH):
        raise FileNotFoundError(f".env not found: {ENV_PATH}")

    # os.environ[...] raises KeyError if the variable is missing (fail fast).
    # rstrip("/") avoids a double slash if .env ends the base URL with "/".
    base_url = os.environ["BMKG_BASE_URL"].rstrip("/")
    return f"{base_url}/{feed_name}.json"


def fetch_feed(feed_name: str) -> dict:
    """Fetch one BMKG feed and return the parsed JSON.

    Retries on timeouts and 5xx with exponential backoff; raises a clear error
    when all attempts fail. Does not retry on 4xx.
    """
    url = build_feed_url(feed_name)
    last_error = None  # remembered for TODO 4 (final error message)

    # TODO 3: retry loop (requests.get with TIMEOUT_SECONDS, raise_for_status, backoff)
    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()  # turns 4xx/5xx into requests.HTTPError
            return response.json()
        except requests.HTTPError as exc:
            if exc.response.status_code < 500:
                raise  # 4xx: our request is wrong, retrying will not help
            last_error = exc  # 5xx: server-side problem, worth retrying
        except (requests.Timeout, requests.ConnectionError, requests.JSONDecodeError) as exc:
            last_error = exc  # transient network problem or a non-JSON error page

        # Exponential backoff: 1s, 2s, 4s... but never sleep after the last attempt.
        if attempt < MAX_RETRY:
            wait_seconds = 2 ** (attempt - 1)
            logger.warning(
                "Attempt %d/%d failed for feed '%s': %s. Retrying in %ds",
                attempt, MAX_RETRY, feed_name, last_error, wait_seconds,
            )
            time.sleep(wait_seconds)

    # TODO 4: reaching this line means every attempt failed (a success returns inside the loop).
    # Raise instead of returning None so the failure can never pass silently.
    # "from last_error" keeps the original cause visible in the traceback.
    raise ExtractError(
        f"Failed to fetch feed '{feed_name}' after {MAX_RETRY} attempts: {last_error}"
    ) from last_error
