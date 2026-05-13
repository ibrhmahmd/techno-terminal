# Schemas

## CompetitionDTO
```json
{
  "id": 1,
  "name": "National Robotics Championship",
  "edition": "2026",
  "edition_year": 2026,
  "competition_date": "2026-05-15",
  "location": "Cairo",
  "notes": "Annual competition",
  "fee_per_student": 500.0,
  "created_at": "2026-04-01T10:00:00"
}
```

## CreateCompetitionInput
| Field | Type | Required |
|-------|------|----------|
| name | string | Yes |
| edition | string | No |
| competition_date | date (YYYY-MM-DD) | No |
| location | string | No |
| notes | string | No |
| fee_per_student | number | No (default: 0) |

## UpdateCompetitionInput
All fields optional. Partial updates supported.

| Field | Type |
|-------|------|
| name | string |
| edition | string |
| edition_year | int |
| competition_date | date |
| location | string |
| fee_per_student | number |
| notes | string |

## TeamDTO
```json
{
  "id": 1,
  "competition_id": 1,
  "team_name": "Team Alpha",
  "category": "Software Leader",
  "subcategory": "Junior",
  "group_id": 1,
  "coach_id": 1,
  "fee": 500.0,
  "placement_rank": 1,
  "placement_label": "Gold Medal",
  "notes": "string",
  "created_at": "2026-04-01T10:00:00"
}
```

## TeamWithMembersDTO
```json
{
  "team": "TeamDTO",
  "members": ["TeamMemberDTO"]
}
```

## TeamMemberDTO
```json
{
  "id": 1,
  "team_id": 1,
  "student_id": 1,
  "member_share": 250.0,
  "fee_paid": true,
  "payment_id": 123
}
```

## TeamMemberRosterDTO
Enriched with student name and team info.

```json
{
  "team_member_id": 1,
  "team_id": 1,
  "team_name": "Team Alpha",
  "student_id": 1,
  "student_name": "Ahmed Ali",
  "member_share": 250.0,
  "fee_paid": true,
  "payment_id": 123
}
```

| Field | Type | Description |
|-------|------|-------------|
| team_member_id | int | Membership record ID |
| team_id | int | Team ID |
| team_name | string | Team display name |
| student_id | int | Student ID |
| student_name | string | Student full name |
| member_share | number | Per-student fee share |
| fee_paid | bool | Payment status |
| payment_id | int? | Payment ID if paid |

## RegisterTeamInput
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| competition_id | int | Yes | Must match URL if provided |
| team_name | string | Yes | Unique within competition |
| category | string | Yes | Stored as citext |
| subcategory | string | No | Required if category has subcategories |
| student_ids | list[int] | Yes | At least 1 student |
| coach_id | int | No | |
| group_id | int | No | |
| fee | number | No | Defaults to competition fee |
| notes | string | No | |

## UpdateTeamInput
All fields optional.

| Field | Type |
|-------|------|
| team_name | string |
| category | string |
| subcategory | string |
| group_id | int |
| coach_id | int |
| fee | number |
| notes | string |

## AddTeamMemberInput
| Field | Type | Required |
|-------|------|----------|
| student_id | int | Yes |

## PlacementUpdateInput
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| placement_rank | int | Yes | 1 = 1st place |
| placement_label | string | No | e.g., "Gold", "3rd Place" |

## PayCompetitionFeeResponseDTO
```json
{
  "receipt_number": "RCP-2026-001",
  "payment_id": 123,
  "amount": 250.0
}
```

## CompetitionSummaryResponse
```json
{
  "competition": "CompetitionDTO",
  "categories": [{
    "category": "CompetitionCategoryDTO",
    "teams": ["TeamWithMembersDTO"]
  }],
  "total_teams": 5,
  "total_participants": 15
}
```

## CategoryResponse
```json
{
  "category": "Software Leader",
  "subcategories": ["Junior", "Senior"]
}
```

## StudentCompetitionDTO
```json
{
  "membership": "TeamMemberDTO",
  "team": "TeamDTO",
  "category": "CompetitionCategoryDTO",
  "competition": "CompetitionDTO"
}
```

## TeamRegistrationResultDTO
```json
{
  "team": "TeamDTO",
  "members_added": 2
}
```

## AddTeamMemberResultDTO
```json
{
  "team_member_id": 1,
  "student_id": 5,
  "student_name": "Ahmed Ali"
}
```

## TeamMemberListResponse
```json
{
  "team_id": 1,
  "team_name": "Team Alpha",
  "members": ["TeamMemberRosterDTO"]
}
```

## StudentCompetitionsResponse
```json
{
  "student_id": 1,
  "competitions": ["StudentCompetitionDTO"]
}
```

## DeletedTeamListResponse
```json
{
  "competition_id": 1,
  "teams": ["TeamDTO"],
  "total": 5
}
```
