from typing import Optional

from pydantic import BaseModel


class LogNoteAddedDTO(BaseModel):
    student_id: int
    note_id: int
    note_type: str
    performed_by: Optional[int] = None

    model_config = {"frozen": True}
