"""
app/modules/finance/schemas/unpaid_comp_fee_item.py
─────────────────────────────────────────────────────
Unpaid competition fee item schema.
"""
from pydantic import BaseModel


class UnpaidCompFeeItem(BaseModel):
    """
    Output DTO for unpaid competition fee records.
    Used by Financial Desk to render checkbox payment lines.
    """

    team_member_id: int
    team_id: int
    team_name: str
    competition_name: str
    category_name: str
    member_share: float
    student_id: int

    model_config = {"from_attributes": True}
