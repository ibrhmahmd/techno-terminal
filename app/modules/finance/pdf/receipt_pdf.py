"""
app/modules/finance/pdf/receipt_pdf.py
───────────────────────────────────────
PDF generation for receipts with Corporate Light design.
Simplified English-only version with clean modern styling.
"""
import os
from typing import List, Optional
from datetime import datetime
from fpdf import FPDF

from app.core.config import settings


# Corporate Light Design System Colors
class ReceiptColors:
    """Color palette for clean corporate receipt design."""
    # Backgrounds
    BACKGROUND = (255, 255, 255)  # #FFFFFF - white
    HEADER_BG = (245, 245, 245)   # #F5F5F5 - light gray
    ROW_EVEN = (250, 250, 250)    # #FAFAFA - very light gray
    ROW_ODD = (255, 255, 255)     # #FFFFFF - white
    
    # Accents
    PRIMARY = (37, 99, 235)       # #2563EB - blue for headers/total
    SECONDARY = (107, 114, 128)    # #6B7280 - gray for secondary text
    TERTIARY = (245, 158, 11)      # #F59E0B - amber/orange for partial badges
    
    # Text
    TEXT_PRIMARY = (31, 41, 55)     # #1F2937 - dark gray
    TEXT_SECONDARY = (75, 85, 99)   # #4B5563 - medium gray
    TEXT_MUTED = (156, 163, 175)    # #9CA3AF - light gray
    BORDER = (229, 231, 235)      # #E5E7EB - border gray


