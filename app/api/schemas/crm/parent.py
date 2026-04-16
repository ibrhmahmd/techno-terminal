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


class ParentCreate(BaseModel):
    """
    Input for creating a new parent.
    """

    full_name: str
    phone_primary: str
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None


class ParentUpdate(BaseModel):
    """
    Input for updating an existing parent.
    All fields are optional.
    """

    full_name: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    notes: Optional[str] = None
