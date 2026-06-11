from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class TimelineFilterDTO(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    activity_types: Optional[List[str]] = None
    performed_by: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    skip: int = 0
    limit: int = 100

    model_config = {"frozen": True}
