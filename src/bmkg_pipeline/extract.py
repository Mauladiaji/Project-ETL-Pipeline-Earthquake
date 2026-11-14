"""Step 1 - Extract: fetches the BMKG JSON feeds, with retry and exponential backoff."""
import logging
import time

import requests

logger = logging.getLogger(__name__)

MAX_RETRY = 3
TIMEOUT_SECONDS = 10
VALID_FEEDS = ("autogempa", "gempaterkini", "gempadirasakan")


class ExtractError(Exception):
    """Raised when a feed cannot be fetched (rejected by the server or retries exhausted)."""


def build_feed_url(feed_name: str, base_url: str) -> str:
    """Return the full URL for a BMKG feed, e.g. 'autogempa' -> '<base_url>/autogempa.json'.

    base_url is passed in by the caller (see config.py) so this function never
    reads the environment itself and can be tested with any URL.
    """
    # Reject unknown names before touching the network.
    if feed_name not in VALID_FEEDS:
        raise ValueError(f"Unknown feed '{feed_name}'. Valid feeds: {VALID_FEEDS}")

    # rstrip("/") avoids a double slash if the base URL ends with "/".
    return f"{base_url.rstrip('/')}/{feed_name}.json"


def fetch_feed(feed_name: str, base_url: str) -> dict:
    """Fetch one BMKG feed and return the parsed JSON.

    Retries timeouts, connection errors, 5xx responses and non-JSON bodies with
    exponential backoff. Any failure surfaces as ExtractError: a 4xx response
    immediately (retrying cannot fix our own request), the others once every
    attempt has failed.
    """
    url = build_feed_url(feed_name, base_url)
    last_error = None

    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()  # turns 4xx/5xx into requests.HTTPError
            return response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code
            if status < 500:
                # 4xx: our request is wrong, retrying will not help.
                raise ExtractError(
                    f"Feed '{feed_name}' rejected with HTTP {status} (not retried): {exc}"
                ) from exc
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

    # Reaching this line means every attempt failed (a success returns inside the loop).
    # Raise instead of returning None so the failure can never pass silently;
    # "from last_error" keeps the original cause visible in the traceback.
    raise ExtractError(
        f"Failed to fetch feed '{feed_name}' after {MAX_RETRY} attempts: {last_error}"
    ) from last_error
