# Quickstart: Competition Module Enhancements

## Integration Scenarios

### Scenario 1: Admin manages full competition lifecycle

1. **Create competition**: `POST /api/v1/competitions` with `{name, competition_date, location, fee_per_student}`
2. **Create team with project info**: `POST /api/v1/teams` with `{competition_id, team_name, category, subcategory?, project_name?, project_description?, student_ids, group_id?}`
3. **Add individual member**: `POST /api/v1/teams/{team_id}/members` with `{student_id, fee}`
4. **Remove member** (if unpaid): `DELETE /api/v1/teams/{team_id}/members/{student_id}`
5. **Partial payment**: `POST /api/v1/teams/{team_id}/members/{student_id}/pay` with `{amount, parent_id?}`
6. **Record placement** (after comp date): `PATCH /api/v1/teams/{team_id}/placement` with `{placement_rank, placement_label}`
7. **Delete team** (no paid members): `DELETE /api/v1/teams/{team_id}`
8. **Delete competition** (no teams): `DELETE /api/v1/competitions/{competition_id}`

### Scenario 2: Group as student pre-fill

1. `POST /api/v1/teams` with `group_id` set → service pre-fills `team_name` and `student_ids` from group roster
2. No `GroupCompetitionParticipation` record created (removed)
3. Group is a one-time source, not a continuing link

### Scenario 3: Coach reads own teams

1. Coach authenticates (has employee record linked to `team.coach_id`)
2. `GET /api/v1/teams?competition_id=X` — only returns teams where `coach_id` matches
3. `POST/DELETE` attempts return 403

### Scenario 4: Subcategory filtering

1. `GET /api/v1/teams?competition_id=X&category=Science&subcategory=Physics`
2. Returns only teams matching both filters
3. `GET /api/v1/competitions/{id}/categories` — lists distinct categories with their subcategories

## Key Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/competitions` | any | List competitions |
| POST | `/api/v1/competitions` | admin | Create competition |
| GET | `/api/v1/competitions/{id}` | any | Get competition |
| PUT/PATCH | `/api/v1/competitions/{id}` | admin | Update competition |
| DELETE | `/api/v1/competitions/{id}` | admin | Hard delete (blocked if has teams) |
| GET | `/api/v1/competitions/{id}/summary` | any | Full competition dashboard |
| GET | `/api/v1/competitions/{id}/categories` | any | List categories/subcategories |
| POST | `/api/v1/teams` | admin | Register team with project info |
| GET | `/api/v1/teams` | any | List teams (filter by comp/category/subcategory) |
| GET | `/api/v1/teams/{id}` | any | Get team (with project info) |
| PUT/PATCH | `/api/v1/teams/{id}` | admin | Update team |
| DELETE | `/api/v1/teams/{id}` | admin | Hard delete (blocked if any paid) |
| GET | `/api/v1/teams/{id}/members` | any | List members with fee status |
| POST | `/api/v1/teams/{id}/members` | admin | Add member |
| DELETE | `/api/v1/teams/{id}/members/{sid}` | admin | Remove member (blocked if paid) |
| POST | `/api/v1/teams/{id}/members/{sid}/pay` | admin | Process payment (partial) |
| PATCH | `/api/v1/teams/{id}/placement` | admin | Record placement (after comp date) |
| GET | `/api/v1/students/{sid}/competitions` | any | Student competition history |

**REMOVED endpoints**: `/competitions/{id}/restore`, `/competitions/deleted`, `/teams/{id}/restore`, `/teams/deleted`, all `/academics/groups/{gid}/competitions/*`.

## Test Verification

```bash
# Run competition-specific tests
pytest tests/test_competitions.py -v

# Run full test suite
pytest tests/ -v

# Check for any dead code
grep -n "restore\|deleted_at\|list_deleted\|GroupCompetitionParticipation" app/modules/competitions/ app/api/routers/competitions/
```
