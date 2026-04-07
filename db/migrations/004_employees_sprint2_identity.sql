-- Sprint 2: national_id, education fields, employment_type NOT NULL, uniqueness (D1, D2, D5, D6).
-- Apply after 003. Test on a copy first.
--
-- Duplicate phones/emails/national_ids: section "4b" auto-suffixes duplicates (keeps lowest id).
--
-- If a previous run failed on CREATE UNIQUE INDEX: indexes may be missing; constraints may exist.
--   DROP INDEX IF EXISTS uq_employees_national_id;
--   DROP INDEX IF EXISTS uq_employees_phone;
--   DROP INDEX IF EXISTS uq_employees_email;
-- Then re-run this file (idempotent for ADD COLUMN / most UPDATEs). If ADD CONSTRAINT fails because
-- the constraint already exists, skip those ALTER blocks or drop the constraint by name first.

-- 1. New columns (nullable first)
ALTER TABLE employees ADD COLUMN IF NOT EXISTS national_id TEXT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS university TEXT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS major TEXT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_graduate BOOLEAN;

-- 2. Backfill (unique placeholders per row)
UPDATE employees
SET national_id = COALESCE(national_id, 'UNASSIGNED-' || id::TEXT)
WHERE national_id IS NULL;

UPDATE employees
SET university = COALESCE(university, 'Unassigned')
WHERE university IS NULL;

UPDATE employees
SET major = COALESCE(major, 'Unassigned')
WHERE major IS NULL;

UPDATE employees
SET is_graduate = COALESCE(is_graduate, FALSE)
WHERE is_graduate IS NULL;

-- Distinct placeholder phones for rows missing phone (avoids UNIQUE violation)
UPDATE employees
SET phone = COALESCE(NULLIF(BTRIM(phone), ''), '0000000' || LPAD(id::TEXT, 4, '0'))
WHERE phone IS NULL OR BTRIM(phone) = '';

-- Normalize whitespace on phone / national_id / email (reveals accidental dupes)
UPDATE employees SET phone = BTRIM(phone) WHERE phone IS NOT NULL;
UPDATE employees SET national_id = BTRIM(national_id) WHERE national_id IS NOT NULL;
UPDATE employees SET email = BTRIM(email) WHERE email IS NOT NULL;

UPDATE employees
SET employment_type = COALESCE(employment_type, 'part_time')
WHERE employment_type IS NULL;

-- Non-contract rows must not carry contract_percentage (D5)
UPDATE employees
SET contract_percentage = NULL
WHERE employment_type IN ('full_time', 'part_time');

-- 3. Employment CHECK (drop legacy NULL allowance from 003)
ALTER TABLE employees DROP CONSTRAINT IF EXISTS employees_employment_type_check;
ALTER TABLE employees
    ADD CONSTRAINT employees_employment_type_check CHECK (
        employment_type IN ('full_time', 'part_time', 'contract')
    );

ALTER TABLE employees DROP CONSTRAINT IF EXISTS employees_contract_pct_check;
ALTER TABLE employees
    ADD CONSTRAINT employees_contract_pct_check CHECK (
        (employment_type != 'contract' AND contract_percentage IS NULL)
        OR (employment_type = 'contract')
    );

-- 4. NOT NULL
ALTER TABLE employees ALTER COLUMN national_id SET NOT NULL;
ALTER TABLE employees ALTER COLUMN university SET NOT NULL;
ALTER TABLE employees ALTER COLUMN major SET NOT NULL;
ALTER TABLE employees ALTER COLUMN is_graduate SET NOT NULL;
ALTER TABLE employees ALTER COLUMN employment_type SET NOT NULL;
ALTER TABLE employees ALTER COLUMN phone SET NOT NULL;

-- 4b. Dedupe before UNIQUE indexes (keeps lowest id per value; suffixes others)
-- If you prefer manual merges, fix duplicates in SQL first and comment this block out.
WITH dup AS (
    SELECT id, national_id,
           ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn
    FROM employees
)
UPDATE employees e
SET national_id = e.national_id || '::dup::' || e.id::TEXT
FROM dup d
WHERE e.id = d.id AND d.rn > 1;

WITH dup AS (
    SELECT id, phone,
           ROW_NUMBER() OVER (PARTITION BY phone ORDER BY id) AS rn
    FROM employees
)
UPDATE employees e
SET phone = e.phone || '::id::' || e.id::TEXT
FROM dup d
WHERE e.id = d.id AND d.rn > 1;

WITH dup AS (
    SELECT id, email,
           ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
    FROM employees
    WHERE email IS NOT NULL
)
UPDATE employees e
SET email = e.email || '.dup' || e.id::TEXT
FROM dup d
WHERE e.id = d.id AND d.rn > 1;

-- 5. Uniqueness (national_id, phone, email)
DROP INDEX IF EXISTS uq_employees_national_id;
DROP INDEX IF EXISTS uq_employees_phone;
DROP INDEX IF EXISTS uq_employees_email;

CREATE UNIQUE INDEX uq_employees_national_id ON employees(national_id);
CREATE UNIQUE INDEX uq_employees_phone ON employees(phone);
CREATE UNIQUE INDEX uq_employees_email ON employees(email);
