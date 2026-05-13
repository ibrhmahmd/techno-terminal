# Academics API - Group Competitions Router

Router source: `app/api/routers/academics/group_competitions.py`

Mounted prefix: `/api/v1`

---

## Authentication & Authorization

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Role guards used in this router:
- `require_any`: any authenticated active user
- `require_admin`: admin/system_admin only

Common auth errors:
- `401 Unauthorized`
- `403 Forbidden`

---

## DTOs and Schemas

### Response DTOs

#### TeamPublic
```json
{
  "id": 1,
  "team_name": "RoboWarriors",
  "group_id": 5,
  "coach_id": 7,
  "created_at": "2026-01-15T10:30:00",
  "is_deleted": false
}
```

Fields:
- `id`: team ID
- `team_name`: display name
- `group_id`: linked group
- `coach_id`: assigned coach/mentor
- `created_at`: creation timestamp
- `is_deleted`: soft delete flag

#### PaginatedResponse[TeamPublic]
```json
{
  "data": [
    {
      "id": 1,
      "team_name": "RoboWarriors",
      "group_id": 5,
      "coach_id": 7,
      "created_at": "2026-01-15T10:30:00",
      "is_deleted": false
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 50
}
```

#### GroupCompetitionParticipationDTO
```json
{
  "participation_id": 1,
  "competition_id": 5,
  "competition_name": "National Robotics Championship",
  "category_id": 3,
  "category_name": "Senior Division",
  "team_id": 2,
  "team_name": "RoboWarriors",
  "entered_at": "2026-03-01T09:00:00",
  "left_at": null,
  "is_active": true,
  "final_placement": null,
  "notes": "First time competing"
}
```

Fields:
- `participation_id`: unique participation record ID
- `competition_id`, `competition_name`: competition details
- `category_id`, `category_name`: competition category
- `team_id`, `team_name`: participating team
- `entered_at`: registration timestamp
- `left_at`: exit/withdrawal timestamp (null if active)
- `is_active`: participation status
- `final_placement`: final ranking (null if not completed)
- `notes`: additional information

#### GroupCompetitionHistoryResponseDTO
```json
{
  "group_id": 5,
  "group_name": "Saturday Robotics Batch",
  "participations": [
    {
      "participation_id": 1,
      "competition_id": 5,
      "competition_name": "National Robotics Championship",
      "team_name": "RoboWarriors",
      "status": "active",
      "entered_at": "2026-03-01T09:00:00",
      "final_placement": null
    }
  ],
  "total_participations": 5,
  "active_participations": 2,
  "completed_participations": 3
}
```

---

## Endpoints

### 1) List competition participations for a group
**GET** `/api/v1/academics/groups/{group_id}/competitions`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `is_active` (optional): Filter by active status (true/false/null for all)

Response:
- `200 OK` -> `ApiResponse<list<GroupCompetitionParticipationDTO>>`

Errors:
- `401`, `403`, `404`

---

### 2) List teams linked to a group
**GET** `/api/v1/academics/groups/{group_id}/teams`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Query:
- `include_inactive` (optional, default `false`): Include soft-deleted teams
- `skip` (optional, default `0`): Pagination offset
- `limit` (optional, default `50`, max `200`): Page size

Response:
- `200 OK` -> `PaginatedResponse<TeamPublic>`

Errors:
- `401`, `403`, `404`

Notes:
- Returns paginated list of teams.
- Supports filtering by active status.

---

### 3) Link an existing team to a group
**POST** `/api/v1/academics/groups/{group_id}/teams/{team_id}/link`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `team_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<TeamLinkResponse>` with linked team info:
```json
{
  "team_id": 1,
  "team_name": "RoboWarriors",
  "group_id": 5
}
```

Errors:
- `401`, `403`, `404` (team not found)

Notes:
- Associates an existing team with a group.
- Team can only be linked to one group at a time.

---

### 4) Register a team for a competition
**POST** `/api/v1/academics/groups/{group_id}/competitions/{competition_id}/register`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `competition_id` (integer, required)

Query params:
- `team_id` (integer, required): Team to register
- `category_id` (integer, optional): Competition category

Response:
- `200 OK` -> `ApiResponse<CompetitionRegistrationResponse>` with participation record:
```json
{
  "participation_id": 1,
  "group_id": 5,
  "team_id": 2,
  "competition_id": 3,
  "category_id": null,
  "entered_at": "2026-03-01T09:00:00",
  "is_active": true,
  "message": "Team registered for competition successfully"
}
```

Errors:
- `401`, `403`, `404`, `409` (team already has active participation in this competition)

Notes:
- Registers a group team for a competition.
- Creates an active participation record.
- Validates that team belongs to the group.

---

### 5) Mark competition participation as completed
**PATCH** `/api/v1/academics/groups/{group_id}/competitions/{participation_id}/complete`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `participation_id` (integer, required)

Query:
- `final_placement` (integer, optional): Final ranking/placement

Response:
- `200 OK` -> `ApiResponse<CompetitionCompletionResponse>` with updated participation:
```json
{
  "participation_id": 1,
  "is_active": false,
  "left_at": "2026-05-15T18:00:00",
  "final_placement": 3,
  "message": "Competition participation marked as completed"
}
```

Errors:
- `401`, `403`, `404` (participation not found)

Notes:
- Marks participation as completed.
- Records final placement if provided.
- Sets `is_active` to false and `left_at` timestamp.

---

### 6) Withdraw from competition
**DELETE** `/api/v1/academics/groups/{group_id}/competitions/{participation_id}`  
Auth: `require_admin`

Path params:
- `group_id` (integer, required)
- `participation_id` (integer, required)

Query:
- `reason` (optional): Reason for withdrawal

Response:
- `200 OK` -> `ApiResponse<CompetitionWithdrawalResponse>` with participation_id, status, withdrawn_at:
```json
{
  "participation_id": 1,
  "status": "withdrawn",
  "withdrawn_at": "2026-04-01T10:30:00",
  "message": "Successfully withdrew from competition."
}
```

Errors:
- `401`, `403`, `404` (participation not found)
- `409` (already withdrawn or completed)

Notes:
- Withdraws a group from a competition.
- Sets participation status to `withdrawn`.
- Records withdrawal timestamp.

---

### 7) Get competition participation analytics
**GET** `/api/v1/academics/groups/{group_id}/competitions/analytics`  
Auth: `require_any`

Path params:
- `group_id` (integer, required)

Response:
- `200 OK` -> `ApiResponse<GroupCompetitionHistoryResponseDTO>`

Notes:
- Returns full competition participation history.
- Includes all competition participations for the group.
- Shows team and category details.
- Includes entry/exit dates and placement results.
- Provides summary statistics (total, active, completed counts).

---

## Router Notes

- The Group Competitions router exposes **7 endpoints** for competition integration.
- All list endpoints support pagination with `skip` and `limit` parameters.
- Teams use soft delete (`is_deleted` flag) to preserve historical data integrity.
- Competition participation creates an audit trail with entry/exit timestamps.
