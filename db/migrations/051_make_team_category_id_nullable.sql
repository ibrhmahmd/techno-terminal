-- Migration 051: Make teams.category_id nullable
-- category_id was part of the old competition_categories FK that was dropped
-- in migration 036. The column remains with NOT NULL but no FK constraint,
-- preventing team creation via the 3-table schema which uses teams.category (citext).
-- Since the FK reference table was already dropped, this column can never
-- hold a valid FK value — make it nullable so it doesn't block inserts.

ALTER TABLE teams ALTER COLUMN category_id DROP NOT NULL;