import io
from datetime import datetime
from fpdf import FPDF
from app.modules.finance.finance_models import Receipt, Payment


class ReceiptPDF(FPDF):
    def header(self):
        # Logo / Title
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Techno Future CRM", border=0, align="L", ln=1)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def build_receipt_pdf(receipt: Receipt, lines: list[Payment], total: float, parent_name: str) -> bytes:
    """Generates a PDF receipt using fpdf2 and returns the raw bytes."""
    pdf = ReceiptPDF(orientation="P", unit="mm", format="A5")
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
        # Avoid complex formatting if paid_at is a string vs datetime
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
    # Col widths: Student 40, Type/For 50, Amount 30
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(10, 8, "#", border=1, align="C", fill=True)
    pdf.cell(40, 8, "Student ID", border=1, align="L", fill=True)
    pdf.cell(50, 8, "Item", border=1, align="L", fill=True)
    pdf.cell(30, 8, "Amount", border=1, align="R", fill=True)
    pdf.ln()

    # Line Items Let's assume the names were fetched earlier or we fall back to IDs
    pdf.set_font("helvetica", "", 9)
    for i, line in enumerate(lines, start=1):
        item_text = f"{line.transaction_type.capitalize()} - {str(line.payment_type).replace('_', ' ').capitalize()}"
        
        pdf.cell(10, 8, str(i), border=1, align="C")
        pdf.cell(40, 8, str(line.student_id), border=1, align="L")
        pdf.cell(50, 8, item_text, border=1, align="L")
        pdf.cell(30, 8, f"{line.amount:g} EGP", border=1, align="R")
        pdf.ln()

    pdf.ln(5)

    # Totals
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(100, 8, "Total Collected:", border=0, align="R")
    pdf.cell(30, 8, f"{total:g} EGP", border=0, align="R")
    pdf.ln()

    # Notes section if any
    if receipt.notes:
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, "Notes / Credit Applications:", ln=1)
        pdf.set_font("helvetica", "", 9)
        pdf.multi_cell(0, 5, receipt.notes)

    # Output to byte array
    return bytes(pdf.output())
