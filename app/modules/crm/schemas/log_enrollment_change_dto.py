from typing import Optional

from pydantic import BaseModel


class LogEnrollmentChangeDTO(BaseModel):
    student_id: int
    enrollment_id: int
    action: str
    old_group_id: Optional[int] = None
    new_group_id: Optional[int] = None
    changes_summary: Optional[str] = None
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
