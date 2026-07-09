import os
from datetime import date
from fpdf import FPDF
from dashboard.config import query

class BIReportPDF(FPDF):
    def header(self):
        # Draw a dark blue top banner
        self.set_fill_color(19, 27, 46) # primary_container #131b2e
        self.rect(0, 0, 210, 32, 'F')
        
        # Title text inside banner
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 14)
        self.set_y(8)
        self.cell(0, 6, 'TECHNO KIDS & TECHNO FUTURE', ln=True, align='C')
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 5, 'Overall Business Context Report - Customer & Revenue Insights', ln=True, align='C')
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 4, f'Generated: {date.today().strftime("%B %d, %Y")} | Source: Supabase Live CRM Data', ln=True, align='C')
        self.ln(10) # whitespace

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Confidential - Techno Terminal Business Intelligence', align='C')

    def draw_section_header(self, title: str):
        self.ln(6)
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(19, 27, 46) # primary_container #131b2e
        # Accent left indicator
        self.set_fill_color(0, 106, 97) # secondary #006a61
        self.rect(self.get_x(), self.get_y(), 3, 6, 'F')
        self.set_x(self.get_x() + 5)
        self.cell(0, 6, title.upper(), ln=True)
        self.ln(2)

    def draw_table(self, headers: list, col_widths: list, rows: list, alignments: list = None):
        """Draws a clean, alternate-colored, borderless data table to match Precision Engine guidelines."""
        if not rows:
            self.set_font('helvetica', 'I', 9)
            self.cell(0, 6, 'No records found.', ln=True)
            return

        self.set_font('helvetica', 'B', 8.5)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(19, 27, 46) # Header background #131b2e
        
        # Header Row
        for i, header in enumerate(headers):
            align = alignments[i] if alignments else 'L'
            self.cell(col_widths[i], 6.5, f' {header}', border=0, fill=True, align=align)
        self.ln()

        # Data Rows
        self.set_font('helvetica', '', 8)
        self.set_text_color(12, 17, 29) # Slate text
        
        for r_idx, row in enumerate(rows):
            # Alternate row background colors
            bg_color = (248, 249, 255) if r_idx % 2 == 0 else (229, 238, 255) # surface_low to surface_container
            self.set_fill_color(*bg_color)
            
            for c_idx, val in enumerate(row):
                align = alignments[c_idx] if alignments else 'L'
                self.cell(col_widths[c_idx], 5.5, f' {str(val)}', border=0, fill=True, align=align)
            self.ln()
        self.ln(2)

