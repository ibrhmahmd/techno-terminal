from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatusHistoryDTO(BaseModel):
    id: int
    student_id: int
    old_status: Optional[str]
    new_status: str
    changed_at: datetime
    changed_by: Optional[int]
    changed_by_name: Optional[str]
    reason: Optional[str]
    notes: Optional[str]

    model_config = {"frozen": True}
