"""
scripts/test_report_email.py
────────────────────────────
Send a test daily report email with the new Precision Engine design.

Usage:
    python scripts/test_report_email.py --to admin@example.com
    python scripts/test_report_email.py --to admin@example.com --save-pdf
    python scripts/test_report_email.py --to admin@example.com --date 2026-05-24
"""
import argparse
import logging
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def send_test_email(recipient: str, report_date: date, save_pdf: bool = False) -> None:
    from app.modules.notifications.services.report_notifications import ReportNotificationService
    from app.modules.notifications.repositories.notification_repository import NotificationRepository
    from app.db.connection import get_session

    with get_session() as session:
        repo = NotificationRepository(session)
        svc = ReportNotificationService(repo)

        import asyncio
        asyncio.run(svc.send_daily_report(target_date=report_date))

    logger.info(f"Test email sent to {recipient} for {report_date.isoformat()}")

    if save_pdf:
        try:
            pdf_bytes = svc.get_daily_report_pdf_base64(report_date)
            pdf_path = f"test_report_{report_date.isoformat()}.pdf"
            with open(pdf_path, "wb") as f:
                import base64
                f.write(base64.b64decode(pdf_bytes[1]))
            logger.info(f"PDF saved to {pdf_path}")
        except Exception as e:
            logger.warning(f"Could not save PDF: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a test daily report email with Precision Engine design"
    )
    parser.add_argument(
        "--to", required=True,
        help="Recipient email address"
    )
    parser.add_argument(
        "--date", default="2026-05-24",
        help="Report date (YYYY-MM-DD). Default: 2026-05-24"
    )
    parser.add_argument(
        "--save-pdf", action="store_true",
        help="Save generated PDF to disk for visual B&W inspection"
    )
    args = parser.parse_args()

    try:
        report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
        sys.exit(1)

    send_test_email(args.to, report_date, args.save_pdf)


if __name__ == "__main__":
    main()
