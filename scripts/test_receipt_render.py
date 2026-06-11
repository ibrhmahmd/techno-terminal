import os
import sys
from datetime import datetime

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Artifacts dir
artifacts_dir = r"C:\Users\ibrahim\.gemini\antigravity\brain\39eee12e-c566-4002-90aa-5c3ed10abc18"
os.makedirs(artifacts_dir, exist_ok=True)

# 1. Generate PDF
from app.modules.finance.pdf.receipt_pdf import build_receipt_pdf
from app.modules.finance.models.receipt import Receipt
from app.modules.finance.models.payment import Payment

# Mock Data
receipt = Receipt(
    id=101,
    receipt_number="REC-2026-00101",
    paid_at=datetime.now(),
    payer_name="John Doe",
    payment_method="cash",
    received_by=1
)

lines = [
    Payment(
        student_id=1,
        amount=500.0,
        transaction_type="charge",
        payment_type="course_level"
    ),
    Payment(
        student_id=2,
        amount=500.0,
        transaction_type="charge",
        payment_type="course_level",
        discount_amount=50.0
    )
]

pdf_bytes = build_receipt_pdf(
    receipt=receipt,
    lines=lines,
    total=950.0,
    payer_name="John Doe",
    payer_phone="01012345678",
    currency="EGP"
)

pdf_path = os.path.join(artifacts_dir, "test_receipt.pdf")
with open(pdf_path, "wb") as f:
    f.write(pdf_bytes)

print(f"Generated PDF at {pdf_path}")

# 2. Render HTML
html_template = """<html>
<body style="background-color: #f8f9ff; font-family: 'Inter', -apple-system, sans-serif; padding: 20px; color: #0b1c30;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 12px 40px rgba(11,28,48,0.06); border: 1px solid rgba(198,198,205,0.15);">
    <div style="background-color: #131b2e; padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 24px; letter-spacing: -0.02em;">Techno Kids &amp; Techno Future KFS</h1>
    </div>
    <div style="padding: 32px;">
      <h2 style="margin-top: 0; font-size: 20px; font-weight: 600;">Payment Recorded</h2>
      <p style="line-height: 1.6;">Dear John Doe,</p>
      <p style="line-height: 1.6;">This is an administrative confirmation that a payment has been successfully recorded for <strong>Alice Doe</strong>.</p>
      
      <div style="background-color: #eff4ff; border-left: 4px solid #006a61; padding: 16px; border-radius: 4px; margin: 24px 0;">
        <p style="margin: 0 0 12px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Amount</span> <strong style="font-size: 16px; color: #006a61;">950.00 EGP</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Group</span> <strong>Robotics Level 1</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Instructor</span> <strong>Dr. Smith</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Payment Date</span> <strong>2026-06-11</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Method</span> <strong>Cash</strong></p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><span style="color: #64748b; display: inline-block; width: 120px;">Receipt #</span> <strong style="font-family: monospace;">REC-2026-00101</strong></p>
      </div>
      
      <p style="line-height: 1.6; font-size: 14px; font-weight: 600; color: #0b1c30;">Attachment:</p>
      <p style="line-height: 1.6; font-size: 14px;">A detailed PDF receipt is attached to this email for your financial records.</p>
    </div>
    <div style="background-color: #f8f9ff; border-top: 1px solid rgba(198,198,205,0.15); padding: 24px; text-align: center;">
      <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; Techno Kids &amp; Techno Future KFS Administration</p>
    </div>
  </div>
</body>
</html>"""

html_path = os.path.join(artifacts_dir, "test_receipt_email.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated HTML at {html_path}")
