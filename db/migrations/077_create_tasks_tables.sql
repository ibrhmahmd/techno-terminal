-- =============================================================================
-- Migration 077 — Create Tasks Tables
-- Date: 2026-07-11
--
-- Creates the tasks, task_subtasks, task_comments, and task_time_logs tables
-- to support internal task tracking for employees.
-- =============================================================================

-- Create custom enum types safely
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'done', 'cancelled', 'overdue');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_recurrence_pattern') THEN
        CREATE TYPE task_recurrence_pattern AS ENUM ('daily', 'weekly', 'monthly', 'custom_interval');
    END IF;
END
$$;

-- Create Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE,
    priority task_priority NOT NULL DEFAULT 'medium',
    status task_status NOT NULL DEFAULT 'todo',
    assigned_to INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    estimated_hours NUMERIC(6, 2),
    tags TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern task_recurrence_pattern,
    recurrence_interval_days INTEGER,
    recurrence_day_of_week INTEGER,
    recurrence_day_of_month INTEGER,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    deleted_by INTEGER REFERENCES users(id) DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tasks performance
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks(id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_deleted ON tasks(deleted_at) WHERE deleted_at IS NOT NULL;

-- Create Task Subtasks table
CREATE TABLE IF NOT EXISTS task_subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_subtasks_task_id ON task_subtasks(task_id);

-- Create Task Comments table
CREATE TABLE IF NOT EXISTS task_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);

-- Create Task Time Logs table
CREATE TABLE IF NOT EXISTS task_time_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    hours NUMERIC(6, 2) NOT NULL CHECK (hours > 0),
    note TEXT,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_time_logs_task_id ON task_time_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_time_logs_employee_id ON task_time_logs(employee_id);
