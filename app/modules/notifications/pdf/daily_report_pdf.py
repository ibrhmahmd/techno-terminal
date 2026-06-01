"""
app/modules/notifications/pdf/daily_report_pdf.py
─────────────────────────────────────────────────────────────
PDF generation for daily business reports.
B&W theme, optimised for 30+ payment rows, printer-friendly.
"""
from datetime import date, datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)

from app.modules.notifications.schemas.report_dto import DailyReportAggregateDTO

# ── Colour palette (B&W) ────────────────────────────────────────────────
HEADER_BG   = colors.HexColor('#333333')
HEADER_FG   = colors.white
GROUP_BG    = colors.HexColor('#e8e8e8')
ROW_EVEN    = colors.HexColor('#f5f5f5')
ROW_ODD     = colors.white
CARD_BG     = colors.HexColor('#f0f0f0')
BORDER      = colors.HexColor('#cccccc')
BORDER_DARK = colors.black
TEXT_BLACK   = colors.black
TEXT_GRAY    = colors.HexColor('#666666')

PAGE_WIDTH = A4[0] - 4 * cm  # usable width with 2cm margins each side


def _alternating_rows(table_style_cmds: list, data_start: int, data_end: int) -> None:
    """Append alternating row background commands to an existing style list."""
    for i in range(data_start, data_end):
        bg = ROW_EVEN if (i - data_start) % 2 == 0 else ROW_ODD
        table_style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))


def _section_rule() -> HRFlowable:
    """Thin horizontal rule to separate report sections."""
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=8)


