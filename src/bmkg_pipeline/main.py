"""Entry point: runs the six pipeline steps in order for a single run."""
import logging
import sys
from datetime import datetime, timezone

from .config import REPO_ROOT, load_config
from .extract import VALID_FEEDS, ExtractError, fetch_feed
from .land import land_raw
from .logging_setup import setup_logging
from .transform import transform_record
from .validate import validate_record

logger = logging.getLogger(__name__)


def _records_of(payload: dict) -> list[dict]:
    """Return the earthquake records of a feed payload as a list.

    Most feeds hold a list of records, but "autogempa" holds a single object.
    A KeyError here means BMKG changed the structure: let it surface (fail hard).
    """
    records = payload["Infogempa"]["gempa"]
    return records if isinstance(records, list) else [records]


def main() -> int:
    """Run one pipeline cycle and return a process exit code (0 = every feed was fetched and landed).

    Extract, land, validate and transform are wired; load comes later.
    """
    # Load the configuration once, outside any try: a broken .env should stop the run
    # immediately instead of failing the same way for every feed.
    cfg = load_config()

    setup_logging(cfg.log_level, str(REPO_ROOT / "logs"))
    logger.info("Pipeline run started")

    # One timestamp for the whole run: it names the raw files and is stored on every row,
    # so a row can always be traced back to the exact raw file it came from.
    ingested_at = datetime.now(timezone.utc)

    # Phase 1 - fetch and land every feed. The three feeds are independent: one failing must
    # not stop the others, because BMKG keeps no history and data that is not fetched now
    # can be lost.
    failed_feeds = []
    landed = {}  # feed name -> payload, for the processing phase
    for feed_name in VALID_FEEDS:
        try:
            payload = fetch_feed(feed_name, cfg.bmkg_base_url)
            path = land_raw(feed_name, payload, cfg.raw_data_dir, ingested_at)
        except (ExtractError, OSError):
            # Only expected failures are caught (BMKG unreachable, disk problem).
            # Anything else is a bug and should surface.
            logger.exception("Feed '%s' failed", feed_name)
            failed_feeds.append(feed_name)
        else:
            landed[feed_name] = payload
            logger.info("Feed '%s' landed at %s", feed_name, path)

    # Phase 2 - validate and transform. It runs after ALL feeds are landed, so a bug or a
    # structure change here can never cost us raw data; the raw files allow a replay.
    total_valid = total_rejected = 0
    for feed_name, payload in landed.items():
        rows = []  # typed rows, handed to load once it exists
        rejected = 0
        records = _records_of(payload)
        for record in records:
            reasons = validate_record(record)
            if reasons:
                # Not lost: the raw file still holds the record. The reasons go to the log
                # until a quarantine table exists.
                rejected += 1
                logger.warning(
                    "Rejected record from '%s' (DateTime=%s): %s",
                    feed_name, record.get("DateTime"), "; ".join(reasons),
                )
            else:
                rows.append(transform_record(record, feed_name, ingested_at))

        total_valid += len(rows)
        total_rejected += rejected
        logger.info(
            "Feed '%s': %d records, %d valid, %d rejected", feed_name, len(records), len(rows), rejected
        )

    # One summary line per run: this is the line to look for in the log.
    succeeded = len(VALID_FEEDS) - len(failed_feeds)
    log = logger.error if failed_feeds else logger.info
    log(
        "Pipeline run finished: %d succeeded, %d failed %s; %d valid records, %d rejected",
        succeeded, len(failed_feeds), failed_feeds, total_valid, total_rejected,
    )

    # The exit code is the report to the scheduler: non-zero when a feed could not be
    # fetched or landed. Rejected records are a data-quality signal, not a failed run.
    return 1 if failed_feeds else 0


if __name__ == "__main__":
    sys.exit(main())
