"""
app/modules/finance/pdf/__init__.py
───────────────────────────────────
PDF generation for finance documents.
"""
from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf, ReceiptPDF

__all__ = ["build_receipt_pdf", "ReceiptPDF"]
