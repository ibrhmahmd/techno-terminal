import os
from datetime import date
from fpdf import FPDF
from dashboard.config import query

class BIReportPDF(FPDF):
    def header(self):
        # Draw a dark blue top banner
        self.set_fill_color(19, 27, 46) # primary_container #131b2e
        self.rect(0, 0, 210, 35, 'F')
        
        # Title text inside banner
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'TECHNO KIDS - OPERATIONAL & FINANCIAL BI REPORT', ln=True, align='L')
        self.set_font('helvetica', '', 9)
        self.cell(0, 5, f'Generated on: {date.today().strftime("%B %d, %Y")} | Source: Supabase Live Database', ln=True, align='L')
        self.ln(15) # whitespace

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Confidential - For Internal Administration Only', align='C')

def generate_bi_pdf() -> bytes:
    # 1. Fetch KPI summary data
    kpi_data = {}
    try:
        df_kpi = query("SELECT * FROM v_bi_kpi_header")
        if not df_kpi.empty:
            kpi_data = df_kpi.iloc[0].to_dict()
    except Exception as e:
        print(f"Error fetching BI KPIs for PDF: {e}")

    # Initialize FPDF
    pdf = BIReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Text color default: dark slate
    pdf.set_text_color(30, 30, 46)
    
    # -------------------------------------------------------------
    # SECTION 1: Key Performance Indicators
    # -------------------------------------------------------------
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 8, '1. Executive KPI Summary', ln=True)
    pdf.ln(2)
    
    # Draw a summary table
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(229, 238, 255) # surface_container #e5eeff
    
    # Headers
    pdf.cell(60, 7, ' Indicator', border=1, fill=True)
    pdf.cell(35, 7, ' Current Value', border=1, fill=True, align='C')
    pdf.cell(60, 7, ' Indicator', border=1, fill=True)
    pdf.cell(35, 7, ' Current Value', border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font('helvetica', '', 9)
    # Row 1
    pdf.cell(60, 6, ' Active Enrolled Students', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("active_students", "N/A")}', border=1, align='C')
    pdf.cell(60, 6, ' Revenue (Current Month)', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("revenue_this_month", 0.0):,.2f} EGP', border=1, align='C')
    pdf.ln()
    
    # Row 2
    pdf.cell(60, 6, ' Waiting List Size', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("waiting_students", "N/A")}', border=1, align='C')
    pdf.cell(60, 6, ' Revenue (All Time)', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("revenue_all_time", 0.0):,.2f} EGP', border=1, align='C')
    pdf.ln()
    
    # Row 3
    pdf.cell(60, 6, ' Active Cohort Groups', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("active_groups", "N/A")}', border=1, align='C')
    pdf.cell(60, 6, ' Total Collection Rate', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("collection_rate_pct", "0.0")}%', border=1, align='C')
    pdf.ln()
    
    # Row 4
    pdf.cell(60, 6, ' Groups Over Capacity', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("groups_over_capacity", 0)}', border=1, align='C')
    pdf.cell(60, 6, ' Avg Lifetime Rev / Student', border=1)
    pdf.cell(35, 6, f' {kpi_data.get("avg_revenue_per_student", 0.0):,.2f} EGP', border=1, align='C')
    pdf.ln()
    
    pdf.ln(10)
    
    # -------------------------------------------------------------
    # SECTION 2: Course & Class Load
    # -------------------------------------------------------------
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 8, '2. Course Performance & Class load', ln=True)
    pdf.ln(2)
    
    # Fetch course performance
    try:
        df_courses = query("SELECT course, category, price_per_level, groups, students, revenue FROM v_bi_course_performance LIMIT 10")
        if not df_courses.empty:
            pdf.set_font('helvetica', 'B', 9)
            pdf.set_fill_color(240, 240, 240)
            
            pdf.cell(50, 6, ' Course Name', border=1, fill=True)
            pdf.cell(35, 6, ' Category', border=1, fill=True)
            pdf.cell(30, 6, ' Price / Level', border=1, fill=True, align='R')
            pdf.cell(20, 6, ' Groups', border=1, fill=True, align='C')
            pdf.cell(20, 6, ' Students', border=1, fill=True, align='C')
            pdf.cell(35, 6, ' Total Collected', border=1, fill=True, align='R')
            pdf.ln()
            
            pdf.set_font('helvetica', '', 8)
            for _, row in df_courses.iterrows():
                pdf.cell(50, 5.5, f' {row["course"]}', border=1)
                pdf.cell(35, 5.5, f' {row["category"] or ""}', border=1)
                pdf.cell(30, 5.5, f'{row["price_per_level"]:,.2f} EGP', border=1, align='R')
                pdf.cell(20, 5.5, f' {row["groups"]}', border=1, align='C')
                pdf.cell(20, 5.5, f' {row["students"]}', border=1, align='C')
                pdf.cell(35, 5.5, f'{row["revenue"]:,.2f} EGP', border=1, align='R')
                pdf.ln()
    except Exception as e:
        pdf.set_font('helvetica', 'I', 9)
        pdf.cell(0, 6, f'Error compiling course details: {e}', ln=True)
        
    pdf.ln(10)
    
    # -------------------------------------------------------------
    # SECTION 3: Monthly Financial Trend
    # -------------------------------------------------------------
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 8, '3. Monthly Revenue Collections Trend', ln=True)
    pdf.ln(2)
    
    try:
        df_rev = query("SELECT month, num_payments, revenue FROM v_bi_monthly_revenue ORDER BY month DESC LIMIT 6")
        if not df_rev.empty:
            pdf.set_font('helvetica', 'B', 9)
            pdf.set_fill_color(240, 240, 240)
            
            pdf.cell(60, 6, ' Billing Month', border=1, fill=True)
            pdf.cell(45, 6, ' Number of Payments', border=1, fill=True, align='C')
            pdf.cell(85, 6, ' Net Revenue Collected', border=1, fill=True, align='R')
            pdf.ln()
            
            pdf.set_font('helvetica', '', 8)
            for _, row in df_rev.iterrows():
                pdf.cell(60, 5.5, f' {row["month"]}', border=1)
                pdf.cell(45, 5.5, f' {row["num_payments"]}', border=1, align='C')
                pdf.cell(85, 5.5, f'{row["revenue"]:,.2f} EGP', border=1, align='R')
                pdf.ln()
    except Exception as e:
        pdf.set_font('helvetica', 'I', 9)
        pdf.cell(0, 6, f'Error compiling revenue trends: {e}', ln=True)

    pdf.ln(10)
    
    # -------------------------------------------------------------
    # SECTION 4: Staffing and Load Insights
    # -------------------------------------------------------------
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 8, '4. Staffing load & Share Allocation', ln=True)
    pdf.ln(2)
    
    try:
        df_staff = query("SELECT full_name, employment_type, active_groups, active_students FROM v_bi_instructor_load LIMIT 10")
        if not df_staff.empty:
            pdf.set_font('helvetica', 'B', 9)
            pdf.set_fill_color(240, 240, 240)
            
            pdf.cell(70, 6, ' Instructor Name', border=1, fill=True)
            pdf.cell(45, 6, ' Employment Type', border=1, fill=True)
            pdf.cell(35, 6, ' Active Classes', border=1, fill=True, align='C')
            pdf.cell(40, 6, ' Active Enrolled students', border=1, fill=True, align='C')
            pdf.ln()
            
            pdf.set_font('helvetica', '', 8)
            for _, row in df_staff.iterrows():
                pdf.cell(70, 5.5, f' {row["full_name"]}', border=1)
                pdf.cell(45, 5.5, f' {row["employment_type"]}', border=1)
                pdf.cell(35, 5.5, f' {row["active_groups"]}', border=1, align='C')
                pdf.cell(40, 5.5, f' {row["active_students"]}', border=1, align='C')
                pdf.ln()
    except Exception as e:
        pdf.set_font('helvetica', 'I', 9)
        pdf.cell(0, 6, f'Error compiling staff loading: {e}', ln=True)

    # Return bytes output
    return bytes(pdf.output())
