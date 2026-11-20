from pydantic import BaseModel


class CompetitionsE2ESeedDTO(BaseModel):
    competition_ids: list[int]
    team_ids: list[int]
    team_member_ids: list[int]