class ReceiptPDF(FPDF):
    """
    Custom PDF class for receipt generation with Corporate Light design.
    Clean, modern, English-only layout optimized for business receipts.
    """
    
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.colors = ReceiptColors()
        self.set_auto_page_break(auto=False)  # We handle pagination manually
        self.set_font("helvetica", "", 10)
    
    def header(self):
        """PDF header with clean corporate styling."""
        # Light gray header band
        self.set_fill_color(*self.colors.HEADER_BG)
        self.rect(0, 0, self.w, 35, style='F')
        
        # Logo on the right
        if settings.pdf_logo_path and os.path.exists(settings.pdf_logo_path):
            try:
                self.image(settings.pdf_logo_path, self.w - 45, 6, 30)
            except Exception:
                pass  # Silently ignore logo errors
        
        # Company Name - left aligned
        self.set_font("helvetica", "B", 14)
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.set_xy(10, 12)
        self.cell(0, 6, settings.receipt_company_name, ln=1, align="L")
        
        # Company address if available
        if settings.receipt_company_address:
            self.set_font("helvetica", "", 9)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.set_xy(10, 20)
            self.cell(0, 5, settings.receipt_company_address, ln=1, align="L")
        
        # Reset to white background for rest of page
        self.set_fill_color(*self.colors.BACKGROUND)
        self.set_xy(10, 40)
    
    def add_receipt_meta(self, receipt_number: str, paid_at: Optional[datetime],
                         payer_name: str, payment_method: Optional[str]):
        """Add receipt metadata section with clean labels."""
        self.set_font("helvetica", "B", 12)
        self.set_text_color(*self.colors.PRIMARY)

        # Receipt title - centered
        self.cell(0, 8, settings.receipt_receipt_label, ln=1, align="C")
        self.ln(2)

        self.set_font("helvetica", "", 10)
        self.set_text_color(*self.colors.TEXT_SECONDARY)

        # Receipt number (right aligned)
        self.cell(0, 6, f"Receipt #: {receipt_number or 'Draft'}", ln=1, align="R")

        # Date (right aligned)
        dt_str = paid_at.strftime("%Y-%m-%d %H:%M") if paid_at else "N/A"
        self.cell(0, 6, f"Date: {dt_str}", ln=1, align="R")
        self.ln(2)

        # Payer info box
        self.set_fill_color(*self.colors.HEADER_BG)
        self.rect(10, self.get_y(), self.w - 20, 12, style='F')
        self.set_xy(12, self.get_y() + 3)
        self.set_font("helvetica", "", 10)
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(20, 6, "Payer:", align="L")
        self.set_font("helvetica", "B", 10)
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.cell(0, 6, payer_name, align="L")

        if payment_method:
            self.set_xy(120, self.get_y())
            self.set_font("helvetica", "", 10)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(25, 6, "Method:", align="L")
            self.set_font("helvetica", "B", 10)
            self.set_text_color(*self.colors.TEXT_PRIMARY)
            self.cell(0, 6, payment_method.capitalize(), align="L")

        self.ln(12)
    
    def add_table_header(self):
        """Add table header with column titles."""
        # Blue header background
        header_y = self.get_y()
        self.set_fill_color(*self.colors.PRIMARY)
        self.rect(10, header_y, self.w - 20, 8, style='F')

        self.set_font("helvetica", "B", 9)
        self.set_text_color(255, 255, 255)  # White text on blue

        # Column headers: # | Student | Course/Group | Level | Amount
        self.set_xy(10, header_y + 2)
        self.cell(10, 5, "#", align="C")
        self.set_xy(20, header_y + 2)
        self.cell(55, 5, "Student", align="L")
        self.set_xy(75, header_y + 2)
        self.cell(65, 5, "Course / Group", align="L")
        self.set_xy(140, header_y + 2)
        self.cell(15, 5, "Lvl", align="C")
        self.set_xy(155, header_y + 2)
        self.cell(40, 5, "Amount", align="R")

        self.ln(10)
    
    def add_table_row(self, index: int, student_name: str, course_group: str,
                      level: Optional[int], amount: float, currency: str = "EGP",
                      is_partial: bool = False, remaining: float = 0.0, row_num: int = 0):
        """Add a table row with alternating background."""
        row_y = self.get_y()
        row_height = 10 if is_partial else 7  # Taller for partial to show remaining

        # Alternating background (light gray/white)
        if row_num % 2 == 0:
            self.set_fill_color(*self.colors.ROW_EVEN)
        else:
            self.set_fill_color(*self.colors.ROW_ODD)
        self.rect(10, row_y, self.w - 20, row_height, style='F')

        self.set_font("helvetica", "", 9)
        self.set_text_color(*self.colors.TEXT_PRIMARY)

        # Truncate long text
        student_display = student_name[:25] if len(student_name) > 25 else student_name
        course_display = course_group[:30] if len(course_group) > 30 else course_group

        # Index
        self.set_xy(10, row_y + 2)
        self.cell(10, 5, str(index), align="C")

        # Student name
        self.set_xy(20, row_y + 2)
        self.cell(55, 5, student_display, align="L")

        # Course/Group
        self.set_xy(75, row_y + 2)
        self.cell(65, 5, course_display, align="L")

        # Level
        self.set_xy(140, row_y + 2)
        level_text = str(level) if level else "-"
        self.cell(15, 5, level_text, align="C")

        # Amount
        self.set_xy(155, row_y + 2)
        self.set_font("helvetica", "B", 9)
        amount_text = f"{amount:,.2f} {currency}"
        self.cell(40, 5, amount_text, align="R")

        # Partial badge (if applicable) - amber/orange color
        if is_partial:
            badge_x = 20
            badge_y = row_y + 6
            self.set_fill_color(*self.colors.TERTIARY)
            self.rect(badge_x, badge_y, 35, 3.5, style='F', round_corners=True, corner_radius=1)
            self.set_xy(badge_x, badge_y)
            self.set_font("helvetica", "", 7)
            self.set_text_color(255, 255, 255)  # White text on amber
            remaining_text = f"Partial: {remaining:,.0f}"
            self.cell(35, 3.5, remaining_text, align="C")

        self.ln(row_height)
    
    def add_totals(self, subtotal: float, discount: float, total: float, currency: str = "EGP"):
        """Add totals section with clean styling."""
        self.ln(4)

        # Separator line
        self.set_draw_color(*self.colors.BORDER)
        self.set_line_width(0.5)
        self.line(self.w - 80, self.get_y(), self.w - 10, self.get_y())
        self.ln(2)

        self.set_font("helvetica", "", 10)

        # Subtotal
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(100, 6, "Subtotal:", align="L")
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.cell(0, 6, f"{subtotal:,.2f} {currency}", align="R", ln=1)

        # Discount (if any)
        if discount > 0:
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(100, 6, "Discount:", align="L")
            self.set_text_color(*self.colors.TERTIARY)  # Amber for discount
            self.cell(0, 6, f"-{discount:,.2f} {currency}", align="R", ln=1)

        self.ln(2)

        # Total highlight bar (blue)
        total_y = self.get_y()
        self.set_fill_color(*self.colors.PRIMARY)
        self.rect(self.w - 80, total_y - 1, 70, 10, style='F', round_corners=True, corner_radius=2)

        self.set_xy(self.w - 75, total_y + 1.5)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(255, 255, 255)  # White text on blue
        self.cell(30, 6, "TOTAL:", align="L")
        self.cell(40, 6, f"{total:,.2f} {currency}", align="R")

        self.ln(12)
    
    def add_notes(self, notes: Optional[str]):
        """Add notes section if present."""
        if not notes:
            return

        self.ln(4)
        self.set_font("helvetica", "B", 9)
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(0, 6, "Notes:", ln=1)

        self.set_font("helvetica", "", 9)
        self.set_text_color(*self.colors.TEXT_MUTED)
        self.multi_cell(self.w - 20, 5, notes)
        self.ln(4)
    
    def add_signature_section(self):
        """Add signature section with clean label."""
        self.ln(8)

        # Center the signature section
        sig_y = self.get_y()
        line_x1 = 65
        line_x2 = 115

        self.set_draw_color(*self.colors.TEXT_MUTED)
        self.set_line_width(0.5)
        self.line(line_x1, sig_y, line_x2, sig_y)

        self.ln(1)

        # Label centered
        self.set_font("helvetica", "", 9)
        self.set_text_color(*self.colors.TEXT_MUTED)
        self.cell(0, 5, settings.receipt_signature_label, align="C", ln=1)

    def footer(self):
        """Footer removed as per requirements."""
        pass  # No footer


