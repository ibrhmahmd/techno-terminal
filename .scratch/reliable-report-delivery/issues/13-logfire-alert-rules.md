# Logfire events and alert rules

Type: grilling
Status: open
Blocked by: 10, 12

## Question

Which events must the app emit, with which attributes? For example: report type, period, recipient count, sent/failed counts, `smtp_auth_failed`.

What are the alert rules? Specifically:
- the absence window for each report type
- failure rules
- a rule for SMTP authentication failing on any notification

What is the query cadence, and how do we avoid noisy alerts?
