# Move off Gmail SMTP?

Type: grilling
Status: open
Blocked by: 05

## Question

Should notification email move from Gmail SMTP with an app password to a transactional provider (Resend, Postmark, SES)? Consider:
- deliverability and sending limits
- whether credentials expire
- per-send status and webhooks
- the effect on every notification type, not only reports

This was deferred on purpose (ticket 03). It's in scope only if it affects reliable report delivery.
