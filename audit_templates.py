import sys, re
sys.path.insert(0, '.')
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT name, subject, body FROM notification_templates'))
    rows = result.fetchall()

# Variables passed by each service (ground truth from code)
service_vars = {
    'enrollment_confirmation': {'parent_name','student_name','group_name','course_name','level_number','instructor_name','admin_name','admin_email','schedule','enrollment_id','enrollment_date','date','time'},
    'enrollment_updated': {'parent_name','student_name','group_name','course_name','instructor_name','admin_name','admin_email','changes_summary','enrollment_id','date','time'},
    'enrollment_completed': {'parent_name','student_name','group_name','course_name','instructor_name','admin_name','admin_email','level_number','completion_date','enrollment_id','date','time'},
    'enrollment_dropped': {'parent_name','student_name','group_name','course_name','instructor_name','admin_name','admin_email','reason','enrollment_id','date','time'},
    'enrollment_transferred': {'parent_name','student_name','from_group_name','to_group_name','course_name','instructor_name','admin_name','admin_email','from_enrollment_id','to_enrollment_id','date','time'},
    'level_progression': {'parent_name','student_name','old_level','new_level','group_name','course_name','instructor_name','admin_name','admin_email','enrollment_id','date','time'},
    'payment_receipt': {'parent_name','student_name','amount','receipt_number','receipt_id','group_name','instructor_name','payment_date','payment_method','item_count'},
    'payment_reminder': {'parent_name','student_name','amount_due','due_date'},
    'competition_team_registration': {'parent_name','student_name','team_name','competition_name','category'},
    'competition_fee_payment': {'parent_name','student_name','team_name','competition_name','amount','receipt_number'},
    'competition_placement': {'parent_name','student_name','team_name','competition_name','placement_rank','placement_label','rank_display'},
    'absence_alert': {'parent_name','student_name','session_name','session_date'},
    'daily_report': {'date','session_details','payment_details','instructor_summary','sessions_held','total_revenue','new_enrollments','debtors_section','tomorrow_preview_section'},
    'weekly_report': {'week_start','week_end','total_revenue','attendance_rate','new_students'},
    'monthly_report': {'month','total_revenue','new_enrollments','active_students'},
}

print("=== TEMPLATE AUDIT REPORT ===\n")
for name, subject, body in rows:
    full_text = (subject or '') + (body or '')
    template_vars = set(re.findall(r'\{\{(\w+)\}\}', full_text))
    svc_vars = service_vars.get(name, set())
    
    unused_in_template = svc_vars - template_vars  # service passes but template doesn't use
    missing_in_service = template_vars - svc_vars   # template expects but service doesn't pass
    
    status = "OK" if not unused_in_template and not missing_in_service else "ISSUES"
    
    print(f"[{status}] {name}")
    if not subject:
        print("  BUG: No subject line configured")
    if not body:
        print("  BUG: Empty body!")
    if missing_in_service:
        print(f"  BUG - Template uses vars not provided by service: {sorted(missing_in_service)}")
    if unused_in_template:
        print(f"  INFO - Service passes vars unused by template: {sorted(unused_in_template)}")
    if status == "OK":
        print(f"  All {len(template_vars)} variables matched")
    print()

print("=== MISSING TEMPLATES (in code, not in DB) ===")
db_names = {r[0] for r in rows}
for name in service_vars:
    if name not in db_names:
        print(f"  MISSING: {name}")
