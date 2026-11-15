"""Entry point: runs the six pipeline steps in order for a single run."""
import logging
import sys

from .config import REPO_ROOT, load_config
from .extract import VALID_FEEDS, ExtractError, fetch_feed
from .land import land_raw
from .logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """Run one pipeline cycle and return a process exit code (0 = every feed succeeded).

    Only extract and land exist so far; validate, transform and load come later.
    """
    # Load the configuration once, outside any try: a broken .env should stop the run
    # immediately instead of failing the same way for every feed.
    cfg = load_config()

    setup_logging(cfg.log_level, str(REPO_ROOT / "logs"))
    logger.info("Pipeline run started")

    # The three feeds are independent: one failing must not stop the others,
    # because BMKG keeps no history and data that is not fetched now can be lost.
    failed_feeds = []
    for feed_name in VALID_FEEDS:
        try:
            payload = fetch_feed(feed_name, cfg.bmkg_base_url)
            path = land_raw(feed_name, payload, cfg.raw_data_dir)
        except (ExtractError, OSError):
            # Only expected failures are caught (BMKG unreachable, disk problem).
            # Anything else is a bug and should surface.
            logger.exception("Feed '%s' failed", feed_name)
            failed_feeds.append(feed_name)
        else:
            logger.info("Feed '%s' landed at %s", feed_name, path)

    # One summary line per run: this is the line to look for in the log.
    succeeded = len(VALID_FEEDS) - len(failed_feeds)
    log = logger.error if failed_feeds else logger.info
    log("Pipeline run finished: %d succeeded, %d failed %s", succeeded, len(failed_feeds), failed_feeds)

    # The exit code is the report to the scheduler: non-zero when anything failed.
    return 1 if failed_feeds else 0


if __name__ == "__main__":
    sys.exit(main())
