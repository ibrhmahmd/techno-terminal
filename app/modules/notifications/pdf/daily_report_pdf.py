"""
app/modules/notifications/pdf/daily_report_pdf.py
─────────────────────────────────────────────────────────────
PDF generation for daily business reports.
Refactored to Light Minimalist styling with modern tables.
"""
import os
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)

from app.core.config import settings
from app.modules.notifications.schemas.report_dto import DailyReportAggregateDTO


# --- Theme Colors (Light Minimalist) ---
TEXT_DARK = colors.HexColor('#1E293B')
TEXT_LIGHT = colors.HexColor('#64748B')
HEADER_BG = colors.HexColor('#F8FAFC')
ALT_BG = colors.HexColor('#F1F5F9')
BORDER_COLOR = colors.HexColor('#E2E8F0')
WHITE = colors.white

def format_currency(amount: float) -> str:
    """Format large numbers with commas."""
    return f"{amount:,.2f} EGP"


def generate_daily_report_pdf(
    date_str: str,
    aggregates: DailyReportAggregateDTO
) -> bytes:
    """
    Generate a PDF daily report with a modern minimalist layout.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=TEXT_DARK,
        spaceAfter=5,
        alignment=0  # Left
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=TEXT_LIGHT,
        spaceAfter=30,
        alignment=0  # Left
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=TEXT_DARK,
        spaceAfter=15,
        spaceBefore=20
    )
    
    card_title_style = ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=11, textColor=TEXT_LIGHT, spaceAfter=8)
    card_value_style = ParagraphStyle('CardValue', parent=styles['Normal'], fontSize=18, textColor=TEXT_DARK, fontName='Helvetica-Bold')

    # Header with Logo (Optional)
    header_data = [[
        Paragraph("Daily Business Report", title_style),
        ""  # Placeholder for logo
    ]]
    
    if settings.pdf_logo_path and os.path.exists(settings.pdf_logo_path):
        try:
            # We add the image to the right column
            logo = Image(settings.pdf_logo_path, width=4*cm, height=2*cm, kind='proportional')
            header_data[0][1] = logo
        except Exception:
            pass

    # Wrap the title and subtitle in a table to align with the logo
    title_block = [
        Paragraph("Daily Business Report", title_style),
        Paragraph(f"Date: {date_str}", subtitle_style)
    ]
    header_table = Table([[title_block, header_data[0][1]]], colWidths=[12*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # --- Summary Cards (2x2 Grid) ---
    # We use a 3x3 table with empty rows/cols for spacing
    card_data = [
        [
            [Paragraph("💰 Total Revenue", card_title_style), Paragraph(format_currency(aggregates.total_revenue), card_value_style)],
            "",
            [Paragraph("📈 New Enrollments", card_title_style), Paragraph(str(aggregates.new_enrollments), card_value_style)]
        ],
        ["", "", ""],
        [
            [Paragraph("👨‍🏫 Sessions Held", card_title_style), Paragraph(str(aggregates.sessions_held), card_value_style)],
            "",
            [Paragraph("👥 Present / Absent", card_title_style), Paragraph(f"{aggregates.present_count} / {aggregates.absent_count}", card_value_style)]
        ]
    ]
    
    card_table = Table(card_data, colWidths=[8.5*cm, 1*cm, 8.5*cm], rowHeights=[2.5*cm, 0.5*cm, 2.5*cm])
    card_table.setStyle(TableStyle([
        # Backgrounds for the cards
        ('BACKGROUND', (0, 0), (0, 0), HEADER_BG),
        ('BACKGROUND', (2, 0), (2, 0), HEADER_BG),
        ('BACKGROUND', (0, 2), (0, 2), HEADER_BG),
        ('BACKGROUND', (2, 2), (2, 2), HEADER_BG),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        
        # Subtle Borders around cards
        ('BOX', (0, 0), (0, 0), 0.5, BORDER_COLOR),
        ('BOX', (2, 0), (2, 0), 0.5, BORDER_COLOR),
        ('BOX', (0, 2), (0, 2), 0.5, BORDER_COLOR),
        ('BOX', (2, 2), (2, 2), 0.5, BORDER_COLOR),
    ]))
    elements.append(card_table)
    elements.append(Spacer(1, 1*cm))
    
    # --- Additional Metrics ---
    elements.append(Paragraph("Additional Metrics", heading_style))
    
    payment_methods_str = ", ".join([f"{m}: {c}" for m, c in aggregates.payment_methods.items()]) if aggregates.payment_methods else "N/A"
    instructors_str = ", ".join(aggregates.instructors_list) if aggregates.instructors_list else "N/A"
    
    metrics_data = [
        ['Payment Transactions', str(aggregates.payment_count)],
        ['Payment Methods', payment_methods_str],
        ['Instructors Today', instructors_str],
        ['Attendance Rate', f"{aggregates.attendance_rate:.1%}"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[6*cm, 12*cm])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_LIGHT),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_DARK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),  # Subtle line between rows
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(metrics_table)
    
    # --- Payment Details ---
    if aggregates.payment_details:
        elements.append(Paragraph("Payment Details", heading_style))
        payment_data = [['Student', 'Group', 'Amount', 'Type']]
        
        for idx, payment in enumerate(aggregates.payment_details):
            payment_data.append([
                payment.student_name,
                payment.group_name,
                format_currency(payment.amount),
                payment.payment_type
            ])
            
        payment_table = Table(payment_data, colWidths=[6*cm, 5.5*cm, 4*cm, 2.5*cm])
        
        # Apply zebra striping manually
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_DARK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),  # Header underline
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ]
        
        for i in range(1, len(payment_data)):
            bg = WHITE if i % 2 != 0 else ALT_BG
            style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))
            style_commands.append(('LINEBELOW', (0, i), (-1, i), 0.5, BORDER_COLOR))
            
        payment_table.setStyle(TableStyle(style_commands))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.5*cm))

    # --- Payments by Type Sub-tables ---
    if aggregates.payments_by_type:
        elements.append(Paragraph("Payments by Type", heading_style))

        for ptype_group in aggregates.payments_by_type:
            type_heading = ParagraphStyle(
                'TypeHeading',
                parent=styles['Normal'],
                fontSize=11,
                textColor=TEXT_DARK,
                spaceAfter=6,
                spaceBefore=10,
            )
            elements.append(Paragraph(
                f"<b>{ptype_group.payment_type}</b> &mdash; Subtotal: {format_currency(ptype_group.subtotal)} ({ptype_group.count} payments)",
                type_heading
            ))

            sub_data = [['Student', 'Group', 'Amount']]
            for payment in ptype_group.items:
                sub_data.append([
                    payment.student_name,
                    payment.group_name,
                    format_currency(payment.amount),
                ])

            sub_table = Table(sub_data, colWidths=[7*cm, 6*cm, 5*cm])
            
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_DARK),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
            ]
            
            for i in range(1, len(sub_data)):
                bg = WHITE if i % 2 != 0 else ALT_BG
                style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))
                style_commands.append(('LINEBELOW', (0, i), (-1, i), 0.5, BORDER_COLOR))

            sub_table.setStyle(TableStyle(style_commands))
            elements.append(sub_table)
            elements.append(Spacer(1, 0.3*cm))

    # --- Session Attendance Details ---
    if aggregates.session_details:
        elements.append(Paragraph("Session Attendance", heading_style))
        
        body_style_italic = ParagraphStyle('BodyItalic', parent=styles['Normal'], fontSize=8, textColor=TEXT_LIGHT, fontName='Helvetica-Oblique')
        
        session_data = [['Instructor', 'Time', 'P', 'A', 'C']]
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_DARK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ]
        
        current_row = 1
        group_idx = 0
        for s in aggregates.session_details:
            bg = WHITE if group_idx % 2 == 0 else ALT_BG
            
            # Master Row
            session_data.append([s.instructor_name, s.session_time, str(s.present_count), str(s.absent_count), str(s.cancelled_count)])
            style_commands.append(('BACKGROUND', (0, current_row), (-1, current_row), bg))
            
            master_row_idx = current_row
            current_row += 1
            
            # Sub-row for Absentees
            if s.student_names_absent:
                absent_str = f"Absent: {s.student_names_absent}"
                session_data.append([Paragraph(absent_str, body_style_italic), '', '', '', ''])
                style_commands.append(('SPAN', (0, current_row), (-1, current_row)))
                style_commands.append(('BACKGROUND', (0, current_row), (-1, current_row), bg))
                # Remove padding top for sub-row so it hugs the master row
                style_commands.append(('TOPPADDING', (0, current_row), (-1, current_row), 0))
                # Remove padding bottom for master row
                style_commands.append(('BOTTOMPADDING', (0, master_row_idx), (-1, master_row_idx), 0))
                current_row += 1
            
            # Bottom border for the group
            style_commands.append(('LINEBELOW', (0, current_row - 1), (-1, current_row - 1), 0.5, BORDER_COLOR))
            group_idx += 1
            
        session_table = Table(session_data, colWidths=[6*cm, 6*cm, 2*cm, 2*cm, 2*cm])
        session_table.setStyle(TableStyle(style_commands))
        elements.append(session_table)
        elements.append(Spacer(1, 0.5*cm))

    # --- Instructor Summary Table ---
    if aggregates.instructor_summary:
        elements.append(Paragraph("Instructor Summary", heading_style))

        instr_data = [['Instructor', 'Sessions']]
        for i in aggregates.instructor_summary:
            instr_data.append([i.instructor_name, str(i.session_count)])

        instr_table = Table(instr_data, colWidths=[9*cm, 9*cm])
        
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_DARK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ]
        
        for i in range(1, len(instr_data)):
            bg = WHITE if i % 2 != 0 else ALT_BG
            style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))
            style_commands.append(('LINEBELOW', (0, i), (-1, i), 0.5, BORDER_COLOR))

        instr_table.setStyle(TableStyle(style_commands))
        elements.append(instr_table)
        elements.append(Spacer(1, 0.5*cm))

    # --- Footer ---
    elements.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=TEXT_LIGHT, alignment=1)
    elements.append(Paragraph("Techno Terminal Automated Report", footer_style))
    elements.append(Paragraph(f"Generated on {date_str}", footer_style))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
