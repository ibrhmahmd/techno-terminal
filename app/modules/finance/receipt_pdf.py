import io
import os
from datetime import datetime
from fpdf import FPDF
from app.modules.finance.finance_models import Receipt, Payment
from app.core.config import settings


class ReceiptPDF(FPDF):
    def header(self):
        # Logo
        if settings.pdf_logo_path and os.path.exists(settings.pdf_logo_path):
            try:
                # Add logo at X=10, Y=8, width=33
                self.image(settings.pdf_logo_path, 10, 8, 33)
                self.set_x(45)  # Move cursor past the logo
            except Exception:
                pass

        # Company Name
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, settings.pdf_company_name, border=0, align="L", ln=1)
        
        # Company Address
        if settings.pdf_company_address:
            # Re-align if there's a logo
            if settings.pdf_logo_path and os.path.exists(settings.pdf_logo_path):
                self.set_x(45)
            self.set_font("helvetica", "I", 9)
            self.cell(0, 5, settings.pdf_company_address, border=0, align="L", ln=1)

        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_signature_blocks(self):
        """Adds signature blocks at the bottom of the page."""
        self.ln(15)
        self.set_font("helvetica", "B", 10)
        
        y_pos = self.get_y()
        
        # Primary Signature
        if settings.pdf_primary_signature:
            self.set_xy(15, y_pos)
            self.cell(50, 5, "_" * 30, ln=2, align="C")
            self.cell(50, 5, settings.pdf_primary_signature, align="C")

        # Secondary Signature
        if settings.pdf_secondary_signature:
            self.set_xy(80, y_pos)
            self.cell(50, 5, "_" * 30, ln=2, align="C")
            self.cell(50, 5, settings.pdf_secondary_signature, align="C")


def build_receipt_pdf(
    receipt: Receipt, lines: list[Payment], total: float, parent_name: str
) -> bytes:
    """Generates a PDF receipt using fpdf2 and returns the raw bytes."""
    # Note: A5 format might be a bit narrow for dual signatures, using A4 portrait.
    pdf = ReceiptPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # Meta Info
    pdf.set_font("helvetica", "", 10)
    pdf.cell(50, 6, "Receipt #:", ln=0)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, receipt.receipt_number or "Draft", ln=1)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(50, 6, "Date & Time:", ln=0)
    pdf.set_font("helvetica", "B", 10)
    dt_str = "N/A"
    if receipt.paid_at:
        dt_str = str(receipt.paid_at)[:16]
    pdf.cell(0, 6, dt_str, ln=1)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(50, 6, "Parent / Name:", ln=0)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, parent_name, ln=1)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(50, 6, "Payment Method:", ln=0)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, (receipt.payment_method or "N/A").capitalize(), ln=1)

    pdf.ln(8)

    # Line Items Table Header
    pdf.set_font("helvetica", "B", 9)
    # A4 portrait has about 190mm usable width.
    # Col widths: # 10, Student ID 50, Item 90, Amount 40
    pdf.set_fill_color(230, 230, 240)
    pdf.cell(10, 8, "#", border=1, align="C", fill=True)
    pdf.cell(50, 8, "Student ID", border=1, align="L", fill=True)
    pdf.cell(90, 8, "Item", border=1, align="L", fill=True)
    pdf.cell(40, 8, "Amount", border=1, align="R", fill=True)
    pdf.ln()

    # Line Items Let's assume the names were fetched earlier or we fall back to IDs
    pdf.set_font("helvetica", "", 9)
    for i, line in enumerate(lines, start=1):
        item_text = f"{line.transaction_type.capitalize()} - {str(line.payment_type).replace('_', ' ').capitalize()}"

        pdf.cell(10, 8, str(i), border=1, align="C")
        pdf.cell(50, 8, str(line.student_id), border=1, align="L")
        pdf.cell(90, 8, item_text[:45], border=1, align="L")
        pdf.cell(40, 8, f"{line.amount:g} EGP", border=1, align="R")
        pdf.ln()

    pdf.ln(5)

    # Totals
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(150, 8, "Total Collected:", border=0, align="R")
    pdf.cell(40, 8, f"{total:g} EGP", border=0, align="R")
    pdf.ln()

    # Notes section if any
    if receipt.notes:
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, "Notes / Credit Applications:", ln=1)
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 5, receipt.notes)

    # Add Signatures block
    pdf.add_signature_blocks()

    # Output to byte array
    return bytes(pdf.output())
