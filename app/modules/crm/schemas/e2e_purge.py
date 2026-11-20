from pydantic import BaseModel


class CrmE2ESeedDTO(BaseModel):
    student_ids: list[int]
    parent_ids: list[int]
