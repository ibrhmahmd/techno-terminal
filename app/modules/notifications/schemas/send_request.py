from typing import Dict, Any, List
from pydantic import BaseModel

class SendAbsenceRequest(BaseModel):
    student_id: int
    session_name: str
    session_date: str

class SendBulkRequest(BaseModel):
    parent_ids: List[int]
    template_name: str
    extra_vars: Dict[str, Any] = {}

class AddSubscriberRequest(BaseModel):
    employee_id: int
    report_type: str
    channel: str
