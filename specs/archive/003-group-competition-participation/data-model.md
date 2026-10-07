# Data Model: Group Competition Participation Fixes

## Entity Changes

### GroupCompetitionParticipation (table: `group_competition_participation`)

**No schema changes**. Fields remain:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | int (PK) | Auto-generated |
| `group_id` | int (FK → groups) | The participating group |
| `team_id` | int (FK → teams) | The team representing the group |
| `competition_id` | int (FK → competitions) | The competition |
| `entered_at` | datetime | When participation started |
| `left_at` | datetime? | When participation ended (withdrawn/completed) |
| `is_active` | bool | Whether participation is currently active |
| `final_placement` | int? | Placement result after competition ends |
| `notes` | str? | Free-text notes |
| `created_at` | datetime | Audit |
| `updated_at` | datetime | Audit |

**Unique constraint**: `(group_id, team_id, competition_id)`

### Team (table: `teams`)

**No changes**. `group_id` FK already exists on `teams` table.

---

## New Service-Layer DTOs

### GroupCompetitionDTO

```python
class GroupCompetitionDTO(BaseModel):
    """Returned by get_group_competitions(). Replaces list[dict]."""
    participation_id: int
    competition_id: int
    competition_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    team_id: int
    team_name: Optional[str] = None
    entered_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    is_active: bool
    final_placement: Optional[int] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
```

### WithdrawalResultDTO

```python
class WithdrawalResultDTO(BaseModel):
    """Returned by withdraw_from_competition(). Replaces dict."""
    id: int
    status: str  # "withdrawn"
    withdrawn_at: datetime
```

### TeamLinkResultDTO

```python
class TeamLinkResultDTO(BaseModel):
    """Returned by link_existing_team(). Replaces dict."""
    team_id: int
    team_name: str
    group_id: int
```

### ParticipationBriefDTO (analytics)

```python
class ParticipationBriefDTO(BaseModel):
    """Returned by get_group_competition_participations(). Replaces raw tuple."""
    participation: GroupCompetitionParticipation
    competition_name: str
    team_name: str
    category: str
    subcategory: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
```

---

## Service Logic Changes

### register_team() — Auto-create participation

```python
# After team creation and member assignment:
if cmd.group_id is not None:
    from app.shared.datetime_utils import utc_now
    from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
    participation = GroupCompetitionParticipation(
        group_id=cmd.group_id,
        team_id=team.id,
        competition_id=cmd.competition_id,
        entered_at=utc_now(),
        is_active=True,
    )
    db.add(participation)
```

### update_placement() — Sync to participation

```python
# After setting placement_rank on team:
from app.modules.academics.models.group_level_models import GroupCompetitionParticipation
stmt = select(GroupCompetitionParticipation).where(
    GroupCompetitionParticipation.team_id == team_id,
    GroupCompetitionParticipation.is_active == True,
)
active = db.exec(stmt).first()
if active:
    active.final_placement = placement_rank
    db.add(active)
```
