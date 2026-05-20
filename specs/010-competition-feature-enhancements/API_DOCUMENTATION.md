# Competitions API Documentation

**Base URL**: `/api/v1`
**Auth**: Bearer JWT (Supabase)
**Response Envelope**: All responses wrapped in `{"success": bool, "data": ..., "message": "..."}`

---

## Authentication & Roles

| Role | Access |
|------|--------|
| `admin` / `system_admin` | Full read + write |
| `coach` | Read-only for teams they coach (`team.coach_id == employee_id`) |
| Any authenticated user | Read competitions, categories, summaries |

---

## Competitions

### 1. List All Competitions

```
GET /competitions
```

**Auth**: Any authenticated user

**Query Params**: None

**Response 200**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Robotics Championship 2024",
      "edition": null,
      "edition_year": 2024,
      "competition_date": "2024-06-15",
      "location": "Main Hall",
      "notes": null,
      "fee_per_student": 50.0,
      "created_at": "2024-01-10T08:00:00"
    }
  ]
}
```

---

### 2. Create Competition

```
POST /competitions
```

**Auth**: Admin only

**Body**:
```json
{
  "name": "Robotics Championship 2024",
  "edition_year": 2024,
  "competition_date": "2024-06-15",
  "location": "Main Hall",
  "fee_per_student": 50.0,
  "notes": "Optional notes",
  "edition": "Optional edition string (deprecated)"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | ✅ | Min 1 char |
| `edition_year` | int | ✅ | 2000–2100 |
| `competition_date` | date | ❌ | ISO 8601 |
| `location` | string | ❌ | Max 200 |
| `fee_per_student` | float | ❌ | ≥ 0, default 0 |
| `notes` | string | ❌ | Max 1000 |
| `edition` | string | ❌ | Max 100 (deprecated) |

**Response 201**:
```json
{
  "success": true,
  "data": { "id": 1, "name": "...", ... },
  "message": "Competition created successfully."
}
```

---

### 3. Get Competition by ID

```
GET /competitions/{id}
```

**Auth**: Any authenticated user

**Response 200**: Same as `CompetitionDTO` above.

**Response 404**: Competition not found.

---

### 4. Update Competition

```
PUT  /competitions/{id}
PATCH /competitions/{id}
```

**Auth**: Admin only

**Body** (all fields optional — partial updates supported):
```json
{
  "name": "Updated Name",
  "location": "New Location"
}
```

**Response 200**: Updated `CompetitionDTO`.

**Response 400**: No fields provided.

**Response 404**: Competition not found.

---

### 5. Delete Competition

```
DELETE /competitions/{id}
```

**Auth**: Admin only

**Response 200**:
```json
{
  "success": true,
  "data": true,
  "message": "Competition deleted successfully."
}
```

**Response 409**: Cannot delete — competition has registered teams.

**Response 404**: Competition not found.

---

### 6. Get Competition Summary (Dashboard)

```
GET /competitions/{id}/summary
```

**Auth**: Any authenticated user

**Response 200**:
```json
{
  "success": true,
  "data": {
    "competition": { "id": 1, "name": "...", ... },
    "categories": [
      {
        "category": "Robotics",
        "subcategory": "Sumo",
        "teams": [
          {
            "team": { "id": 1, "team_name": "Team Alpha", ... },
            "members": [
              { "id": 1, "team_id": 1, "student_id": 10, "amount_due": 50.0, "amount_paid": 50.0 }
            ]
          }
        ]
      }
    ],
    "total_teams": 12,
    "total_participants": 48
  }
}
```

**Response 404**: Competition not found.

---

### 7. List Categories

```
GET /competitions/{id}/categories
```

**Auth**: Any authenticated user

**Response 200**:
```json
{
  "success": true,
  "data": [
    {
      "category": "Robotics",
      "subcategories": ["Sumo", "Line Follower", "Freestyle"]
    },
    {
      "category": "Programming",
      "subcategories": []
    }
  ]
}
```

Categories are derived from distinct `category`/`subcategory` values on teams.

**Response 404**: Competition not found.

---

## Teams

### 8. List Teams

```
GET /teams?competition_id=1&category=Robotics&subcategory=Sumo&include_members=true
```

**Auth**: Any authenticated user (coaches see only their own teams)

**Query Params**:

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `competition_id` | int | ✅ | — | Filter by competition |
| `category` | string | ❌ | — | Filter by category |
| `subcategory` | string | ❌ | — | Filter by subcategory |
| `include_members` | bool | ❌ | `true` | Include team members in response |

**Response 200** (`include_members=true`):
```json
{
  "success": true,
  "data": [
    {
      "team": { "id": 1, "team_name": "Team Alpha", "competition_id": 1, "category": "Robotics", ... },
      "members": [
        { "id": 1, "team_id": 1, "student_id": 10, "amount_due": 50.0, "amount_paid": 50.0 }
      ]
    }
  ]
}
```

**Response 200** (`include_members=false`): Same structure but `members` array omitted.

**Response 400**: `competition_id` is required.

---

### 9. Register Team

```
POST /teams
```

**Auth**: Admin only

**Body**:
```json
{
  "competition_id": 1,
  "team_name": "Team Alpha",
  "category": "Robotics",
  "subcategory": "Sumo",
  "student_ids": [10, 11, 12],
  "student_fees": { "10": 50.0, "11": 30.0 },
  "coach_id": 5,
  "group_id": 3,
  "project_name": "Autonomous Sumo Bot",
  "project_description": "A robot that...",
  "notes": "Optional notes"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `competition_id` | int | ✅ | — | FK to competition |
| `team_name` | string | ✅ | — | Must be unique within competition |
| `category` | string | ✅ | — | Category name |
| `subcategory` | string | ❌ | `null` | Subcategory (required if category has subcategories) |
| `student_ids` | int[] | ✅ | — | At least 1 student required |
| `student_fees` | dict | ❌ | `{}` | Per-student fees: `{student_id: amount}`. Missing students default to 0. |
| `coach_id` | int | ❌ | `null` | FK to employees |
| `group_id` | int | ❌ | `null` | FK to groups (stored but not used for pre-fill) |
| `project_name` | string | ❌ | `null` | Max 500 |
| `project_description` | string | ❌ | `null` | Max 5000 |
| `notes` | string | ❌ | `null` | Max 1000 |

**Response 201** (no warnings):
```json
{
  "success": true,
  "data": {
    "team": { "id": 1, "team_name": "Team Alpha", ... },
    "members_added": 3
  },
  "message": "Team registered successfully."
}
```

**Response 201** (with warnings — duplicate students):
```json
{
  "success": true,
  "data": {
    "team": { "id": 1, "team_name": "Team Alpha", ... },
    "members_added": 3
  },
  "message": "Student 10 already registered in another team for this competition."
}
```

**Business Rules**:
- One student can only be in one team per competition (duplicate → warning, not blocked)
- Team name must be unique within the competition
- All students must be active

**Response 404**: Competition or student not found.

**Response 409**: Duplicate team name.

---

### 10. Get Team by ID

```
GET /teams/{id}
```

**Auth**: Admin or team's coach

**Response 200**: `TeamDTO`

**Response 403**: User is not admin and not the team's coach.

**Response 404**: Team not found.

---

### 11. Update Team

```
PUT  /teams/{id}
PATCH /teams/{id}
```

**Auth**: Admin only

**Body** (all fields optional):
```json
{
  "team_name": "New Name",
  "category": "Programming",
  "subcategory": "Web Dev",
  "project_name": "New Project",
  "project_description": "Updated description",
  "coach_id": 7,
  "group_id": 5,
  "notes": "Updated notes"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `team_name` | string | Min 1, max 200 |
| `category` | string | Max 100 |
| `subcategory` | string | Max 100 |
| `project_name` | string | Max 500 |
| `project_description` | string | Max 5000 |
| `coach_id` | int | FK to employees |
| `group_id` | int | FK to groups |
| `notes` | string | Max 1000 |

**Response 200**: Updated `TeamDTO`.

**Response 400**: No fields provided.

**Response 404**: Team not found.

---

### 12. Delete Team

```
DELETE /teams/{id}
```

**Auth**: Admin only

**Response 200**:
```json
{
  "success": true,
  "data": true,
  "message": "Team deleted successfully."
}
```

**Response 409**: Cannot delete — team has members who have paid fees.

**Response 404**: Team not found.

---

## Team Members

### 13. List Team Members

```
GET /teams/{id}/members
```

**Auth**: Admin or team's coach

**Response 200**:
```json
{
  "success": true,
  "data": {
    "team_id": 1,
    "team_name": "Team Alpha",
    "members": [
      {
        "team_member_id": 1,
        "team_id": 1,
        "team_name": "Team Alpha",
        "student_id": 10,
        "student_name": "Ahmed Ali",
        "amount_due": 50.0,
        "amount_paid": 50.0
      }
    ]
  }
}
```

**Response 403**: User is not admin and not the team's coach.

**Response 404**: Team not found.

---

### 14. Add Team Member

```
POST /teams/{id}/members
```

**Auth**: Admin only

**Body**:
```json
{
  "student_id": 15,
  "amount_due": 50.0
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `student_id` | int | ✅ | — | Student to add |
| `amount_due` | float | ❌ | `0.0` | Fee amount for this member |

**Response 201**:
```json
{
  "success": true,
  "data": {
    "team_member_id": 5,
    "student_id": 15,
    "student_name": "Sara Mohamed"
  },
  "message": "Member added successfully."
}
```

**Response 201** (with warning — duplicate student):
```json
{
  "success": true,
  "data": { "team_member_id": 5, "student_id": 15, "student_name": "Sara Mohamed" },
  "message": "Student 15 already registered in another team for this competition."
}
```

**Business Rules**:
- Student cannot already be in another team for this competition (warning, not blocked)
- Student must be active

**Response 404**: Team or student not found.

**Response 409**: Student already in this team.

---

### 15. Remove Team Member

```
DELETE /teams/{id}/members/{student_id}
```

**Auth**: Admin only

**Response 200**:
```json
{
  "success": true,
  "data": true,
  "message": "Member removed successfully."
}
```

**Response 400**: Cannot remove member who has already paid (`amount_paid > 0`).

**Response 404**: Team or member not found.

---

### 16. Pay Competition Fee

```
POST /teams/{id}/members/{student_id}/pay
```

**Auth**: Admin only

**Body**:
```json
{
  "amount": 25.0,
  "parent_id": 20
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `amount` | float | ✅ | — | Payment amount (must be > 0, supports partial) |
| `parent_id` | int | ❌ | `null` | Parent ID for receipt |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "receipt_number": "REC-2024-0001",
    "payment_id": 100,
    "amount": 25.0,
    "amount_paid": 25.0,
    "amount_due": 50.0
  },
  "message": "Payment processed successfully."
}
```

**Business Rules**:
- Payment amount must be > 0
- Supports partial payments (call multiple times until `amount_paid >= amount_due`)
- Atomic: receipt creation + fee recording in single transaction
- On failure, entire operation rolls back (no orphan receipts)

**Response 400**: Invalid amount or business rule violation.

**Response 404**: Team or member not found.

---

### 17. Refund Competition Fee

```
POST /teams/{id}/members/{student_id}/refund
```

**Auth**: Admin only

**Body**:
```json
{
  "amount": 10.0
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | float | ✅ | Refund amount (must be > 0 and ≤ current `amount_paid`) |

**Response 200**:
```json
{
  "success": true,
  "data": true,
  "message": "Refund of 10.0 processed successfully with receipt REC-2024-0002."
}
```

**Business Rules**:
- Refund amount must be > 0 and ≤ current `amount_paid`
- Atomic: refund receipt + fee adjustment in single transaction
- On failure, entire operation rolls back

**Response 400**: Refund amount exceeds amount paid.

**Response 404**: Team or member not found.

---

### 18. Update Team Placement

```
PATCH /teams/{id}/placement
```

**Auth**: Admin only

**Body**:
```json
{
  "placement_rank": 1,
  "placement_label": "Gold"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `placement_rank` | int | ✅ | Placement rank (1 = 1st place, ≥ 1) |
| `placement_label` | string | ❌ | Label like "Gold", "3rd Place" (max 100) |

**Response 200**: Updated `TeamDTO`.

**Business Rules**:
- Cannot set placement before competition date
- Cannot set placement if competition date is > 30 days in the past

**Response 400**: Placement window closed or competition date has not passed.

**Response 404**: Team not found.

---

## Student Competitions

### 19. Get Student's Competitions

```
GET /students/{student_id}/competitions
```

**Auth**: Any authenticated user

**Response 200**:
```json
{
  "success": true,
  "data": {
    "student_id": 10,
    "competitions": [
      {
        "membership": {
          "id": 1,
          "team_id": 1,
          "student_id": 10,
          "amount_due": 50.0,
          "amount_paid": 50.0
        },
        "team": {
          "id": 1,
          "team_name": "Team Alpha",
          "competition_id": 1,
          "category": "Robotics",
          "subcategory": "Sumo",
          "placement_rank": 1,
          "placement_label": "Gold",
          ...
        },
        "category": "Robotics",
        "subcategory": "Sumo",
        "competition": {
          "id": 1,
          "name": "Robotics Championship 2024",
          "edition_year": 2024,
          "competition_date": "2024-06-15",
          ...
        }
      }
    ]
  }
}
```

**Response 404**: Student not found.

---

## Data Models

### CompetitionDTO
```typescript
interface CompetitionDTO {
  id: number;
  name: string;
  edition: string | null;        // deprecated
  edition_year: number;
  competition_date: string | null;  // ISO date
  location: string | null;
  notes: string | null;
  fee_per_student: number;
  created_at: string | null;     // ISO datetime
}
```

### TeamDTO
```typescript
interface TeamDTO {
  id: number;
  competition_id: number;
  category: string;
  subcategory: string | null;
  group_id: number | null;
  team_name: string;
  coach_id: number | null;
  project_name: string | null;
  project_description: string | null;
  placement_rank: number | null;
  placement_label: string | null;
  notes: string | null;
  created_at: string | null;
}
```

### TeamMemberDTO
```typescript
interface TeamMemberDTO {
  id: number;
  team_id: number;
  student_id: number;
  amount_due: number;
  amount_paid: number;
}
```

### TeamMemberRosterDTO
```typescript
interface TeamMemberRosterDTO {
  team_member_id: number;
  team_id: number;
  team_name: string;
  student_id: number;
  student_name: string;
  amount_due: number;
  amount_paid: number;
}
```

### TeamWithMembersDTO
```typescript
interface TeamWithMembersDTO {
  team: TeamDTO;
  members: TeamMemberDTO[];
}
```

### CategoryWithTeamsDTO
```typescript
interface CategoryWithTeamsDTO {
  category: string;
  subcategory: string | null;
  teams: TeamWithMembersDTO[];
}
```

### TeamRegistrationResultDTO
```typescript
interface TeamRegistrationResultDTO {
  team: TeamDTO;
  members_added: number;
}
```

### AddTeamMemberResultDTO
```typescript
interface AddTeamMemberResultDTO {
  team_member_id: number;
  student_id: number;
  student_name: string;
}
```

### PayCompetitionFeeResponseDTO
```typescript
interface PayCompetitionFeeResponseDTO {
  receipt_number: string;
  payment_id: number;
  amount: number;
  amount_paid: number;   // Running total after this payment
  amount_due: number;    // For context
}
```

### CompetitionSummaryResponse
```typescript
interface CompetitionSummaryResponse {
  competition: CompetitionDTO;
  categories: CategoryWithTeamsDTO[];
  total_teams: number;
  total_participants: number;
}
```

### StudentCompetitionDTO
```typescript
interface StudentCompetitionDTO {
  membership: TeamMemberDTO;
  team: TeamDTO;
  category: string;
  subcategory: string | null;
  competition: CompetitionDTO | null;
}
```

### StudentCompetitionsResponse
```typescript
interface StudentCompetitionsResponse {
  student_id: number;
  competitions: StudentCompetitionDTO[];
}
```

---

## Error Responses

All errors follow the standard envelope:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable description"
}
```

| HTTP Status | Error Type | When |
|-------------|-----------|------|
| 400 | `BadRequest` | Invalid input, business rule violation |
| 401 | `Unauthorized` | Missing or invalid JWT |
| 403 | `Forbidden` | Insufficient role |
| 404 | `NotFound` | Resource not found |
| 409 | `Conflict` / `BusinessRuleError` | Duplicate, state conflict |
| 422 | `ValidationError` | Pydantic validation failure |
| 500 | `InternalServerError` | Server error |

---

## Key Business Rules Summary

| Rule | Detail |
|------|--------|
| **One student per team per competition** | Duplicate → warning in `message` field, not blocked |
| **Team name uniqueness** | Must be unique within a competition |
| **Payment atomicity** | Receipt + fee recording in single transaction — no orphan data |
| **Partial payments** | Call `/pay` multiple times until `amount_paid >= amount_due` |
| **Refund limit** | `amount` ≤ current `amount_paid` |
| **Placement window** | Only after competition date AND within 30 days after |
| **Delete guards** | Competition: blocked if teams exist. Team: blocked if any member has `amount_paid > 0` |
| **Coach access** | Coaches can only view teams where `team.coach_id == employee_id` |
| **Hard delete** | No soft delete — competitions and teams are permanently removed |
