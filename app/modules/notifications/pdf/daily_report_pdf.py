"""
app/modules/notifications/pdf/daily_report_pdf.py
─────────────────────────────────────────────────────────────
PDF generation for daily business reports.
"""
from datetime import date
from typing import Dict, Any
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)


def generate_daily_report_pdf(
    date_str: str,
    aggregates: Dict[str, Any]
) -> bytes:
    """
    Generate a PDF daily report.
    
    Args:
        date_str: Report date string
        aggregates: Dictionary containing all daily metrics
        
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
        bottomMargin=2*cm
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )
    
    # Title
    elements.append(Paragraph("Daily Business Report", title_style))
    elements.append(Paragraph(date_str, subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Summary Cards Table
    summary_data = [
        ['Total Revenue', 'New Enrollments'],
        [f"{aggregates['total_revenue']:.2f} EGP", str(aggregates['new_enrollments'])],
        ['', ''],
        ['Sessions Held', 'Absent Students'],
        [str(aggregates['sessions_held']), str(aggregates['absent_count'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[7*cm, 7*cm])
    summary_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#4CAF50')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#2196F3')),
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#FF9800')),
        ('BACKGROUND', (1, 3), (1, 3), colors.HexColor('#9C27B0')),
        
        # Value row styling
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#E8F5E9')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#E3F2FD')),
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#FFF3E0')),
        ('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#F3E5F5')),
        
        # Text styling
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#333333')),
        
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('FONTSIZE', (0, 3), (-1, 3), 12),
        ('FONTSIZE', (0, 4), (-1, 4), 20),
        
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, 1), 20),
        ('TOPPADDING', (0, 3), (-1, 3), 12),
        ('TOPPADDING', (0, 4), (-1, 4), 20),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 20),
        ('BOTTOMPADDING', (0, 3), (-1, 3), 12),
        ('BOTTOMPADDING', (0, 4), (-1, 4), 20),
        
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('BOX', (0, 0), (-1, 1), 2, colors.HexColor('#4CAF50')),
        ('BOX', (0, 3), (-1, 4), 2, colors.HexColor('#FF9800')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    # Additional Metrics Section
    elements.append(Paragraph("Additional Metrics", heading_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Format payment methods for display
    payment_methods_str = ", ".join(
        [f"{method}: {count}" for method, count in aggregates.get("payment_methods", {}).items()]
    ) if aggregates.get("payment_methods") else "N/A"
    
    # Format instructors list
    instructors_str = ", ".join(aggregates.get("instructors_list", [])) if aggregates.get("instructors_list") else "N/A"
    
    # Metrics table
    metrics_data = [
        ['Metric', 'Value'],
        ['Payment Transactions', str(aggregates.get('payment_count', 0))],
        ['Payment Methods', payment_methods_str],
        ['Instructors Today', instructors_str],
        ['Attendance Rate', f"{aggregates.get('attendance_rate', 0):.1%}"],
        ['Unpaid Enrollments', str(aggregates.get('unpaid_count', 0))]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[7*cm, 7*cm])
    metrics_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Body rows
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f9f9f9')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        
        # Unpaid row (highlight)
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3e0')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#E65100')),
        
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('BOX', (0, 0), (-1, 0), 1.5, colors.HexColor('#667eea')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#e0e0e0')),
        
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(metrics_table)
    elements.append(Spacer(1, 1*cm))
    
    # Payment Details Section
    payment_details = aggregates.get('payment_details', [])
    if payment_details:
        elements.append(Paragraph("Payment Details", heading_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Payment details table
        payment_data = [['Student', 'Group', 'Amount', 'Type']]
        for payment in payment_details:
            payment_data.append([
                payment['student_name'],
                payment['group_name'],
                f"{payment['amount']:.2f} EGP",
                payment['payment_type']
            ])
        
        payment_table = Table(payment_data, colWidths=[5*cm, 4*cm, 3*cm, 2*cm])
        payment_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Body rows - alternating colors
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('BOX', (0, 0), (-1, 0), 1.5, colors.HexColor('#2c3e50')),
            
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(payment_table)
        elements.append(Spacer(1, 1*cm))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#999999'),
        alignment=1  # Center
    )
    elements.append(Paragraph("Techno Terminal Automated Report", footer_style))
    elements.append(Paragraph(f"Generated on {date_str}", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
