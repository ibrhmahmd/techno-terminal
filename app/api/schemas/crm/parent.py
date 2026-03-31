"""
app/api/schemas/crm/parent.py
───────────────────────────────
Public-facing (API boundary) Parent DTOs.
"""
from typing import Optional

from pydantic import BaseModel


class ParentPublic(BaseModel):
    """
    Full parent profile returned by GET /crm/parents/{id}.
    """

    id: int
    full_name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ParentListItem(BaseModel):
    """
    Slim representation for paginated list responses.
    """

    id: int
    full_name: str
    phone_primary: str

    model_config = {"from_attributes": True}
