from pydantic import BaseModel


class AcademicsE2ESeedDTO(BaseModel):
    course_ids: list[int]
    group_ids: list[int]
    session_ids: list[int]
    level_ids: list[int]
