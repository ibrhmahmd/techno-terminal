from typing import Optional

from pydantic import BaseModel


class LogStatusChangeDTO(BaseModel):
    student_id: int
    old_status: str
    new_status: str
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
