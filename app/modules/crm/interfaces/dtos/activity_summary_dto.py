from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel


class ActivitySummaryDTO(BaseModel):
    student_id: int
    total_activities: int
    activities_by_type: Dict[str, int]
    first_activity_date: Optional[datetime]
    last_activity_date: Optional[datetime]

    model_config = {"frozen": True}
