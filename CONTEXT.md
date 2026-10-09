# Techno Terminal

Operations system for a STEM education center: students, groups, enrollments, payments, staff, and the business notifications sent about them.

## Language

### Scheduled reporting

**Scheduled Report**:
A daily, weekly or monthly business summary emailed to Report Recipients on a fixed schedule.
_Avoid_: digest, business email, cron report

**Report Period**:
The span of business activity a Scheduled Report covers. It's one day for a daily report, the Monday–Sunday week for a weekly report, and the calendar month for a monthly report.
_Avoid_: report date range, window

**Report Recipient**:
A person subscribed to a type of Scheduled Report through the notification settings.
_Avoid_: admin, subscriber, fallback

**Delivery**:
One Scheduled Report, for one Report Period, sent to one Report Recipient. It counts as delivered only when its send succeeded.
_Avoid_: send, dispatch, log entry

**Trigger**:
The external, scheduled request that asks the system to produce the Scheduled Reports that are due.
_Avoid_: scheduler, cron, job

### People

**Employee**:
A staff member of the center (instructor, admin or other role) as an HR record, whether or not they can sign in.
_Avoid_: staff, user, instructor (when meaning the record)

**Staff Account**:
The sign-in identity someone uses to access the system, with a role that decides what they may do. It is usually linked to an Employee, but it doesn't have to be (e.g. a system administrator). An Employee without one cannot sign in.
_Avoid_: user, login, account
