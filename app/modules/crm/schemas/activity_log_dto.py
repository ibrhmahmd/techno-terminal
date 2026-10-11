from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel


class ActivityLogDTO(BaseModel):
    id: int
    student_id: int
    activity_type: str
    activity_subtype: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    description: str
    metadata: Dict[str, Any]
    performed_by: Optional[int]
    performed_by_name: Optional[str]
    created_at: datetime

    model_config = {"frozen": True}
