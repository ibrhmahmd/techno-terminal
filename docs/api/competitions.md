# Competitions API Reference

Base path: `/api/v1/competitions`

---

## 🔐 Authentication
All requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### CompetitionDTO
```json
{
  "id": 1,
  "name": "National Robotics Championship",
  "edition": "2026",
  "competition_date": "2026-05-15",
  "location": "Cairo",
  "notes": "Annual national competition",
  "fee_per_student": 500.0,
  "created_at": "2026-04-01T10:00:00"
}
```

### CompetitionCategoryDTO
```json
{
  "id": 1,
  "competition_id": 1,
  "category_name": "Junior League (Age 10-12)",
  "notes": "Entry level category"
}
```

### CreateCompetitionInput
```json
{
  "name": "string (required)",
  "edition": "string (optional)",
  "competition_date": "date (optional) - YYYY-MM-DD",
  "location": "string (optional)",
  "notes": "string (optional)",
  "fee_per_student": "number (default: 0)"
}
```

### AddCategoryInput
```json
{
  "competition_id": "integer (required)",
  "category_name": "string (required)",
  "notes": "string (optional)"
}
```

### TeamDTO
```json
{
  "id": 1,
  "category_id": 1,
  "group_id": 1,
  "team_name": "Techno Eagles",
  "coach_id": 1,
  "created_at": "2026-04-01T10:00:00"
}
```

### TeamMemberDTO
```json
{
  "id": 1,
  "team_id": 1,
  "student_id": 1,
  "member_share": 500.0,
  "fee_paid": false,
  "payment_id": null
}
```

### RegisterTeamInput
```json
{
  "category_id": "integer (required)",
  "team_name": "string (required)",
  "student_ids": ["integer (required, at least 1)"],
  "coach_id": "integer (optional)",
  "group_id": "integer (optional)"
}
```

### TeamRegistrationResultDTO
```json
{
  "team": {
    "id": 1,
    "category_id": 1,
    "group_id": 1,
    "team_name": "Techno Eagles",
    "coach_id": 1,
    "created_at": "2026-04-01T10:00:00"
  },
  "members_added": 4
}
```

### TeamWithMembersDTO
```json
{
  "team": {
    "id": 1,
    "category_id": 1,
    "group_id": 1,
    "team_name": "Techno Eagles",
    "coach_id": 1
  },
  "members": [
    {
      "id": 1,
      "team_id": 1,
      "student_id": 1,
      "member_share": 500.0,
      "fee_paid": false
    }
  ]
}
```

### ApiResponse (Envelope)
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## Endpoints

### 1. List all competitions
**GET** `/api/v1/competitions`

**Response (200):** `ApiResponse<list<CompetitionDTO>>`

---

### 2. Create a new competition
**POST** `/api/v1/competitions`

**Request Body:** `CreateCompetitionInput`

**Response (201):** `ApiResponse<CompetitionDTO>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Competition name cannot be empty
- Creates competition with optional categories

---

### 3. Get single competition details
**GET** `/api/v1/competitions/{competition_id}`

**Path Parameters:**
- `competition_id` - integer (required)

**Response (200):** `ApiResponse<CompetitionDTO>`

**Error Response (422):** `HTTPValidationError`

---

### 4. List categories for a competition
**GET** `/api/v1/competitions/{competition_id}/categories`

**Path Parameters:**
- `competition_id` - integer (required)

**Response (200):** `ApiResponse<list<CompetitionCategoryDTO>>`

**Error Response (422):** `HTTPValidationError`

---

### 5. Add a category to a competition
**POST** `/api/v1/competitions/{competition_id}/categories`

**Path Parameters:**
- `competition_id` - integer (required)

**Request Body:** `AddCategoryInput`

**Response (201):** `ApiResponse<CompetitionCategoryDTO>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Category name cannot be empty
- Creates category under specified competition

---

### 6. Register a team for a competition
**POST** `/api/v1/competitions/register`

**Request Body:** `RegisterTeamInput`

**Response (201):** `ApiResponse<TeamRegistrationResultDTO>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Requires at least one student
- Associates team with category and optionally a group
- Fee is calculated per student based on competition fee_per_student

---

### 7. List teams in a competition category
**GET** `/api/v1/competitions/{competition_id}/categories/{category_id}/teams`

**Path Parameters:**
- `competition_id` - integer (required)
- `category_id` - integer (required)

**Response (200):** `ApiResponse<list<TeamWithMembersDTO>>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Returns teams with their members for a specific category
- Includes team details and member roster

---

### 8. Mark competition fee as paid (bypass Finance Desk)
**POST** `/api/v1/competitions/team-members/{team_member_id}/pay`

**Path Parameters:**
- `team_member_id` - integer (required)

**Response (200):** `ApiResponse<None>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Direct payment marking without creating receipt
- Updates fee_paid status to true
- Use with caution - bypasses normal financial tracking