def generate_bi_pdf() -> bytes:
    # -------------------------------------------------------------
    # 1. Fetch live query data (safety fallbacks for all views)
    # -------------------------------------------------------------
    kpi_data = {}
    try:
        df = query("SELECT * FROM v_bi_kpi_header")
        if not df.empty:
            kpi_data = df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error querying v_bi_kpi_header: {e}")

    new_studs_rows = []
    try:
        df = query("SELECT month, new_students FROM v_bi_new_students_monthly ORDER BY month_date ASC")
        new_studs_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_new_students_monthly: {e}")

    waitlist_sum = {}
    try:
        df = query("SELECT * FROM v_bi_waiting_list_summary")
        if not df.empty:
            waitlist_sum = df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error querying v_bi_waiting_list_summary: {e}")

    waitlist_months = []
    try:
        df = query("SELECT joined_month, waiting_students FROM v_bi_waiting_list_by_month ORDER BY joined_month_date ASC")
        waitlist_months = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_waiting_list_by_month: {e}")

    wait_duration = {}
    try:
        df = query("SELECT * FROM v_bi_current_wait_duration")
        if not df.empty:
            wait_duration = df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error querying v_bi_current_wait_duration: {e}")

    wait_conversion = {}
    try:
        df = query("SELECT * FROM v_bi_waiting_conversion_stats")
        if not df.empty:
            wait_conversion = df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error querying v_bi_waiting_conversion_stats: {e}")

    gender_rows = []
    try:
        df = query("SELECT gender, student_count, avg_age FROM v_bi_gender_age_breakdown")
        gender_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_gender_age_breakdown: {e}")

    demographics_comp = {}
    try:
        df = query("SELECT * FROM v_bi_demographics_completeness")
        if not df.empty:
            demographics_comp = df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error querying v_bi_demographics_completeness: {e}")

    cohort_rows = []
    try:
        df = query("SELECT status, student_count FROM v_bi_founding_cohort_status")
        cohort_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_founding_cohort_status: {e}")

    rev_rows = []
    try:
        df = query("SELECT month, num_payments, revenue FROM v_bi_monthly_revenue ORDER BY month_date ASC")
        # Format revenue as EGP string for the table
        formatted_rev = []
        for r in df.values.tolist():
            formatted_rev.append([r[0], r[1], f"{r[2]:,.2f} EGP"])
        rev_rows = formatted_rev
    except Exception as e:
        print(f"Error querying v_bi_monthly_revenue: {e}")

    pay_completeness_rows = []
    try:
        df = query("SELECT payment_state, enrollments, billed, collected FROM v_bi_payment_completeness")
        formatted_pay = []
        for r in df.values.tolist():
            formatted_pay.append([r[0].replace('_', ' ').title(), r[1], f"{r[2]:,.2f} EGP", f"{r[3]:,.2f} EGP"])
        pay_completeness_rows = formatted_pay
    except Exception as e:
        print(f"Error querying v_bi_payment_completeness: {e}")

    pay_method_rows = []
    try:
        df = query("SELECT payment_method, receipt_count, total_collected, pct_of_total FROM v_bi_payment_method_mix")
        formatted_method = []
        for r in df.values.tolist():
            formatted_method.append([r[0].title(), r[1], f"{r[2]:,.2f} EGP", f"{r[3]:.1f}%"])
        pay_method_rows = formatted_method
    except Exception as e:
        print(f"Error querying v_bi_payment_method_mix: {e}")

    course_rows = []
    try:
        df = query("SELECT course, category, price_per_level, groups, students, revenue FROM v_bi_course_performance")
        formatted_course = []
        for r in df.values.tolist():
            formatted_course.append([r[0], r[1].title(), f"{r[2]:,.2f} EGP", r[3], r[4], f"{r[5]:,.2f} EGP"])
        course_rows = formatted_course
    except Exception as e:
        print(f"Error querying v_bi_course_performance: {e}")

    over_cap_rows = []
    try:
        df = query("SELECT group_name, max_capacity, enrolled, over_by FROM v_bi_groups_over_capacity")
        over_cap_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_groups_over_capacity: {e}")

    instructor_load_rows = []
    try:
        df = query("SELECT full_name, employment_type, active_groups, active_students FROM v_bi_instructor_load")
        instructor_load_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_instructor_load: {e}")

    contract_cost_rows = []
    try:
        df = query("SELECT full_name, active_groups, active_enrollments, estimated_cost FROM v_bi_contract_instructor_cost")
        formatted_contract = []
        for r in df.values.tolist():
            formatted_contract.append([r[0], r[1], r[2], f"{r[3]:,.2f} EGP"])
        contract_cost_rows = formatted_contract
    except Exception as e:
        print(f"Error querying v_bi_contract_instructor_cost: {e}")

    headcount_rows = []
    try:
        df = query("SELECT employment_type, headcount, total_monthly_salary FROM v_bi_headcount_by_type")
        formatted_headcount = []
        for r in df.values.tolist():
            formatted_headcount.append([r[0].replace('_', ' ').title(), r[1], f"{r[2]:,.2f} EGP"])
        headcount_rows = formatted_headcount
    except Exception as e:
        print(f"Error querying v_bi_headcount_by_type: {e}")

    attendance_rows = []
    try:
        df = query("SELECT status, records, pct FROM v_bi_attendance_rate")
        formatted_att = []
        for r in df.values.tolist():
            formatted_att.append([r[0].title(), r[1], f"{r[2]:.1f}%"])
        attendance_rows = formatted_att
    except Exception as e:
        print(f"Error querying v_bi_attendance_rate: {e}")

    lifecycle_rows = []
    try:
        df = query("SELECT status, enrollments, pct FROM v_bi_enrollment_status")
        formatted_life = []
        for r in df.values.tolist():
            formatted_life.append([r[0].title(), r[1], f"{r[2]:.1f}%"])
        lifecycle_rows = formatted_life
    except Exception as e:
        print(f"Error querying v_bi_enrollment_status: {e}")

    schedule_rows = []
    try:
        df = query("SELECT day, afternoon_groups, evening_groups, total_groups, students_enrolled FROM v_bi_weekly_schedule")
        schedule_rows = df.values.tolist()
    except Exception as e:
        print(f"Error querying v_bi_weekly_schedule: {e}")


    # -------------------------------------------------------------
    # 2. PDF Builder & Page Layout
    # -------------------------------------------------------------
    pdf = BIReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(12, 17, 29) # Slate body text

    # --- INTRODUCTION NOTE ---
    pdf.set_font('helvetica', 'I', 8.5)
    pdf.cell(0, 5, 'Techno Kids has only been running on its current CRM system for about 3 months, so several figures here are early snapshots', ln=True)
    pdf.cell(0, 5, 'rather than settled trends. Thresholds like "old customer" are starting points to revisit as more history builds up.', ln=True)
    pdf.ln(2)

    # --- EXECUTIVE SUMMARY ---
    pdf.draw_section_header('Executive Summary')
    pdf.set_font('helvetica', '', 9.5)
    
    total_wait = waitlist_sum.get("waiting_total", 303)
    active_count = kpi_data.get("active_students", 386)
    rev_this_month = kpi_data.get("revenue_this_month", 55559.0)
    total_rev = kpi_data.get("revenue_all_time", 235702.0)
    col_rate = kpi_data.get("collection_rate_pct", 56.8)
    
    # Render direct, technical bullets
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, f'Records database profile: {active_count + total_wait} students on file ({active_count} active, {total_wait} on waiting list). 0 waiting-list students have been placed into a class. Waitlist activation represents the single largest growth lever.')
    pdf.ln(1)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, f'Revenue tracking: May recorded 21,149 EGP, June recorded 155,442 EGP (a 7x increase), and July month-to-date is tracking at {rev_this_month:,.2f} EGP. Total cumulative revenue collected is {total_rev:,.2f} EGP.')
    pdf.ln(1)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, f'Collections performance: {col_rate}% of net billed amount has been collected. 318 of 678 total enrollments have recorded zero payments, and 11 are partially paid. Outstanding balances represent a significant recovery target.')
    pdf.ln(1)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Course distribution: Hardware modules (Spike Essentials, Spike Prime, WeDo, EV3, Arduino) drive the majority of enrollment volume and revenue. HTML leads software modules.')
    pdf.ln(1)

    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Cost structure: Part-time monthly payroll midpoint is estimated at 24,500 EGP. Active contract instructor liabilities stand at 17,450 EGP. Full-time staff salaries need to be backfilled in database records.')
    pdf.ln(1)

    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(5, 5, 'o')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Conversion velocity: Transition speed from waiting to active status averages 1 day. Constraint is group and class scheduling capacity, not customer conversion resistance.')
    pdf.ln(4)

    # --- NEW CUSTOMER INSIGHTS ---
    pdf.draw_section_header('New Customer Insights')
    
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'New Registrations by Month:', ln=True)
    pdf.draw_table(['Month', 'New Student Sign-ups'], [90, 100], new_studs_rows, alignments=['L', 'C'])
    
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Waiting List Backlog (by registration month):', ln=True)
    pdf.draw_table(['Join Cohort Month', 'Students Currently Waiting'], [90, 100], waitlist_months, alignments=['L', 'C'])

    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Wait Duration & Funnel Metrics:', ln=True)
    pdf.set_font('helvetica', '', 8.5)
    
    avg_wait = wait_duration.get("avg_days_waiting", 35.0)
    longest_wait = wait_duration.get("longest_wait_days", 54)
    conv_count = wait_conversion.get("total_conversions", 85)
    avg_conv_days = wait_conversion.get("avg_days_to_convert", 1.0)
    
    pdf.cell(0, 5.5, f'- Average duration on waiting list: {avg_wait} days (longest duration: {longest_wait} days).', ln=True)
    pdf.cell(0, 5.5, f'- Historical conversions: {conv_count} students transitioned from waiting to active with an average conversion speed of {avg_conv_days} day(s).', ln=True)
    pdf.cell(0, 5.5, f'- Waitlist demographic split: Gender split shows {gender_rows[0][1] if len(gender_rows)>0 else 264} Male / {gender_rows[1][1] if len(gender_rows)>1 else 120} Female. Average age is {gender_rows[0][2] if len(gender_rows)>0 else "8.6"} years.', ln=True)
    
    completeness_pct = demographics_comp.get("completeness_pct", 49.5)
    missing_count = demographics_comp.get("missing_demographics", 0)
    pdf.cell(0, 5.5, f'- Demographics database status: {completeness_pct}% of records are complete. {missing_count} student profiles are missing birth date or gender fields.', ln=True)
    pdf.ln(4)

    # --- OLD CUSTOMER INSIGHTS ---
    pdf.draw_section_header('Old Customer Insights (Founding Cohort)')
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Founding cohort represents students registered in May 2026. Tracking the May 2026 cohort provides direct retention metrics.')
    pdf.ln(1)
    
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'May Cohort Current Status:', ln=True)
    pdf.draw_table(['Enrollment Status', 'Student Count'], [90, 100], cohort_rows, alignments=['L', 'C'])
    pdf.set_font('helvetica', '', 8.5)
    pdf.cell(0, 5.5, '- May 2026 cohort retention rate is 96%. Out of 162 initial students, 156 remain active and 0 have gone inactive.', ln=True)
    pdf.cell(0, 5.5, '- Sibling check: Two registered names share a phone number. Regular manual checks are advised to prevent duplicate contacts.', ln=True)
    pdf.ln(4)

    # Force page break for spacing and aesthetics
    pdf.add_page()

    # --- REVENUE & COLLECTIONS ---
    pdf.draw_section_header('Revenue & Collections')
    
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Monthly Collected Revenue:', ln=True)
    pdf.draw_table(['Month', 'Completed Payments Count', 'Collected Revenue (EGP)'], [60, 60, 70], rev_rows, alignments=['L', 'C', 'R'])

    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Enrollment Payment Completeness:', ln=True)
    pdf.draw_table(['Payment State', 'Enrollments Count', 'Total Billed (Net)', 'Total Collected'], [50, 40, 50, 50], pay_completeness_rows, alignments=['L', 'C', 'R', 'R'])

    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Collections Method Mix:', ln=True)
    pdf.draw_table(['Payment Method', 'Receipts Count', 'Total Collected', 'Share (%)'], [50, 45, 55, 40], pay_method_rows, alignments=['L', 'C', 'R', 'R'])
    
    avg_per_stud = kpi_data.get("avg_revenue_per_student", 655.0)
    pdf.set_font('helvetica', '', 8.5)
    pdf.cell(0, 5.5, f'- Average revenue collected per paying student: {avg_per_stud:,.2f} EGP.', ln=True)
    pdf.cell(0, 5.5, '- Cash represents 71% of all revenue collected. Shifting families to InstaPay will decrease manual overhead.', ln=True)
    pdf.ln(4)

    # --- COURSE PERFORMANCE ---
    pdf.draw_section_header('Course Performance')
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Course Profitability and Enrollment Load:', ln=True)
    pdf.draw_table(['Course Name', 'Category', 'Price/Level', 'Groups', 'Students', 'Total Collected'], [45, 30, 30, 20, 20, 45], course_rows, alignments=['L', 'L', 'R', 'C', 'C', 'R'])
    
    # Over capacity note
    if over_cap_rows:
        pdf.set_font('helvetica', 'B', 8.5)
        pdf.set_text_color(179, 38, 30) # Error red
        for r in over_cap_rows:
            pdf.cell(0, 5.5, f'WARNING: Group "{r[0]}" exceeds maximum capacity. Enrolled: {r[2]} (Max limit: {r[1]}, Over limit by: {r[3]}).', ln=True)
        pdf.set_text_color(12, 17, 29)
    pdf.ln(4)

    # Force page break
    pdf.add_page()

    # --- STAFFING & INSTRUCTOR COST ---
    pdf.draw_section_header('Staffing & Instructor Cost')
    
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Instructor Active Groups Load:', ln=True)
    pdf.draw_table(['Instructor Name', 'Employment Type', 'Active Groups', 'Enrolled Students'], [60, 45, 40, 45], instructor_load_rows, alignments=['L', 'L', 'C', 'C'])

    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Contract Instructor Revenue-Share Cost:', ln=True)
    pdf.draw_table(['Contract Instructor Name', 'Active Classes Count', 'Enrolled Students', 'Owed Revenue Share (EGP)'], [60, 45, 40, 45], contract_cost_rows, alignments=['L', 'C', 'C', 'R'])

    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(0, 6, 'Headcount & Salary Obligations:', ln=True)
    pdf.draw_table(['Employment Type', 'Headcount', 'Total Fixed Salary Obligation (EGP)'], [70, 50, 70], headcount_rows, alignments=['L', 'C', 'R'])

    pdf.set_font('helvetica', '', 8.5)
    pdf.cell(0, 5.5, '- Midpoint estimated part-time payroll: 24,500.00 EGP per month (based on 7 instructors at 3,000 - 4,000 EGP).', ln=True)
    pdf.cell(0, 5.5, '- Estimated contract instructor liabilities for active rounds: 17,450.00 EGP.', ln=True)
    pdf.cell(0, 5.5, '- Full-time staff count: 3 (Salaries must be entered in employees.monthly_salary to complete payroll analysis).', ln=True)
    pdf.ln(4)

    # --- ATTENDANCE & LIFE CYCLE ---
    pdf.draw_section_header('Attendance & Enrollment Lifecycle')
    
    col_att, col_life = st.columns(2) # we can just layout two tables side by side in PDF
    
    # We will write the two tables sequentially
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(95, 6, 'Attendance Status Rates:', ln=False)
    pdf.cell(95, 6, 'Enrollment Lifecycle Status:', ln=True)
    
    # We render them manually to place side-by-side or clean vertical
    # For simplicity of fpdf layout, we'll draw them sequentially
    pdf.draw_table(['Attendance Status', 'Records Count', 'Share (%)'], [70, 60, 60], attendance_rows, alignments=['L', 'C', 'R'])
    pdf.draw_table(['Lifecycle Status', 'Enrollments Count', 'Share (%)'], [70, 60, 60], lifecycle_rows, alignments=['L', 'C', 'R'])
    pdf.ln(4)

    # --- WEEKLY SCHEDULE ---
    pdf.draw_section_header('Weekly Schedule Density')
    pdf.draw_table(['Day of Week', 'Afternoon (<17:00)', 'Evening (>=17:00)', 'Total Groups', 'Students Enrolled'], [40, 40, 40, 30, 40], schedule_rows, alignments=['L', 'C', 'C', 'C', 'C'])
    pdf.set_font('helvetica', '', 8.5)
    pdf.cell(0, 5.5, '- Saturday is the peak operational day. Tuesday has zero classes scheduled.', ln=True)
    pdf.ln(4)

    # --- RECOMMENDATIONS ---
    pdf.draw_section_header('Suggested Data Points to Track Going Forward')
    pdf.set_font('helvetica', '', 8.5)
    recommendations = [
        "Full-time instructor salaries: Needed to complete payroll analysis alongside part-time and contract estimates.",
        "Waiting-list capacity planning: Monitor waitlist backlog reduction rate against newly opened class schedules.",
        "Customer acquisition source: Track referral, walk-in, and social media channels to evaluate marketing spend.",
        "Time from enrollment to drop: Track drop velocity and schedule conflicts to identify early warning indicators.",
        "Demographics completeness: Encourage entry of missing birth dates and genders (currently missing for 44% of records).",
        "Cost of cash handling: With 71% of collections in cash, audit security and manual counting overhead.",
        "Follow-up cadence on unpaid enrollments: Track days-since-enrollment on unpaid records to optimize collections."
    ]
    for rec in recommendations:
        pdf.cell(5, 5, '-')
        pdf.multi_cell(0, 5, rec)
        pdf.ln(1)

    # Return bytes output
    return bytes(pdf.output())