def build_receipt_pdf(
    receipt,
    lines: List,
    total: float,
    payer_name: str,
    payer_phone: Optional[str] = None,
    currency: str = "EGP"
) -> bytes:
    """
    Generate a PDF receipt with Corporate Light design.

    Args:
        receipt: Receipt object (Receipt model)
        lines: List of EnhancedReceiptLineDTO or Payment objects
        total: Total amount to display
        payer_name: Payer name for the receipt
        payer_phone: Optional payer phone number
        currency: Currency code (default: EGP)

    Returns:
        PDF file as bytes
    """
    pdf = ReceiptPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # Determine if we're using enhanced DTOs or old Payment objects
    has_enhanced_data = hasattr(lines[0], 'student_name') if lines else False

    # Receipt metadata section
    pdf.add_receipt_meta(
        receipt_number=receipt.receipt_number,
        paid_at=receipt.paid_at,
        payer_name=payer_name,
        payment_method=receipt.payment_method
    )

    # Add phone if available
    if payer_phone:
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*pdf.colors.TEXT_SECONDARY)
        pdf.cell(40, 6, "Phone:", align="L")
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*pdf.colors.TEXT_PRIMARY)
        pdf.cell(0, 6, payer_phone, align="L", ln=1)
        pdf.ln(2)

    # Table section
    pdf.add_table_header()

    # Calculate subtotal and discount
    subtotal = 0.0
    total_discount = 0.0

    for i, line in enumerate(lines, start=1):
        if has_enhanced_data:
            # Using EnhancedReceiptLineDTO
            student_name = line.student_name
            course_group = line.course_group_display
            level = line.level_number
            amount = line.amount
            is_partial = line.is_partial_payment
            remaining = line.remaining_amount
            discount = line.discount_amount
        else:
            # Fallback to Payment objects
            student_name = f"Student #{line.student_id}"
            course_group = f"{line.transaction_type} - {line.payment_type or 'Payment'}"
            level = None
            amount = line.amount
            is_partial = False
            remaining = 0.0
            discount = getattr(line, 'discount_amount', 0.0)

        subtotal += amount
        total_discount += discount

        pdf.add_table_row(
            index=i,
            student_name=student_name,
            course_group=course_group,
            level=level,
            amount=amount,
            currency=currency,
            is_partial=is_partial,
            remaining=remaining,
            row_num=i-1
        )

    # Totals section
    pdf.add_totals(subtotal=subtotal, discount=total_discount, total=total, currency=currency)

    # Notes section
    if hasattr(receipt, 'notes') and receipt.notes:
        pdf.add_notes(receipt.notes)

    # Signature section
    pdf.add_signature_section()

    # Output to bytes
    return bytes(pdf.output())
