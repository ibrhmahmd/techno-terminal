-- Allow full_time in addition to part_time and contract on employees.employment_type
-- Apply after 002 (if used). Safe to run on DBs created from schema.sql before this change.

ALTER TABLE employees
    DROP CONSTRAINT IF EXISTS employees_employment_type_check;

ALTER TABLE employees
    ADD CONSTRAINT employees_employment_type_check CHECK (
        employment_type IS NULL
        OR employment_type IN ('full_time', 'part_time', 'contract')
    );
