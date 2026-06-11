from typing import Optional

from pydantic import BaseModel


class LogRegistrationDTO(BaseModel):
    student_id: int
    student_name: str
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
