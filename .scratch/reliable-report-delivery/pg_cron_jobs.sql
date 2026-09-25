-- Scheduled report triggers (production). Run in the Supabase SQL Editor
-- ONLY AFTER the new trigger endpoints are deployed.
-- Requires: pg_cron, pg_net, and the Vault secrets 'app_base_url' and 'internal_trigger_secret'.
-- Times are UTC. 05:00 UTC is 08:00 Cairo in summer (DST) and 07:00 in winter.
-- cron.schedule with an existing job name replaces that job, so re-running this file is safe.

select cron.schedule(
  'scheduled-report-daily',
  '0 5 * * *',
  $$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name = 'app_base_url')
           || '/api/v1/notifications/internal/reports/daily-report/trigger',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Internal-Trigger-Secret',
      (select decrypted_secret from vault.decrypted_secrets where name = 'internal_trigger_secret')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 120000
  );
  $$
);

-- Weekly: Mondays, 5 minutes after the daily job so the two don't overlap.
select cron.schedule(
  'scheduled-report-weekly',
  '5 5 * * 1',
  $$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name = 'app_base_url')
           || '/api/v1/notifications/internal/reports/weekly-report/trigger',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Internal-Trigger-Secret',
      (select decrypted_secret from vault.decrypted_secrets where name = 'internal_trigger_secret')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 120000
  );
  $$
);

-- Monthly: on the 1st, 10 minutes after the daily job.
select cron.schedule(
  'scheduled-report-monthly',
  '10 5 1 * *',
  $$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name = 'app_base_url')
           || '/api/v1/notifications/internal/reports/monthly-report/trigger',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'X-Internal-Trigger-Secret',
      (select decrypted_secret from vault.decrypted_secrets where name = 'internal_trigger_secret')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 120000
  );
  $$
);

-- Check the jobs exist:
select jobid, jobname, schedule, active from cron.job where jobname like 'scheduled-report-%';

-- After a run: did pg_cron fire, and what did the app answer?
--   select jobid, status, return_message, start_time from cron.job_run_details order by start_time desc limit 10;
--   select id, status_code, timed_out, error_msg, created from net._http_response order by created desc limit 10;
-- (net._http_response rows are kept for only 6 hours.)
