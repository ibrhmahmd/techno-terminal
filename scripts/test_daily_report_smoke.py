"""
scripts/test_daily_report_smoke.py
────────────────────────────────────
End-to-end smoke test for daily report fixes (Bugs 1-5).

Three ways to run:

  1. Pytest integration tests (recommended):
     py -m pytest tests/test_notifications.py::TestDailyReportIntegration -v -s

  2. Via running API server (tests email delivery):
     Start:        python run_api.py
     Then run:     py scripts/test_daily_report_smoke.py --api http://localhost:8000

  3. Unit tests only:
     py -m pytest tests/test_notifications.py::TestDailyReport -v

Options:
  --api URL    Base URL of running API (e.g. http://localhost:8000)
               Triggers template test endpoint to send a real email.
  --save-pdf   Save generated PDF to disk for visual B&W inspection
"""
import sys
import urllib.request
import urllib.error
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_via_api(base_url: str, save_pdf: bool = False) -> None:
    """Hit the running API to test template + email delivery."""
    import subprocess

    # Step 1: Get a test JWT
    logger.info("Getting test JWT...")
    result = subprocess.run(
        [sys.executable, "scripts/get_test_jwt.py"],
        capture_output=True, text=True, cwd="."
    )
    if result.returncode != 0:
        logger.error(f"Failed to get JWT: {result.stderr}")
        sys.exit(1)
    jwt = result.stdout.strip()
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }

    # Step 2: List templates to find daily_report template ID
    logger.info("Fetching templates...")
    req = urllib.request.Request(f"{base_url}/api/v1/notifications/templates", headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        templates = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.error(f"Failed to list templates: {e.code} {e.read().decode()}")
        sys.exit(1)

    # Find daily_report template
    template_id = None
    data = templates.get("data", templates) if isinstance(templates, dict) else templates
    for t in data if isinstance(data, list) else []:
        if t.get("name") == "daily_report" or t.get("code") == "daily_report":
            template_id = t.get("id")
            break
    if not template_id:
        logger.error("daily_report template not found in API response")
        sys.exit(1)
    logger.info(f"Found daily_report template (ID: {template_id})")

    # Step 3: Send test email using template test endpoint
    logger.info(f"Sending test email via template {template_id}...")
    req = urllib.request.Request(
        f"{base_url}/api/v1/notifications/templates/{template_id}/test",
        method="POST",
        headers=headers,
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        logger.info(f"Test email sent: {result}")
    except urllib.error.HTTPError as e:
        logger.error(f"Test template failed: {e.code} {e.read().decode()}")
        sys.exit(1)

    logger.info("=== Smoke test via API complete ===")
    logger.info("Check your email inbox for the test daily report.")
    logger.info("For B&W PDF inspection: open the PDF attachment and verify")
    logger.info("  - No colored backgrounds (black/white/gray only)")
    logger.info("  - Thin black borders on tables")
    logger.info("  - Black text on white backgrounds")


if __name__ == "__main__":
    save_pdf = "--save-pdf" in sys.argv

    api_url = None
    for i, arg in enumerate(sys.argv):
        if arg == "--api" and i + 1 < len(sys.argv):
            api_url = sys.argv[i + 1]

    if api_url:
        test_via_api(api_url, save_pdf)
    else:
        print(__doc__)
