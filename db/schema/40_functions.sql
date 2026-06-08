-- =============================================================================
-- FUNCTIONS (SYNCED FROM LIVE DB)
-- =============================================================================

-- Function: normalize_team_fields
CREATE OR REPLACE FUNCTION public.normalize_team_fields()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.category := TRIM(NEW.category);
    NEW.subcategory := TRIM(NEW.subcategory);
    RETURN NEW;
END;
$function$;

-- Function: rls_auto_enable
CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$function$;

-- Function: update_waiting_since
CREATE OR REPLACE FUNCTION public.update_waiting_since()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status = 'waiting' THEN
            NEW.waiting_since = CURRENT_TIMESTAMP;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.status = 'waiting' AND (OLD.status IS NULL OR OLD.status != 'waiting') THEN
            NEW.waiting_since = CURRENT_TIMESTAMP;
        ELSIF NEW.status != 'waiting' AND OLD.status = 'waiting' THEN
            NEW.waiting_since = NULL;
            NEW.waiting_priority = NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$function$;

-- Function: tf_set_updated_at
CREATE OR REPLACE FUNCTION public.tf_set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$;

