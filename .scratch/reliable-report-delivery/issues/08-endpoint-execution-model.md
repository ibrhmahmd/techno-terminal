# Endpoint execution model and response contract

Type: grilling
Status: resolved
Blocked by: 06, 07, 17

## Question

Should the trigger endpoint do the whole report run inside the request (synchronous), or accept and return 202 while doing the work in the background?

What should it return when some or all deliveries fail? Today `send_*_report` returns `None` and the endpoint answers `200 success:true` even when every send failed.

## Answer

Run the report **inside the request**. Return HTTP 500 when the outcome is `partial`, `failed` or `not_configured`, and 200 otherwise, using the standard envelope. Default accepted by the user on 2026-09-25. Revisit if ticket 17 measures a cutoff under about 25s.
