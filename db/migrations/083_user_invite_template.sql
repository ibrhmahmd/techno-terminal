-- =============================================================================
-- Migration 083: user_invite email template (#148)
--
-- POST /admin/users/invite emails the invitee a registration link
-- ({FRONTEND_BASE_URL}/register?token=...) using this template. Inserted by
-- name when missing; safe to re-run.
-- Ladder: testing project first, then production.
-- =============================================================================

INSERT INTO notification_templates (name, channel, subject, body, variables, is_standard, is_active)
VALUES ('user_invite', 'EMAIL', 'You are invited to Techno Terminal', '<html>
<body style="background-color: #f8f9ff; font-family: ''Inter'', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: ''Space Grotesk'', sans-serif; font-size: 24px;">Techno Kids &amp; Techno Future KFS</h1>
      <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 14px;">Account Invitation</p>
    </div>
    <div style="padding: 32px;">
      <p style="margin-top: 0; font-size: 16px; line-height: 1.5;">You have been invited to Techno Terminal as <strong>{{role}}</strong>.</p>
      <p style="font-size: 14px; line-height: 1.6;">Choose a username and password to activate your account:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{{register_url}}" style="background-color: #006a61; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">Create my account</a>
      </p>
      <p style="font-size: 13px; color: #64748b; line-height: 1.5;">If the button does not work, open this link: <br><span style="word-break: break-all;">{{register_url}}</span></p>
      <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">The invitation expires on <strong>{{expires_at}}</strong>. If you did not expect it, ignore this email.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>', ARRAY['email', 'role', 'register_url', 'expires_at'], True, True)
ON CONFLICT (name) DO NOTHING;
