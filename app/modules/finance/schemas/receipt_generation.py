"""Receipt generation result DTOs (service output, moved from the HTTP schemas)."""
from typing import Optional

from pydantic import BaseModel


class BatchReceiptItem(BaseModel):
    """Item in batch receipt generation response."""
    receipt_id: int
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class BatchGenerateResponse(BaseModel):
    """Response for batch receipt generation."""
    items: list[BatchReceiptItem]
    total_count: int
    success_count: int
    failed_count: int
