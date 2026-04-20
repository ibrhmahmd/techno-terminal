# Finalizing Notification Service Implementation

This plan covers the final steps to make the Notification Service fully operational, including database schema creation, standard template seeding, and integration with the Analytics module for automated business reports.

## User Review Required

> [!IMPORTANT]
> **Environment Variables Verification**: Please ensure the following variables are set in your `.env` file for the dispatchers to work:
> - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`
> - `GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`

> [!WARNING]
> **Database Migration**: This plan will execute DDL to create 3 new tables: `notification_templates`, `notification_logs`, and `notification_subscribers`.

## Proposed Changes

---

### [NEW] Database Schema & Seeding
Create the necessary tables and populate them with standard business templates.

#### [NEW] SQL Script: `create_notification_tables.sql`
- `notification_templates`: stores message bodies with `{{variable}}` placeholders.
- `notification_logs`: audit trail of every send attempt.
- `notification_subscribers`: mappings of employees to scheduled reports.

#### Seed Data
We will seed 7 standard templates:
1. `absence_alert` (WhatsApp)
2. `enrollment_confirmation` (WhatsApp)
3. `payment_receipt` (WhatsApp)
4. `daily_report` (Email)
5. `weekly_report` (Email)
6. `monthly_report` (Email)
7. `bulk_marketing` (WhatsApp)

---

### [MODIFY] Service Layer
Implement the missing report generation logic.

#### [MODIFY] [notification_service.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/modules/notifications/services/notification_service.py)
- Integrate `AcademicAnalyticsService` and `FinancialAnalyticsService`.
- Implement `send_daily_report()`: fetch aggregates (revenue, new enrollments, attendance) and email all DAILY subscribers.
- Implement `send_weekly_report()`: fetch weekly analytics and email WEEKLY subscribers.
- Implement `send_monthly_report()`: fetch monthly summaries and email MONTHLY subscribers.

---

### [MODIFY] API Dependencies
Ensure consistent injection of the notification service.

#### [MODIFY] [dependencies.py](file:///e:/Users/ibrahim/Desktop/techno_data_%20Copy/app/api/dependencies.py)
- Minor cleanup to ensure `NotificationService` is properly instantiated with a fresh session where needed.

---

## Open Questions

1. **Email Body Format**: Should the automated reports be sent as plain text or should I include basic HTML table formatting for better readability? (Defaulting to basic HTML tables).
2. **Report Time**: The scheduler is currently set to 08:00 AM. Is this preferred, or should it be end-of-day (e.g., 10:00 PM)?

## Verification Plan

### Automated Tests
- Run `pytest tests/api/notifications/` (if I create them) or manual check via Swagger UI.

### Manual Verification
1. **Template Seeding**: Verify tables exist and `GET /api/v1/notifications/templates` returns 7 standard items.
2. **Transactional Send**: Trigger an absence alert via UI/API and verify log status is `SENT` or `FAILED` (with error).
3. **Report Generation**: Manually invoke `send_daily_report()` via a temporary test endpoint to verify analytics data is correctly fetched and rendered.
