-- =============================================================================
-- Migration 082: Task notification templates, keyed by name (#156)
--
-- The task processors look templates up by name (task_assigned,
-- task_status_changed, task_comment_added). Migration 078 inserted them into a
-- `code` column the table no longer has, with a display name in `name`, so the
-- lookup never matched. This inserts the three used templates by name when
-- missing; existing rows are left untouched. task_due_reminder is not used by
-- the code and is not added.
-- Ladder: testing project first, then production.
-- =============================================================================

-- Task assigned to employee
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES (
  'task_assigned',
  'EMAIL',
  'New Task Assigned: {{task_title}}',
  '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">New Task Assigned</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 16px;">Hi <strong>{{employee_name}}</strong>,</p>
      <p style="color: #374151; font-size: 15px; margin: 0 0 24px;">A new task has been assigned to you:</p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 130px; vertical-align: top;">Task</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px; font-weight: 600;">{{task_title}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Priority</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{task_priority}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Due Date</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{due_date}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Assigned by</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{assigned_by_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">Description</td>
            <td style="padding: 8px 0; color: #374151; font-size: 14px; line-height: 1.5;">{{task_description}}</td>
          </tr>
        </table>
      </div>

      <p style="color: #6b7280; font-size: 13px; margin: 0;">Please log in to the Techno Kids portal to manage this task.</p>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>',
  ARRAY['employee_name', 'task_title', 'task_priority', 'due_date', 'assigned_by_name', 'task_description'],
  TRUE,
  TRUE
) ON CONFLICT (name) DO NOTHING;

-- Task status changed
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES (
  'task_status_changed',
  'EMAIL',
  'Task Update: {{task_title}} → {{new_status}}',
  '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">Task Status Updated</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 24px;">The status of a task has changed:</p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 130px;">Task</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px; font-weight: 600;">{{task_title}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Assigned to</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{employee_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Previous Status</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{old_status}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">New Status</td>
            <td style="padding: 8px 0; color: #0ea5e9; font-size: 14px; font-weight: 600;">{{new_status}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Changed by</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{changed_by_name}}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280; font-size: 13px;">Date</td>
            <td style="padding: 8px 0; color: #111827; font-size: 14px;">{{changed_at}}</td>
          </tr>
        </table>
      </div>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>',
  ARRAY['task_title', 'employee_name', 'old_status', 'new_status', 'changed_by_name', 'changed_at'],
  TRUE,
  TRUE
) ON CONFLICT (name) DO NOTHING;

-- Comment added to task
INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES (
  'task_comment_added',
  'EMAIL',
  'New Comment on Task: {{task_title}}',
  '<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0;">
  <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <div style="background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%); padding: 32px 40px;">
      <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700;">New Comment on Your Task</h1>
      <p style="margin: 8px 0 0; color: rgba(255,255,255,0.85); font-size: 14px;">Techno Kids — Task Management</p>
    </div>
    <div style="padding: 32px 40px;">
      <p style="color: #374151; font-size: 15px; margin: 0 0 8px;"><strong>{{author_name}}</strong> commented on <strong>{{task_title}}</strong>:</p>

      <div style="background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px; padding: 16px 20px; margin: 20px 0;">
        <p style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0;">{{comment_content}}</p>
      </div>

      <p style="color: #6b7280; font-size: 13px; margin: 0;">Commented on {{commented_at}}</p>
    </div>
    <div style="background: #f8f9ff; border-top: 1px solid #e5e7eb; padding: 20px 40px; text-align: center;">
      <p style="color: #9ca3af; font-size: 12px; margin: 0;">&copy; Techno Kids Operations</p>
    </div>
  </div>
</body>
</html>',
  ARRAY['task_title', 'author_name', 'comment_content', 'commented_at', 'employee_name'],
  TRUE,
  TRUE
) ON CONFLICT (name) DO NOTHING;
