-- =============================================================================
-- Migration 079: Employee Soft Delete
--
-- Adds deleted_at / deleted_by markers and converts the three identity
-- uniqueness constraints to partial unique indexes so a deleted employee's
-- national_id / phone / email become reusable (re-hire) while remaining
-- unique among LIVE employees.
--
-- Constraint names are preserved on the replacement indexes: the
-- IntegrityError mapper in app/modules/hr/services/integrity_error_mapper.py
-- matches on these exact names to produce typed conflict errors.
--
-- uq_employees_user_id is intentionally left untouched: an employee keeps at
-- most one linked account across its full lifecycle (deleted or not).
-- =============================================================================

ALTER TABLE employees ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE employees ADD COLUMN deleted_by INTEGER;

ALTER TABLE employees DROP CONSTRAINT uq_employees_email;
ALTER TABLE employees DROP CONSTRAINT uq_employees_national_id;
ALTER TABLE employees DROP CONSTRAINT uq_employees_phone;

CREATE UNIQUE INDEX uq_employees_email
    ON public.employees USING btree (email)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX uq_employees_national_id
    ON public.employees USING btree (national_id)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX uq_employees_phone
    ON public.employees USING btree (phone)
    WHERE deleted_at IS NULL;

ALTER TABLE employees
    ADD CONSTRAINT fk_employees_deleted_by
    FOREIGN KEY (deleted_by) REFERENCES users(id);
