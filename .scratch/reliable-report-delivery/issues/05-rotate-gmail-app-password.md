# Change the Gmail app password

Type: task
Status: open
Blocked by:

## Question

HITL. Generate a new Gmail app password for `GMAIL_SENDER_ADDRESS`. Update `GMAIL_APP_PASSWORD` in the FastAPI Cloud environment, `.env` and `.env.test`. Then confirm a send works, for example with `scripts/send_test_email.py` and a new `SENT` row in `notification_logs`.

Walk through it with `$wizard`. Record the date it was done and the first new `SENT` timestamp.
