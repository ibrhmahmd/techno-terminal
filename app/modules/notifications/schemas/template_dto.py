from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TemplateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    channel: str
    subject: Optional[str]
    body: str
    variables: list[str]
    is_standard: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class CreateTemplateRequest(BaseModel):
    name: str
    channel: str
    subject: Optional[str] = None
    body: str
    variables: list[str]
    is_standard: bool = False
    
class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    channel: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[list[str]] = None
    is_active: Optional[bool] = None
