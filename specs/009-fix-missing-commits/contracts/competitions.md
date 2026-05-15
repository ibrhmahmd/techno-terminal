# Competition API Contracts

**Note**: Contracts are unchanged — only backend persistence behavior is fixed.

## POST /api/v1/competitions

**Request**: `CreateCompetitionInput` (name, edition, competition_date, location, notes, fee_per_student)  
**Response**: `ApiResponse[CompetitionPublic]` — 201 on success  
**Auth**: `require_admin`

## POST /api/v1/competitions/{id}/teams

**Request**: `RegisterTeamInput` (competition_id, team_name, category, subcategory, student_ids, coach_id, group_id, notes, student_fees)  
**Response**: `ApiResponse[TeamRegistrationResult]` — 201 on success  
**Auth**: `require_admin`

## PATCH /api/v1/competitions/teams/{id}

**Request**: fields to update  
**Response**: `ApiResponse[TeamPublic]` — 200 on success  
**Auth**: `require_admin`

## DELETE /api/v1/competitions/teams/{id}

**Response**: `ApiResponse[bool]` — 200 on success  
**Auth**: `require_admin`

## POST /api/v1/competitions/teams/{id}/placement

**Request**: `{ placement_rank, placement_label? }`  
**Response**: `ApiResponse[TeamPublic]` — 200 on success  
**Auth**: `require_admin`
