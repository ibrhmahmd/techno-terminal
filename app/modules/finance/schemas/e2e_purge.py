from pydantic import BaseModel, Field


class E2EPurgeResultDTO(BaseModel):
    prefix: str
    counts: dict[str, int] = Field(default_factory=dict)
