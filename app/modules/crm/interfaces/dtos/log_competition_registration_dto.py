from typing import Optional

from pydantic import BaseModel


class LogCompetitionRegistrationDTO(BaseModel):
    student_id: int
    competition_id: int
    competition_name: str
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
