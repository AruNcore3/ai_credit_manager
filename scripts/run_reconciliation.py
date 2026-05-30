from __future__ import annotations

import argparse
import json
import logging
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.observability import observability
from services.reconcilation_service import reconile_initiated_topups


def main() -> int:
    parser = argparse.ArgumentParser(description="Run top-up reconciliation sweep.")
    parser.add_argument("--older-than-minutes", type=int, default=5)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=int, default=10)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("reconciliation_runner")

    attempt = 1
    while attempt <= max(args.retries, 1):
        db = SessionLocal()
        try:
            summary = reconile_initiated_topups(
                db=db,
                older_than_minutes=args.older_than_minutes,
                limit=args.limit,
            )
            logger.info(
                "reconciliation_summary attempt=%s %s",
                attempt,
                json.dumps(summary, sort_keys=True),
            )
            print(json.dumps(summary))
            return 0
        except Exception as exc:
            is_alert = observability.increment_event("reconciliation_run_failed")
            logger.exception("reconciliation_run_failed attempt=%s error=%s", attempt, str(exc))
            if is_alert:
                logger.error("alert_triggered type=reconciliation_run_failures threshold_window=60s")
            if attempt >= args.retries:
                return 1
            sleep_seconds = max(args.retry_delay_seconds, 1) * attempt
            logger.warning("reconciliation_retry_scheduled in_seconds=%s", sleep_seconds)
            time.sleep(sleep_seconds)
            attempt += 1
        finally:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())
