# Measure the real request cutoff on FastAPI Cloud

Type: task
Status: open
Blocked by:

## Question

HITL, because it needs a deploy. Deploy a temporary authenticated endpoint that sleeps N seconds (N = 10, 20, 40, 90, 130). Record where the request gets cut off and with which status (Envoy 504/408 or Cloudflare 524).

Also record whether an `asyncio.create_task` started just before the response finishes after about 5 minutes of no traffic, i.e. whether it survives scale-down.

Remove the endpoint afterwards. Deploy from a clean tree (`git stash` first), because `fastapi deploy` uploads uncommitted files.
