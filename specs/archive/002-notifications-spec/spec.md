# Feature Specification: Notifications Module

**Feature Branch**: `002-notifications-spec`
**Created**: 2026-05-12
**Status**: Draft
**Input**: User description: "create spec for the notifications module"

## Clarifications

### Session 2026-05-12

- Q: Retry strategy for failed deliveries → A: Automatic retry up to 3 times (1min, 5min, 30min delays) + manual retry option from notification logs.
- Q: Bulk notifications to parents scope → A: Deferred for later consideration. Bulk notifications feature removed from scope.
- Q: Single vs multi-channel per recipient → A: Focus on email for now. Admin decides per notification type which channel to use (channel expansion deferred).

## User Scenarios & Testing

### User Story 1 - Admin Receives Enrollment Alerts (Priority: P1)

As an admin, I want to receive notifications when students are enrolled, complete a level, drop out, or transfer between groups, so that I can stay informed about student lifecycle events without manually checking the system.

**Why this priority**: Enrollment events are the core operational workflow — notifications replace manual tracking and prevent missed updates.

**Independent Test**: Can be tested by creating an enrollment and verifying a notification is sent to the configured recipients within a reasonable timeframe.

**Acceptance Scenarios**:

1. **Given** a student is enrolled in a group, **When** the enrollment is confirmed, **Then** a notification with student name, group name, and level is sent to all active recipients subscribed to enrollment notifications
2. **Given** a student completes a level, **When** the level progression is recorded, **Then** a notification with student name and new level is sent to all active recipients subscribed to level progression notifications
3. **Given** an enrollment is dropped, **When** the drop action is saved, **Then** a notification with student name and reason is sent to all active recipients subscribed to enrollment notifications
4. **Given** a student transfers between groups, **When** the transfer is completed, **Then** a notification with student name, source group, and destination group is sent to all active recipients subscribed to enrollment notifications

---

### User Story 2 - Admin Receives Payment Notifications (Priority: P1)

As an admin, I want to receive notifications when payments are received and when payments are due, so that I can track financial activity and follow up on outstanding balances.

**Why this priority**: Payment notifications are critical for financial operations and cash flow management.

**Independent Test**: Can be tested by recording a payment and verifying a notification email with receipt details is sent to the configured recipients.

**Acceptance Scenarios**:

1. **Given** a payment is recorded against a receipt, **When** the payment is saved, **Then** a notification email with receipt number, amount, and PDF receipt attachment is sent to all active recipients subscribed to payment notifications
2. **Given** an enrollment has an outstanding balance, **When** a payment reminder is triggered, **Then** a notification with amount due and due date is sent to all active recipients subscribed to payment reminders

---

### User Story 3 - Admin Receives Scheduled Business Reports (Priority: P2)

As a center manager, I want to receive daily, weekly, and monthly business summary reports via email, so that I can monitor revenue, attendance, enrollment trends, and key performance indicators without logging into the system.

**Why this priority**: Scheduled reports automate managerial oversight and reduce the need for manual data gathering.

**Independent Test**: Can be tested by configuring a report time and verifying the report email is delivered with the correct summary data and PDF attachment.

**Acceptance Scenarios**:

1. **Given** the daily report is scheduled, **When** the configured time is reached, **Then** a report email with revenue, sessions held, attendance count, and payment breakdown is sent to all active recipients
2. **Given** it is Monday, **When** the daily report is triggered, **Then** a weekly report is also sent with revenue trends, new student count, and attendance rate
3. **Given** it is the 1st of the month, **When** the daily report is triggered, **Then** a monthly report is also sent with revenue, new enrollments, and active student count

---

### User Story 4 - Admin Manages Notification Templates (Priority: P2)

As an admin, I want to create, preview, test, and update notification templates with variable placeholders, so that notification content can be customized without code changes.

**Why this priority**: Template customization enables localized messaging, branding, and format adjustments.

**Independent Test**: Can be tested by creating a template with placeholder variables and sending a test notification via the template's channel to verify correct rendering.

**Acceptance Scenarios**:

1. **Given** an admin has template management access, **When** they create a new template with a name, body, and variable list, **Then** the template is saved and available for use
2. **Given** a template exists, **When** an admin updates it, **Then** standard templates prevent modification of name and variables
3. **Given** a template exists, **When** an admin requests a test send, **Then** the template is rendered with placeholder values and test emails are sent to all active recipients
4. **Given** a template is marked as standard, **When** an admin attempts to delete it, **Then** the deletion is blocked

---

### User Story 5 - Admin Manages Notification Recipients (Priority: P2)

As an admin, I want to manage a list of email recipients and assign them to specific notification types, so that the right people get the right notifications.

**Why this priority**: Recipient management ensures notifications reach the appropriate staff without overwhelming everyone with all messages.

**Independent Test**: Can be tested by adding a recipient with notification type filters, then triggering a matching event and verifying the email is sent.

**Acceptance Scenarios**:

1. **Given** an admin has recipient management access, **When** they add a new recipient with an email address and optional notification type filters, **Then** that recipient receives only matching notifications
2. **Given** a recipient exists, **When** an admin toggles their active status off, **Then** no notifications are sent to that recipient
3. **Given** a recipient exists with notification type filters, **When** an admin updates the filters, **Then** future notifications respect the updated filters

---

