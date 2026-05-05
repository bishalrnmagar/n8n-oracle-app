"""
Weekly Finance Analytics Runner.

Modes:
  --once       Run once immediately (for testing / manual trigger)
  --schedule   Run on weekly schedule (default: Sunday 9:00 AM)
"""

import argparse
import schedule
import time
import logging

from db import query_df
from report import build_weekly_report
from sender import send_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def get_active_users():
    df = query_df("SELECT id, telegram_id FROM users WHERE is_active = true")
    return df.to_dict("records")


def run_weekly_report():
    log.info("Starting weekly report generation")
    users = get_active_users()

    if not users:
        log.warning("No active users found")
        return

    for user in users:
        try:
            report_text = build_weekly_report(user["id"])
            send_report(report_text, chat_id=str(user["telegram_id"]))
            log.info(f"Report sent to user {user['telegram_id']}")
        except Exception as e:
            log.error(f"Failed for user {user['telegram_id']}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Finance Analytics")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--day", default="sunday", help="Day to send report (default: sunday)"
    )
    parser.add_argument(
        "--time", default="09:00", dest="send_time", help="Time to send (default: 09:00)"
    )
    args = parser.parse_args()

    if args.once:
        run_weekly_report()
        return

    log.info(f"Scheduling weekly report: every {args.day} at {args.send_time}")
    getattr(schedule.every(), args.day).at(args.send_time).do(run_weekly_report)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
