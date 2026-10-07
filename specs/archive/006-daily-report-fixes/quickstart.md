# Quickstart: Daily Report Fixes

## Implementation Order

### Phase 1: Fix Data Bugs

1. **Fix Bug 1** — `report_notifications.py:272-278`: Correct instructor query column names
2. **Fix Bug 2** — `report_notifications.py:253-257`: Resolve group name through enrollment chain
3. **Fix Bug 3** — `report_notifications.py:237-247`: Align payment date filter with `receipts.paid_at`

### Phase 2: Template Redesign

4. **Fix Bug 4** — `daily_report_pdf.py`: Rewrite PDF template for B&W printing
5. **Fix Bug 5** — `report_notifications.py:46-67`: Add `@media print` styles to email HTML

### Phase 3: Tests

6. **Add tests** — `test_notifications.py`: Add `TestReportNotifications` class with 3 tests

## Verification

```bash
# Run all notification tests
pytest tests/test_notifications.py -v

# Run only report tests
pytest tests/test_notifications.py::TestReportNotifications -v
```

## Dependencies

- ReportLab (`reportlab`) — already installed, used by existing PDF generation
- No new dependencies required
- No database migration required
