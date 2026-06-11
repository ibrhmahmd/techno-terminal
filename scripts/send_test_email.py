import os
import sys
import asyncio
from datetime import datetime
from unittest.mock import patch

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.modules.notifications.services.payment_notifications import PaymentNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.db.connection import get_session

async def send_test_email():
    target_email = "ibrahim.ahmd.net@gmail.com"
    print(f"Sending test payment receipt email to {target_email}...")
    
    with get_session() as session:
        repo = NotificationRepository(session)
        service = PaymentNotificationService(repo)
        
        # Fetch a valid receipt
        from app.modules.finance.models.receipt import Receipt
        from app.modules.finance.models.payment import Payment
        from sqlalchemy import select
        
        receipt_row = session.exec(select(Receipt).limit(1)).first()
        receipt = receipt_row[0] if receipt_row else None
        
        if not receipt:
            print("No receipts found in DB. Creating one...")
            receipt = Receipt(receipt_number="CI-RCP-001", paid_at=datetime.now(), payer_name="Test Payer", payment_method="cash", received_by=1)
            session.add(receipt)
            session.commit()
            
        payment_row = session.exec(select(Payment).where(Payment.receipt_id == receipt.id).limit(1)).first()
        payment = payment_row[0] if payment_row else None
        student_id = payment.student_id if payment else 1
        
        receipt_id = receipt.id
        amount = "500.0"
        receipt_number = receipt.receipt_number
        
        # Patch the recipient resolver to ONLY return the requested email
        with patch.object(service, '_resolve_notification_recipients', return_value=[(target_email, 1, "PARENT")]):
            await service._process_received(
                receipt_id=receipt_id, 
                student_id=student_id, 
                amount=amount, 
                receipt_number=receipt_number
            )
            
    print("Test email sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_test_email())
