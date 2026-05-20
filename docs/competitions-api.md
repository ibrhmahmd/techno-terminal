# Competitions API Documentation

**Base URL**: `/api/v1`
**Auth**: Bearer JWT token in `Authorization` header
**Response Envelope**: All responses wrapped in `{"success": bool, "data": ..., "message": "..."}`

---

## Competitions

### List Competitions
```
GET /competitions
Auth: any
```
**Response**: `CompetitionDTO[]`

### Create Competition
```
POST /competitions
Auth: admin
```
**Body**:
```json
{
  "name": "string (required)",
  "edition_year": 2024,
  "competition_date": "2024-06-01",
  "location": "string",
  "fee_per_student": 0.0,
  "notes": "string"
}
```
**Response**: `CompetitionDTO` (201)

### Get Competition
```
GET /competitions/{id}
Auth: any
```
**Response**: `CompetitionDTO`

### Update Competition
```
PUT|PATCH /competitions/{id}
Auth: admin
```
**Body** (all fields optional):
```json
{
  "name": "string",
  "edition_year": 2024,
  "competition_date": "2024-06-01",
  "location": "string",
  "fee_per_student": 0.0,
  "notes": "string"
}
```
**Response**: `CompetitionDTO`

### Delete Competition
```
DELETE /competitions/{id}
Auth: admin
```
**Response**: `true`
**Errors**: 409 if teams exist

### Get Competition Summary
```
GET /competitions/{id}/summary
Auth: any
```
**Response**:
```json
{
  "competition": "CompetitionDTO",
  "categories": "CategoryWithTeamsDTO[]",
  "total_teams": 0,
  "total_participants": 0
}
```

### List Categories
```
GET /competitions/{id}/categories
Auth: any
```
**Response**:
```json
[
  {"category": "Robotics", "subcategories": ["Sumo", "Line Follower"]}
]
```

---

## Teams

### List Teams
```
GET /teams?competition_id=1&category=&subcategory=&include_members=true
Auth: any (coaches see only their teams)
```
**Query Params**:
- `competition_id` (required)
- `category` (optional)
- `subcategory` (optional)
- `include_members` (default: true)

**Response**: `TeamWithMembersDTO[]` or `TeamDTO[]`

### Register Team
```
POST /teams
Auth: admin
```
**Body**:
```json
{
  "competition_id": 1,
  "team_name": "string (required)",
  "category": "string (required)",
  "subcategory": "string",
  "student_ids": [1, 2, 3],
  "student_fees": {"1": 50.0, "2": 0.0},
  "coach_id": 1,
  "group_id": 1,
  "project_name": "string",
  "project_description": "string",
  "notes": "string"
}
```
**Student resolution**:
- Provide `student_ids` directly, OR
- Provide `group_id` to auto-fill from group's active roster at current level
- Both can be provided — results are merged (union, no duplicates)
- At least one student source is required

**Response**: `TeamRegistrationResultDTO` (201)
**Note**: Duplicate students return warning in `message` field, not error.

### Get Team
```
GET /teams/{id}
Auth: admin or team coach
```
**Response**: `TeamDTO`

### Update Team
```
PUT|PATCH /teams/{id}
Auth: admin
```
**Body** (all fields optional):
```json
{
  "team_name": "string",
  "category": "string",
  "subcategory": "string",
  "project_name": "string",
  "project_description": "string",
  "coach_id": 1,
  "group_id": 1,
  "notes": "string"
}
```
**Response**: `TeamDTO`

### Delete Team
```
DELETE /teams/{id}
Auth: admin
```
**Response**: `true`
**Errors**: 409 if members have paid

---

## Team Members

### List Members
```
GET /teams/{id}/members
Auth: admin or team coach
```
**Response**:
```json
{
  "team_id": 1,
  "team_name": "string",
  "members": [
    {
      "team_member_id": 1,
      "team_id": 1,
      "team_name": "string",
      "student_id": 1,
      "student_name": "string",
      "amount_due": 50.0,
      "amount_paid": 25.0
    }
  ]
}
```

### Add Member
```
POST /teams/{id}/members
Auth: admin
```
**Body**:
```json
{
  "student_id": 1,
  "amount_due": 50.0
}
```
**Response**: `AddTeamMemberResultDTO` (201)

### Remove Member
```
DELETE /teams/{id}/members/{student_id}
Auth: admin
```
**Response**: `true`
**Errors**: 400 if member has paid

### Pay Fee
```
POST /teams/{id}/members/{student_id}/pay
Auth: admin
```
**Body**:
```json
{
  "amount": 25.0,
  "parent_id": 1
}
```
**Response**:
```json
{
  "receipt_number": "REC-2024-001",
  "payment_id": 1,
  "amount": 25.0,
  "amount_paid": 25.0,
  "amount_due": 50.0
}
```
**Note**: Supports partial payments. Atomic transaction.

### Refund Fee
```
POST /teams/{id}/members/{student_id}/refund
Auth: admin
```
**Body**:
```json
{
  "amount": 25.0
}
```
**Response**: `true`
**Errors**: 400 if amount > amount_paid

### Update Placement
```
PATCH /teams/{id}/placement
Auth: admin
```
**Body**:
```json
{
  "placement_rank": 1,
  "placement_label": "Gold"
}
```
**Response**: `TeamDTO`
**Errors**: 409 if competition date is future or >30 days past

---

## Student Competitions

### Get Student's Competitions
```
GET /students/{id}/competitions
Auth: any
```
**Response**:
```json
{
  "student_id": 1,
  "competitions": [
    {
      "membership": "TeamMemberDTO",
      "team": "TeamDTO",
      "category": "Robotics",
      "subcategory": "Sumo",
      "competition": "CompetitionDTO"
    }
  ]
}
```

---

## Data Models

### CompetitionDTO
```json
{
  "id": 1,
  "name": "string",
  "edition_year": 2024,
  "competition_date": "2024-06-01",
  "location": "string",
  "fee_per_student": 0.0,
  "notes": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

### TeamDTO
```json
{
  "id": 1,
  "competition_id": 1,
  "category": "Robotics",
  "subcategory": "Sumo",
  "team_name": "string",
  "coach_id": 1,
  "project_name": "string",
  "project_description": "string",
  "placement_rank": 1,
  "placement_label": "Gold",
  "notes": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

### TeamMemberDTO
```json
{
  "id": 1,
  "team_id": 1,
  "student_id": 1,
  "amount_due": 50.0,
  "amount_paid": 25.0
}
```

### TeamWithMembersDTO
```json
{
  "team": "TeamDTO",
  "members": ["TeamMemberDTO"]
}
```

### CategoryWithTeamsDTO
```json
{
  "category": "Robotics",
  "subcategory": "Sumo",
  "teams": ["TeamWithMembersDTO"]
}
```

---

## Auth Roles

| Role | Access |
|------|--------|
| `admin` | Full read/write |
| `coach` | Read-only for their teams |
| `any` | Read competitions, categories, summaries |

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid input / business rule violation |
| 401 | Missing or invalid JWT |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate, placement window closed, has paid members) |
| 422 | Validation error |