def generate_daily_report_pdf(
    date_str: str,
    aggregates: DailyReportAggregateDTO
) -> bytes:
    """
    Generate a PDF daily report.

    Args:
        date_str: Report date string
        aggregates: DTO containing all daily metrics

    Returns:
        PDF bytes ready for email attachment
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    elements: list = []
    styles = getSampleStyleSheet()

    # ── Custom styles ────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=22, textColor=TEXT_BLACK, spaceAfter=6, alignment=1,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Normal'],
        fontSize=12, textColor=TEXT_GRAY, spaceAfter=16, alignment=1,
    )
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading2'],
        fontSize=14, textColor=TEXT_BLACK, spaceAfter=4, spaceBefore=12,
    )
    cell_label_style = ParagraphStyle(
        'CellLabel', parent=styles['Normal'],
        fontSize=9, textColor=TEXT_GRAY, alignment=1,
    )
    cell_value_style = ParagraphStyle(
        'CellValue', parent=styles['Normal'],
        fontSize=18, textColor=TEXT_BLACK, alignment=1,
        fontName='Helvetica-Bold',
    )
    wrap_style = ParagraphStyle(
        'WrapSmall', parent=styles['Normal'],
        fontSize=7, leading=9, textColor=TEXT_BLACK, wordWrap='CJK',
    )

    # ── Title ────────────────────────────────────────────────────────────
    elements.append(Paragraph("Daily Business Report", title_style))
    elements.append(Paragraph(date_str, subtitle_style))

    # ── Summary KPI Cards (2×2 grid) ─────────────────────────────────────
    card_data = [
        [
            [Paragraph("Total Revenue", cell_label_style),
             Paragraph(f"{aggregates.total_revenue:,.2f} EGP", cell_value_style)],
            [Paragraph("New Enrollments", cell_label_style),
             Paragraph(str(aggregates.new_enrollments), cell_value_style)],
        ],
        [
            [Paragraph("Sessions Held", cell_label_style),
             Paragraph(str(aggregates.sessions_held), cell_value_style)],
            [Paragraph("Present / Absent", cell_label_style),
             Paragraph(f"{aggregates.present_count} / {aggregates.absent_count}", cell_value_style)],
        ],
    ]

    half = PAGE_WIDTH / 2
    card_table = Table(card_data, colWidths=[half, half], rowHeights=[2.2*cm, 2.2*cm])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX',        (0, 0), (-1, -1), 1, BORDER_DARK),
        ('INNERGRID',  (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    elements.append(card_table)
    elements.append(Spacer(1, 0.6*cm))

    # ── Additional Metrics ───────────────────────────────────────────────
    elements.append(Paragraph("Additional Metrics", heading_style))
    elements.append(_section_rule())

    payment_methods_str = "<br/>".join(
        [f"&bull; {method}: {count}" for method, count in aggregates.payment_methods.items()]
    ) if aggregates.payment_methods else "N/A"
    instructors_str = "<br/>".join([f"&bull; {i}" for i in aggregates.instructors_list]) if aggregates.instructors_list else "N/A"

    # Wrap long text values in Paragraph so they word-wrap inside the cell
    metrics_wrap = ParagraphStyle(
        'MetricsWrap', parent=styles['Normal'],
        fontSize=9, leading=12, textColor=TEXT_BLACK, wordWrap='CJK',
    )

    metrics_data = [
        ['Metric', 'Value'],
        ['Payment Transactions', str(aggregates.payment_count)],
        ['Payment Methods', Paragraph(payment_methods_str, metrics_wrap)],
        ['Instructors Today', Paragraph(instructors_str, metrics_wrap)],
    ]

    metrics_cmds = [
        ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, 0), 10),
        ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
        ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
        ('FONTNAME',       (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',       (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 9),
        ('ALIGN',          (0, 1), (0, -1), 'LEFT'),
        ('ALIGN',          (1, 1), (1, -1), 'RIGHT'),
        ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
        ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
        ('TOPPADDING',     (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
        ('LEFTPADDING',    (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 10),
    ]
    _alternating_rows(metrics_cmds, 1, len(metrics_data))

    metrics_table = Table(metrics_data, colWidths=[half, half], repeatRows=1)
    metrics_table.setStyle(TableStyle(metrics_cmds))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.8*cm))

    # ── Payment Breakdown (merged & grouped) ─────────────────────────────
    payments_by_type = aggregates.payments_by_type
    if payments_by_type:
        elements.append(Paragraph("Payment Breakdown", heading_style))
        elements.append(_section_rule())

        col_widths = [5*cm, 5*cm, PAGE_WIDTH - 10*cm]
        pay_data = [['Student', 'Group', 'Amount']]

        for ptype_group in payments_by_type:
            # Group header row (spans all columns)
            group_label = f"{ptype_group.payment_type}  —  {ptype_group.count} payment{'s' if ptype_group.count != 1 else ''}  —  Subtotal: {ptype_group.subtotal:,.2f} EGP"
            pay_data.append([group_label, '', ''])

            for payment in ptype_group.items:
                pay_data.append([
                    payment.student_name,
                    payment.group_name,
                    f"{payment.amount:,.2f} EGP",
                ])

        # Grand total row
        grand_total = sum(pg.subtotal for pg in payments_by_type)
        pay_data.append([f"Total Revenue: {grand_total:,.2f} EGP", '', ''])

        pay_cmds = [
            # Column header
            ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0), 10),
            ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
            # Body defaults
            ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
            ('FONTSIZE',       (0, 1), (-1, -1), 9),
            ('ALIGN',          (0, 1), (1, -1), 'LEFT'),
            ('ALIGN',          (2, 1), (2, -1), 'RIGHT'),
            ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
            ('TOPPADDING',     (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 7),
            ('LEFTPADDING',    (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ]

        # Style group header rows and data rows
        row_idx = 1
        for ptype_group in payments_by_type:
            # Group header
            pay_cmds.append(('SPAN', (0, row_idx), (-1, row_idx)))
            pay_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), GROUP_BG))
            pay_cmds.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
            pay_cmds.append(('FONTSIZE', (0, row_idx), (-1, row_idx), 9))
            row_idx += 1

            # Data rows with alternating shading
            for i in range(len(ptype_group.items)):
                bg = ROW_EVEN if i % 2 == 0 else ROW_ODD
                pay_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))
                row_idx += 1

        # Grand total row (last row)
        pay_cmds.append(('SPAN', (0, row_idx), (-1, row_idx)))
        pay_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), HEADER_BG))
        pay_cmds.append(('TEXTCOLOR', (0, row_idx), (-1, row_idx), HEADER_FG))
        pay_cmds.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
        pay_cmds.append(('FONTSIZE', (0, row_idx), (-1, row_idx), 11))
        pay_cmds.append(('ALIGN', (0, row_idx), (-1, row_idx), 'CENTER'))

        pay_table = Table(pay_data, colWidths=col_widths, repeatRows=1)
        pay_table.setStyle(TableStyle(pay_cmds))
        elements.append(pay_table)
        elements.append(Spacer(1, 0.8*cm))

    elif aggregates.payment_details:
        # Fallback: flat list if no type grouping available
        elements.append(Paragraph("Payment Details", heading_style))
        elements.append(_section_rule())

        col_widths = [5*cm, 4.5*cm, 3*cm, PAGE_WIDTH - 12.5*cm]
        flat_data = [['Student', 'Group', 'Amount', 'Type']]
        for p in aggregates.payment_details:
            flat_data.append([p.student_name, p.group_name, f"{p.amount:,.2f} EGP", p.payment_type])

        flat_cmds = [
            ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0), 10),
            ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
            ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
            ('FONTSIZE',       (0, 1), (-1, -1), 9),
            ('ALIGN',          (0, 1), (1, -1), 'LEFT'),
            ('ALIGN',          (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN',          (3, 1), (3, -1), 'CENTER'),
            ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
            ('TOPPADDING',     (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 7),
            ('LEFTPADDING',    (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ]
        _alternating_rows(flat_cmds, 1, len(flat_data))
        flat_table = Table(flat_data, colWidths=col_widths, repeatRows=1)
        flat_table.setStyle(TableStyle(flat_cmds))
        elements.append(flat_table)
        elements.append(Spacer(1, 0.8*cm))

    # ── Session Attendance Details ────────────────────────────────────────
    session_details = aggregates.session_details
    if session_details:
        elements.append(Paragraph("Session Attendance Details", heading_style))
        elements.append(_section_rule())

        sess_col_widths = [2.5*cm, 1.8*cm, 0.8*cm, 0.8*cm, 0.8*cm, 5*cm, 5*cm]
        sess_data = [['Instructor', 'Time', 'P', 'A', 'C', 'Students Present', 'Students Absent']]

        for s in session_details:
            present_names = "<br/>".join([f"&bull; {n.strip()}" for n in s.student_names_present.split(",") if n.strip()]) if s.student_names_present else "—"
            absent_names = "<br/>".join([f"&bull; {n.strip()}" for n in s.student_names_absent.split(",") if n.strip()]) if s.student_names_absent else "—"
            
            try:
                # Convert 24h format to 12h format (e.g., "14:30:00" -> "02:30 PM")
                t_format = "%H:%M:%S" if s.session_time and len(s.session_time.split(":")) == 3 else "%H:%M"
                display_time = datetime.strptime(s.session_time, t_format).strftime("%I:%M %p") if s.session_time else "—"
            except (ValueError, TypeError):
                display_time = s.session_time or "—"

            sess_data.append([
                s.instructor_name,
                display_time,
                str(s.present_count),
                str(s.absent_count),
                str(s.cancelled_count),
                Paragraph(present_names, wrap_style),
                Paragraph(absent_names, wrap_style),
            ])

        sess_cmds = [
            ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0), 8),
            ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
            ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
            ('FONTSIZE',       (0, 1), (4, -1), 8),
            ('ALIGN',          (0, 1), (0, -1), 'LEFT'),
            ('ALIGN',          (1, 1), (1, -1), 'CENTER'),
            ('ALIGN',          (2, 1), (4, -1), 'CENTER'),
            ('ALIGN',          (5, 1), (6, -1), 'LEFT'),
            ('VALIGN',         (0, 1), (-1, -1), 'TOP'),
            ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
            ('TOPPADDING',     (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
            ('LEFTPADDING',    (0, 0), (-1, -1), 4),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
        ]
        _alternating_rows(sess_cmds, 1, len(sess_data))

        sess_table = Table(sess_data, colWidths=sess_col_widths, repeatRows=1)
        sess_table.setStyle(TableStyle(sess_cmds))
        elements.append(sess_table)
        elements.append(Spacer(1, 0.6*cm))

    # ── Instructor Summary ───────────────────────────────────────────────
    instructor_summary = aggregates.instructor_summary
    if instructor_summary:
        elements.append(Paragraph("Instructor Summary", heading_style))
        elements.append(_section_rule())

        instr_data = [['Instructor', 'Sessions']]
        for i in instructor_summary:
            instr_data.append([i.instructor_name, str(i.session_count)])

        instr_cmds = [
            ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0), 10),
            ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
            ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
            ('FONTSIZE',       (0, 1), (-1, -1), 9),
            ('ALIGN',          (0, 1), (0, -1), 'LEFT'),
            ('ALIGN',          (1, 1), (1, -1), 'RIGHT'),
            ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
            ('TOPPADDING',     (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
            ('LEFTPADDING',    (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 10),
        ]
        _alternating_rows(instr_cmds, 1, len(instr_data))

        instr_table = Table(instr_data, colWidths=[9*cm, PAGE_WIDTH - 9*cm], repeatRows=1)
        instr_table.setStyle(TableStyle(instr_cmds))
        elements.append(instr_table)
        elements.append(Spacer(1, 0.5*cm))

    # ── Unpaid Students (Session 3) ────────────────────────────────────────
    today_unpaid = aggregates.today_unpaid_attendees
    if today_unpaid:
        elements.append(Paragraph("Unpaid Students (Session 3)", heading_style))
        elements.append(_section_rule())

        unpiad_col_widths = [5*cm, 5*cm, PAGE_WIDTH - 10*cm]
        unpiad_data = [['Student', 'Group', 'Amount']]

        for u in today_unpaid:
            unpiad_data.append([
                u.student_name,
                u.group_name,
                f"{u.amount_owed:,.2f} EGP",
            ])

        unpiad_cmds = [
            ('BACKGROUND',     (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR',      (0, 0), (-1, 0), HEADER_FG),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0), 10),
            ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
            ('TEXTCOLOR',      (0, 1), (-1, -1), TEXT_BLACK),
            ('FONTSIZE',       (0, 1), (-1, -1), 9),
            ('ALIGN',          (0, 1), (1, -1), 'LEFT'),
            ('ALIGN',          (2, 1), (2, -1), 'RIGHT'),
            ('GRID',           (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',            (0, 0), (-1, -1), 1, BORDER_DARK),
            ('TOPPADDING',     (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 7),
            ('LEFTPADDING',    (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ]
        _alternating_rows(unpiad_cmds, 1, len(unpiad_data))
        unpiad_table = Table(unpiad_data, colWidths=unpiad_col_widths, repeatRows=1)
        unpiad_table.setStyle(TableStyle(unpiad_cmds))
        elements.append(unpiad_table)
        elements.append(Spacer(1, 0.5*cm))

    # ── Footer ───────────────────────────────────────────────────────────
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=9, textColor=TEXT_GRAY, alignment=1,
    )
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("Techno Terminal Automated Report", footer_style))
    elements.append(Paragraph(f"Generated on {date_str}", footer_style))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
