# Managing the pg_cron jobs and secret, and the rollout path

Type: grilling
Status: open
Blocked by: 10

## Question

Where do the `pg_cron` jobs live: a versioned migration in `db/migrations/`, or configured by hand in the dashboard?

- Where is the trigger secret kept? Supabase Vault vs inline, and how it matches `INTERNAL_TRIGGER_SECRET` in the FastAPI Cloud env.
- How does the rollout follow the environment ladder? That means the testing project (`qugffjtucavdseczbata`) first, then production (`srbppkcvrgioneitktdj`).
- Note from ticket 06: the testing project has **no report templates** and no weekly recipients. The rollout has to seed them, without writing production data into testing by accident.
