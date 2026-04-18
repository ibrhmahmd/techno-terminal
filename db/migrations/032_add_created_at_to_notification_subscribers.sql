-- Migration 032: Add created_at column to notification_subscribers
-- Created: 2026-04-18
-- Purpose: Add missing created_at column that the application model expects

-- Add created_at column to notification_subscribers table
ALTER TABLE notification_subscribers ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