### User Story 6 - Admin Receives Competition Notifications (Priority: P3)

As an admin, I want to receive notifications when a team is registered for a competition, a competition fee is paid, or a placement result is announced, so that I can track competition-related activities.

**Why this priority**: Competition events are less frequent but still require notification coverage for completeness.

**Independent Test**: Can be tested by registering a team in a competition and verifying a notification is sent via the recipient's preferred channel.

**Acceptance Scenarios**:

1. **Given** a team is registered for a competition, **When** the registration is saved, **Then** a notification with team name and competition details is sent to all active recipients subscribed to competition notifications
2. **Given** a competition fee payment is recorded, **When** the payment is saved, **Then** a notification with team name and amount is sent
3. **Given** a competition placement is announced, **When** the result is recorded, **Then** a notification with team name, rank, and competition name is sent

---

### Edge Cases

- What happens when no recipients are configured for a notification type? The system should log a warning and alert the configured fallback contact.
- What happens when an email dispatch fails (invalid address, SMTP timeout)? The notification log should record the failure, trigger automatic retry (up to 3 attempts), and not block the originating operation.
- How does the system handle concurrent notification sends for the same event? Notifications should be logged independently without race conditions.
- What happens when the email service is temporarily unavailable? Failed sends should be logged and retried; the system should continue operating without throwing errors to the user.
- How does the scheduler behave after a server restart? Reports should not be sent twice for the same day.
- What happens when all 3 automatic retry attempts fail? The notification should be marked as permanently failed and remain available in the log for manual retry.
- How does the admin configure which channel each notification type uses? The admin settings API should expose a channel selection per notification type, currently defaulting to email.

## Requirements

### Functional Requirements

- **FR-001**: System MUST send email notifications for enrollment lifecycle events: created, completed, dropped, transferred
- **FR-002**: System MUST send email notifications for payment events: received (with PDF receipt), and due reminder
- **FR-003**: System MUST support scheduled daily, weekly, and monthly business summary reports via email
- **FR-004**: System MUST support competition event notifications: team registration, fee payment, placement announcement
- **FR-005**: Users MUST be able to create, read, update, and delete notification templates
- **FR-006**: Standard system templates MUST be protected from name, variable, and channel changes
- **FR-007**: Standard system templates MUST be protected from deletion
- **FR-008**: Users MUST be able to preview and test-send a rendered template to all active recipients
- **FR-009**: Users MUST be able to add, update, and remove additional email recipients
- **FR-010**: Each additional recipient MUST be assignable to specific notification types (or all types)
- **FR-011**: Users MUST be able to toggle individual notification types on/off
- **FR-012**: All sent notifications MUST be logged with status, timestamp, recipient, and channel
- **FR-013**: Failed notification sends MUST be logged with the error message without blocking the initiating operation
- **FR-014**: Failed notification sends MUST be automatically retried up to 3 times with progressive delays (approximately 1min, 5min, 30min)
- **FR-015**: After all automatic retry attempts are exhausted, the failed status MUST be final and the notification MUST remain accessible for manual retry
- **FR-016**: Users MUST be able to manually retry a failed notification from the notification log
- **FR-017**: System MUST alert the configured fallback contact when no valid recipients exist for a notification type
- **FR-018**: System MUST send notifications via the email channel
- **FR-019**: Admin MUST be able to configure which channel each notification type uses (email for now, extensible to additional channels later)
- **FR-020**: Email notifications with attachments (PDF receipts, reports) MUST include the attachment in the email
- **FR-021**: Scheduled reports MUST NOT be sent more than once per day/week/month after server restarts

### Key Entities

- **Notification Template**: A reusable message definition with a name, subject template, body template with `{{variable}}` placeholders, and a list of declared variables. Templates can be standard (system-protected) or custom.
- **Recipient**: A person who receives notifications, defined by an email address, optional label, and optional list of notification types they subscribe to. Recipients can be active or inactive.
- **Admin Setting**: Per-notification-type configuration including enabled/disabled toggle and delivery channel selection (currently email, extensible to additional channels).
- **Scheduled Report**: A time-triggered business summary (daily/weekly/monthly) that aggregates key metrics (revenue, attendance, enrollment counts) and delivers via email with a PDF attachment.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Enrollment, payment, and competition notifications are delivered within 5 minutes of the triggering event
- **SC-003**: Failed delivery does not impact the success or response time of the originating API operation; automatic retries execute in the background without blocking new notifications
- **SC-004**: All notification send attempts (success and failure) are recorded in the log with sufficient detail for audit
- **SC-005**: Template test-send feature verifies rendered output matches expected variable substitution before live sending
- **SC-006**: Recipient can be added, toggled, and removed without requiring system restart or code deployment

## Assumptions

- Email is the current notification channel; additional channels (WhatsApp, SMS) can be added later via the admin-configurable channel setting
- PDF receipts and reports are sent as email attachments
- Admin users are technical enough to configure recipients and manage templates via the API
- The system has access to a working email server (Gmail SMTP) and valid sender credentials
- Recipients are staff members, not parents or students (parent-directed and bulk notifications are deferred for later consideration)
- Scheduled reports are sent to the same recipient list as other notifications
- Report scheduler tolerates up to 5 minutes of drift without sending duplicate reports
- The existing fallback email mechanism (single configured fallback address) is a safety net, not a primary delivery path
