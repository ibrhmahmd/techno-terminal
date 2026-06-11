from typing import Optional

from pydantic import BaseModel


class LogEnrollmentDTO(BaseModel):
    student_id: int
    enrollment_id: int
    group_id: int
    group_name: str
    level_number: int
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
