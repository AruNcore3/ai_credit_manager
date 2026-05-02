from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from services.reconcilation_service import reconile_initiated_topups


def main() -> int:
    parser = argparse.ArgumentParser(description="Run top-up reconciliation sweep.")
    parser.add_argument("--older-than-minutes", type=int, default=5)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("reconciliation_runner")

    db = SessionLocal()
    try:
        summary = reconile_initiated_topups(
            db=db,
            older_than_minutes=args.older_than_minutes,
            limit=args.limit,
        )
        logger.info("reconciliation_summary %s", json.dumps(summary, sort_keys=True))
        print(json.dumps(summary))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
