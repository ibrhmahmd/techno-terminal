# Spec 006: Daily Report Data & Template Fixes

## Overview

The daily business report feature produces empty data sections and uses a PDF/email template that renders poorly on black-and-white printers. This spec documents 5 bugs found in the implementation.

---

## Bug 1: Instructor Query Uses Wrong Column Names

**File:** `app/modules/notifications/services/report_notifications.py:272-278`

**Severity:** High — `instructors_list` is always empty

**Current query:**
```sql
SELECT DISTINCT e.name
FROM sessions s
JOIN employees e ON s.instructor_id = e.id
WHERE s.date = :target_date
```

**Problems:**

| Column | Current | Actual | Evidence |
|--------|---------|--------|----------|
| Employee name | `e.name` | `e.full_name` | `EmployeeBase.full_name` in `app/modules/hr/models/employee_models.py:18` |
| Session instructor FK | `s.instructor_id` | `s.actual_instructor_id` | `CourseSession.actual_instructor_id` in `app/modules/academics/models/session_models.py:18` |
| Session date | `s.date` | `s.session_date` | `CourseSession.session_date` in `app/modules/academics/models/session_models.py:15` |

**Fix:** Rename all three columns:
```sql
SELECT DISTINCT e.full_name
FROM sessions s
JOIN employees e ON s.actual_instructor_id = e.id
WHERE s.session_date = :target_date
```

---

## Bug 2: Payment Model Has No `group_id` Column

**File:** `app/modules/notifications/services/report_notifications.py:253-257`

**Severity:** High — `payment_details` section is always empty

**Current code:**
```python
student = session.get(Student, payment.student_id)
student_name = student.full_name if student else "Unknown"

group = session.get(Group, payment.group_id) if payment.group_id else None  # FAILS
group_name = group.name if group else "N/A"
```

**Root cause:** The `Payment` model (`app/modules/finance/models/payment.py`) has **no `group_id` column**. The `Group` association exists through `Payment.enrollment_id → Enrollment.group_id`.

When `payment.group_id` is accessed, an `AttributeError` is raised. The exception is caught by the generic `except` on line 265 and silently logged, resulting in zero payment details.

**Fix:** Resolve group name through the enrollment chain:
```python
student = session.get(Student, payment.student_id)
student_name = student.full_name if student else "Unknown"

enrollment = session.get(Enrollment, payment.enrollment_id) if payment.enrollment_id else None
group_name = "N/A"
if enrollment and enrollment.group_id:
    group = session.get(Group, enrollment.group_id)
    group_name = group.name if group else "N/A"
```

---

## Bug 3: Date Filter Mismatch Between Revenue and Payment Count

**File:** `app/modules/notifications/services/report_notifications.py:178-181, 237-242`

**Severity:** Medium — payment count may differ from revenue data

**Current behavior:**

| Query | Date Column Used | Table |
|-------|-----------------|-------|
| Revenue total | `receipts.paid_at` | Via `FinancialAnalyticsService` (wraps `financial_repository.py:21-35`) |
| Payment count | `payments.created_at` | Direct SQL via `report_notifications.py:238` |

If a receipt is paid on day X but the payment record was created on day Y (e.g., backdated entry), the two queries disagree. This means `payment_count` could be 0 while `total_revenue` is non-zero, or vice versa.

**Fix:** Align the payment count query to use the same date source. Since revenue uses `receipts.paid_at`, the payment detail query should join through `receipts` and filter by `receipts.paid_at`:

```python
# Join payments with receipts for consistent date filtering
payment_stmt = (
    select(Payment)
    .join(Receipt, Payment.receipt_id == Receipt.id)
    .where(
        Receipt.paid_at >= target_date,
        Receipt.paid_at < target_date + timedelta(days=1),
        Payment.deleted_at.is_(None),
    )
)
```

**Imports to add:** `from app.modules.finance.models.receipt import Receipt`

---

## Bug 4: PDF Template Not B&W Printer Friendly

**File:** `app/modules/notifications/pdf/daily_report_pdf.py`

**Severity:** Medium — report is unreadable when printed grayscale

**Problems:**

| Element | Style | B&W Issue |
|---------|-------|-----------|
| Title | `#667eea` (purple-blue) | Light gray text on B&W, hard to read |
| Summary card headers | Green/blue/orange/purple backgrounds with `whitesmoke` text | Text disappears against gray background |
| Summary card values | Light colored backgrounds (`#E8F5E9`, `#E3F2FD`, etc.) | All render as same light gray |
| Metrics table header | `#667eea` background | Same light gray as body rows |
| Payment details header | `#2c3e50` background with `whitesmoke` text | Text invisible in grayscale |
| Alternating row colors | White only (no alternating) | OK, but missed opportunity for lightweight separators |
| Font colors | `#333333`, `#666666`, `#999999`, `#E65100` | `#999999` is too light for B&W |

**Requirements:**
1. All text must be **black** (`#000000`) on white background — no colored text
2. Section headers use **bold** and **borders**, not background colors
3. Summary cards use **thin black borders** and **white backgrounds**
4. Alternating table rows use **very light gray** (`#f5f5f5`) if any shading
5. All grid lines must be **black** (`#000000`) or dark gray (`#555555`)
6. Minimum font size 10pt for body, 14pt for headings
7. Footer remains minimal and in black

---

## Bug 5: Email HTML Template Not Print Friendly

**File:** `app/modules/notifications/services/report_notifications.py:46-67`

**Severity:** Medium — email preview and print render poorly

**Current HTML table styles:**
```html
<tr style="background: #2c3e50; color: white;">
```
```html
<p style='color: #666; font-style: italic;'>No payments recorded today.</p>
```

**Problems:**
- Table header with dark background + white text is invisible on B&W print
- `color: #666` is low contrast on some printers
- No `@media print` CSS rules
- No print-friendly fallback colors
- Monolithic inline styles are hard to maintain

**Requirements:**
1. Add `<style>` block with `@media print` rules
2. Table headers should use **black text on white** with **bottom border** in print mode
3. All colored text should have a black fallback for print
4. Responsive table design for mobile email clients

---

## Files Affected

| File | Bugs | Change Type |
|------|------|-------------|
| `app/modules/notifications/services/report_notifications.py` | 1, 2, 3 | Fix queries + payment group resolution + date alignment |
| `app/modules/notifications/pdf/daily_report_pdf.py` | 4 | Full PDF template redesign (B&W) |
| `app/modules/notifications/services/report_notifications.py` (template strings) | 5 | Email HTML template update |

## Acceptance Criteria

1. Daily report shows instructor names when sessions exist with instructors
2. Daily report shows payment details (student name, group name, amount) for same-day payments
3. Payment count matches revenue date range (both use `receipts.paid_at`)
4. PDF prints clearly on B&W printer — all text readable, no colored backgrounds interfering
5. Email renders with print-friendly styles — table headers visible on B&W printout

## Test Plan

### Automated Tests
- `TestReportNotifications.test_daily_report_instructors_list` — verify instructor names appear
- `TestReportNotifications.test_daily_report_payment_details` — verify payment detail rows appear
- `TestReportNotifications.test_daily_report_date_alignment` — verify payment count aligns with revenue

### Manual Verification
- Generate daily report PDF, print to B&W → verify all text readable
- Open daily report email, use browser print preview → verify header text visible
