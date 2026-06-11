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


# Grayscale / B&W Printable Theme (Precision Engine mapping)
class ReceiptColors:
    """Color palette for Precision Engine receipt design in B&W."""
    BACKGROUND = (255, 255, 255)
    HEADER_BG = (255, 255, 255)      # White header for B&W
    ROW_EVEN = (245, 245, 245)       # Light gray
    ROW_ODD = (255, 255, 255)        # White
    TOTALS_BG = (235, 235, 235)      # Soft surface_container gray
    
    # Text
    TEXT_PRIMARY = (0, 0, 0)         # Pure black for contrast
    TEXT_SECONDARY = (80, 80, 80)    # Dark gray
    TEXT_MUTED = (150, 150, 150)     # Muted gray
    
    # Badges/Accents
    BADGE_BG = (220, 220, 220)
    BADGE_TEXT = (40, 40, 40)


class ReceiptPDF(FPDF):
    """
    Custom PDF class for receipt generation with Corporate Light design.
    Clean, modern, English-only layout optimized for business receipts.
    """
    
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.colors = ReceiptColors()
        self.set_auto_page_break(auto=False)  # We handle pagination manually
        
        # Typography Setup
        self.font_h = "helvetica"  # Headings
        self.font_b = "helvetica"  # Body
        
        font_dir = os.path.join("app", "assets", "fonts")
        inter_r = os.path.join(font_dir, "Inter-Regular.ttf")
        inter_b = os.path.join(font_dir, "Inter-Bold.ttf")
        space_r = os.path.join(font_dir, "SpaceGrotesk-Regular.ttf")
        space_b = os.path.join(font_dir, "SpaceGrotesk-Bold.ttf")
        
        if os.path.exists(inter_r) and os.path.exists(space_r):
            self.add_font("Inter", "", inter_r, uni=True)
            self.add_font("Inter", "B", inter_b, uni=True)
            self.add_font("SpaceGrotesk", "", space_r, uni=True)
            self.add_font("SpaceGrotesk", "B", space_b, uni=True)
            self.font_h = "SpaceGrotesk"
            self.font_b = "Inter"
            
        self.set_font(self.font_b, "", 10)
    
    def header(self):
        """PDF header with clean corporate styling."""
        self.set_fill_color(*self.colors.HEADER_BG)
        self.rect(0, 0, self.w, 35, style='F')
        
        if settings.pdf_logo_path and os.path.exists(settings.pdf_logo_path):
            try:
                self.image(settings.pdf_logo_path, self.w - 45, 6, 30)
            except Exception:
                pass
        
        self.set_font(self.font_h, "B", 16)
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.set_xy(10, 12)
        self.cell(0, 6, settings.receipt_company_name, ln=1, align="L")
        
        if settings.receipt_company_address:
            self.set_font(self.font_b, "", 9)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.set_xy(10, 20)
            self.cell(0, 5, settings.receipt_company_address, ln=1, align="L")
        
        self.set_fill_color(*self.colors.BACKGROUND)
        self.set_xy(10, 40)
    
    def add_receipt_meta(self, receipt_number: str, paid_at: Optional[datetime],
                         payer_name: str, payment_method: Optional[str],
                         processed_by: str = "", location: str = "", device: str = "",
                         transaction_ref: str = "", payment_time: str = "", balance_remaining: float = 0.0):
        """Add receipt metadata section with clean labels."""
        self.set_font(self.font_h, "B", 14)
        self.set_text_color(*self.colors.TEXT_PRIMARY)

        self.cell(0, 8, settings.receipt_receipt_label, ln=1, align="C")
        self.ln(2)

        self.set_font(self.font_b, "", 10)
        self.set_text_color(*self.colors.TEXT_SECONDARY)

        self.cell(0, 6, f"Receipt #: {receipt_number or 'Draft'}", ln=1, align="R")
        dt_str = paid_at.strftime("%Y-%m-%d") if paid_at else "N/A"
        time_str = payment_time or (paid_at.strftime("%H:%M") if paid_at else "N/A")
        self.cell(0, 6, f"Date: {dt_str} {time_str}", ln=1, align="R")
        
        if transaction_ref:
            self.cell(0, 6, f"Ref: {transaction_ref}", ln=1, align="R")
            
        self.ln(4)

        # Payer info & Location
        self.set_xy(10, self.get_y())
        self.set_font(self.font_b, "", 10)
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(20, 6, "Payer:", align="L")
        self.set_font(self.font_b, "B", 10)
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.cell(70, 6, payer_name, align="L")

        if location:
            self.set_font(self.font_b, "", 10)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(20, 6, "Location:", align="L")
            self.set_font(self.font_b, "B", 10)
            self.set_text_color(*self.colors.TEXT_PRIMARY)
            self.cell(0, 6, location, align="L", ln=1)
        else:
            self.ln(6)

        # Method & Processed By
        if payment_method:
            self.set_xy(10, self.get_y())
            self.set_font(self.font_b, "", 10)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(20, 6, "Method:", align="L")
            self.set_font(self.font_b, "B", 10)
            self.set_text_color(*self.colors.TEXT_PRIMARY)
            self.cell(70, 6, payment_method.capitalize(), align="L")
            
        if processed_by:
            self.set_font(self.font_b, "", 10)
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(25, 6, "Processed by:", align="L")
            self.set_font(self.font_b, "B", 10)
            self.set_text_color(*self.colors.TEXT_PRIMARY)
            self.cell(0, 6, processed_by, align="L", ln=1)
        else:
            self.ln(6)
            
        if device or balance_remaining > 0:
            self.set_xy(10, self.get_y())
            if device:
                self.set_font(self.font_b, "", 10)
                self.set_text_color(*self.colors.TEXT_SECONDARY)
                self.cell(20, 6, "Device:", align="L")
                self.set_font(self.font_b, "B", 10)
                self.set_text_color(*self.colors.TEXT_PRIMARY)
                self.cell(70, 6, device, align="L")
            else:
                self.cell(90, 6, "", align="L")
                
            if balance_remaining > 0:
                self.set_font(self.font_b, "", 10)
                self.set_text_color(*self.colors.TEXT_SECONDARY)
                self.cell(20, 6, "Balance:", align="L")
                self.set_font(self.font_b, "B", 10)
                self.set_text_color(*self.colors.TEXT_PRIMARY)
                self.cell(0, 6, f"{balance_remaining:,.2f} EGP", align="L", ln=1)
            else:
                self.ln(6)

        self.ln(8)
    
    def add_table_header(self):
        """Add table header with column titles."""
        header_y = self.get_y()
        self.set_fill_color(*self.colors.TOTALS_BG)
        self.rect(10, header_y, self.w - 20, 8, style='F')

        self.set_font(self.font_b, "B", 9)
        self.set_text_color(*self.colors.TEXT_PRIMARY)

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
        row_height = 10 if is_partial else 7

        if row_num % 2 == 0:
            self.set_fill_color(*self.colors.ROW_EVEN)
        else:
            self.set_fill_color(*self.colors.ROW_ODD)
        self.rect(10, row_y, self.w - 20, row_height, style='F')

        self.set_font(self.font_b, "", 9)
        self.set_text_color(*self.colors.TEXT_PRIMARY)

        student_display = student_name[:25] if len(student_name) > 25 else student_name
        course_display = course_group[:30] if len(course_group) > 30 else course_group

        self.set_xy(10, row_y + 2)
        self.cell(10, 5, str(index), align="C")

        self.set_xy(20, row_y + 2)
        self.cell(55, 5, student_display, align="L")

        self.set_xy(75, row_y + 2)
        self.cell(65, 5, course_display, align="L")

        self.set_xy(140, row_y + 2)
        level_text = str(level) if level else "-"
        self.cell(15, 5, level_text, align="C")

        self.set_xy(155, row_y + 2)
        self.set_font(self.font_b, "B", 9)
        amount_text = f"{amount:,.2f} {currency}"
        self.cell(40, 5, amount_text, align="R")

        if is_partial:
            badge_x = 20
            badge_y = row_y + 6
            self.set_fill_color(*self.colors.BADGE_BG)
            self.rect(badge_x, badge_y, 35, 3.5, style='F')
            self.set_xy(badge_x, badge_y)
            self.set_font(self.font_b, "", 7)
            self.set_text_color(*self.colors.BADGE_TEXT)
            remaining_text = f"Partial: {remaining:,.0f}"
            self.cell(35, 3.5, remaining_text, align="C")

        self.ln(row_height)
    
    def add_totals(self, subtotal: float, discount: float, total: float, currency: str = "EGP"):
        """Add totals section with clean tonal block."""
        self.ln(8) # Aggressive whitespace instead of line

        self.set_font(self.font_b, "", 10)

        # Subtotal
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(100, 6, "Subtotal:", align="L")
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.cell(0, 6, f"{subtotal:,.2f} {currency}", align="R", ln=1)

        # Discount (if any)
        if discount > 0:
            self.set_text_color(*self.colors.TEXT_SECONDARY)
            self.cell(100, 6, "Discount:", align="L")
            self.set_text_color(*self.colors.TEXT_PRIMARY)
            self.cell(0, 6, f"-{discount:,.2f} {currency}", align="R", ln=1)

        self.ln(4)

        # Total highlight tonal block
        total_y = self.get_y()
        self.set_fill_color(*self.colors.TOTALS_BG)
        # Full width totals block for differentiation without borders
        self.rect(10, total_y - 1, self.w - 20, 10, style='F')

        self.set_xy(15, total_y + 1.5)
        self.set_font(self.font_h, "B", 11)
        self.set_text_color(*self.colors.TEXT_PRIMARY)
        self.cell(30, 6, "TOTAL PAID:", align="L")
        self.set_xy(self.w - 55, total_y + 1.5)
        self.cell(40, 6, f"{total:,.2f} {currency}", align="R")

        self.ln(12)
    
    def add_notes(self, notes: Optional[str]):
        """Add notes section if present."""
        if not notes:
            return

        self.ln(4)
        self.set_font(self.font_b, "B", 9)
        self.set_text_color(*self.colors.TEXT_SECONDARY)
        self.cell(0, 6, "Notes:", ln=1)

        self.set_font(self.font_b, "", 9)
        self.set_text_color(*self.colors.TEXT_MUTED)
        self.multi_cell(self.w - 20, 5, notes)
        self.ln(4)
    
    def add_signature_section(self):
        """Add signature section with typography hierarchy."""
        self.ln(12)

        self.set_font(self.font_b, "", 9)
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
    currency: str = "EGP",
    processed_by: str = "",
    location: str = "",
    device: str = "",
    transaction_ref: str = "",
    balance_remaining: float = 0.0,
    payment_time: str = ""
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
        payment_method=receipt.payment_method,
        processed_by=processed_by,
        location=location,
        device=device,
        transaction_ref=transaction_ref,
        balance_remaining=balance_remaining,
        payment_time=payment_time
    )

    # Add phone if available
    if payer_phone:
        pdf.set_font(pdf.font_b, "", 10)
        pdf.set_text_color(*pdf.colors.TEXT_SECONDARY)
        pdf.cell(40, 6, "Phone:", align="L")
        pdf.set_font(pdf.font_b, "B", 10)
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
