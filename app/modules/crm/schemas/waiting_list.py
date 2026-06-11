from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WaitingListStudentDTO(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    status: str
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    has_unpaid_balance: bool = False
    waiting_since: Optional[datetime] = None
    waiting_priority: Optional[int] = None
    waiting_notes: Optional[str] = None

    model_config = {"frozen": True}
